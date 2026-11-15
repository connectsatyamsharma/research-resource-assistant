"""Retrieval, ranking, confidence and explanation.

Three methods are implemented so they can be compared in evaluate.py:
  keyword  - baseline: exact token overlap (TF-IDF weighted) on name + description only
  semantic - LSA (TF-IDF -> truncated SVD) + char n-gram similarity on graph-enriched text, no graph/availability
  hybrid   - semantic + knowledge-graph theme match + availability + department context  (selected approach)
"""
import difflib
import re
import numpy as np
import networkx as nx
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .kg import RANKED_TYPES, is_incomplete, load_kg

STOP = set("a an the of for in on to and or with from by at is are be can i we my me need find using use "
           "where how what which that this any some data".split())  # 'data' is too generic to be evidence
AVAIL_SCORE = {"available": 1.0, "limited": 0.5, "unavailable": 0.0, None: 0.3}
WEIGHTS = {"semantic": 0.45, "graph": 0.35, "availability": 0.15, "context": 0.05}
CONF_HIGH, CONF_MED = 0.60, 0.35


def tokens(text):
    return [t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in STOP and len(t) > 1]


class Engine:
    def __init__(self, G=None, svd_dim=24):
        self.G = G or load_kg()
        self.items = [n for n, a in self.G.nodes(data=True) if a["type"] in RANKED_TYPES]
        self.themes = [n for n, a in self.G.nodes(data=True) if a["type"] == "Theme"]
        self.raw = [self._raw_text(n) for n in self.items]
        self.enriched = [self._enriched_text(n) for n in self.items]
        theme_docs = [self.G.nodes[t]["name"] + " " + self.G.nodes[t]["aliases"] for t in self.themes]

        # keyword baseline index: raw text, plain word tf-idf, no semantics
        self.kw_vec = TfidfVectorizer(tokenizer=tokens, token_pattern=None, lowercase=False)
        self.kw_mat = self.kw_vec.fit_transform(self.raw)

        # semantic index: word LSA + char n-gram on enriched text
        corpus = self.enriched + theme_docs
        self.w_vec = TfidfVectorizer(tokenizer=tokens, token_pattern=None, lowercase=False, ngram_range=(1, 2),
                                     sublinear_tf=True)
        W = self.w_vec.fit_transform(corpus)
        k = min(svd_dim, W.shape[0] - 1, W.shape[1] - 1)
        self.svd = TruncatedSVD(n_components=k, random_state=42).fit(W)
        Z = self.svd.transform(W)
        self.item_lsa, self.theme_lsa = Z[: len(self.items)], Z[len(self.items):]
        self.vocab = {t for d in corpus for t in tokens(d)}
        self.c_vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True)
        C = self.c_vec.fit_transform(corpus)
        self.item_chr, self.theme_chr = C[: len(self.items)], C[len(self.items):]

    # ---------- text views ----------
    def _raw_text(self, n):
        a = self.G.nodes[n]
        return f"{a['name']} {a.get('description', '')}"

    def _enriched_text(self, n):
        a = self.G.nodes[n]
        th = " ".join(self.G.nodes[t]["name"] + " " + self.G.nodes[t]["aliases"] for t in a.get("themes", []))
        return f"{self._raw_text(n)} {th}"

    # ---------- scoring components ----------
    def _semantic(self, q):
        zq = self.svd.transform(self.w_vec.transform([q]))
        s_lsa = np.clip(cosine_similarity(zq, self.item_lsa)[0], 0, 1)
        s_chr = cosine_similarity(self.c_vec.transform([q]), self.item_chr)[0]
        t_lsa = np.clip(cosine_similarity(zq, self.theme_lsa)[0], 0, 1)
        t_chr = cosine_similarity(self.c_vec.transform([q]), self.theme_chr)[0]
        return 0.7 * s_lsa + 0.3 * s_chr, 0.7 * t_lsa + 0.3 * t_chr

    def match_themes(self, q, min_sim=0.12):
        """Map a query onto theme nodes of the knowledge graph. Returns {theme_id: similarity}."""
        _, ts = self._semantic(q)
        mx = ts.max() if len(ts) else 0
        return {self.themes[i]: float(ts[i]) for i in range(len(ts)) if ts[i] >= min_sim and ts[i] >= 0.5 * mx}

    def coverage(self, query):
        """Share of query terms the index recognises (exactly or as a close spelling). Guards against
        confident answers built on one generic word such as 'detection' (calibration safeguard)."""
        toks = tokens(query)
        if not toks:
            return 0.0
        ok = sum(1 for t in toks if t in self.vocab or difflib.get_close_matches(t, self.vocab, n=1, cutoff=0.82))
        return ok / len(toks)

    # ---------- public API ----------
    def search(self, query, method="hybrid", k=5, context_dept=None):
        """Returns (results, status). status: ok | empty_query | too_vague | no_match."""
        toks = tokens(query or "")
        if not (query or "").strip():
            return [], "empty_query"
        if len(toks) < 2 and method != "keyword":
            return [], "too_vague"

        if method == "keyword":
            qv = self.kw_vec.transform([query])
            scores = cosine_similarity(qv, self.kw_mat)[0]
            comps = [{"keyword": float(s)} for s in scores]
            final, themes = scores, {}
        else:
            sem, _ = self._semantic(query)
            themes = self.match_themes(query)
            if method == "semantic":
                final = sem
                comps = [{"semantic": float(s)} for s in sem]
            else:
                final = np.zeros(len(self.items))
                comps = []
                for i, n in enumerate(self.items):
                    a = self.G.nodes[n]
                    g = max([min(1.0, themes[t] / 0.5) for t in a.get("themes", []) if t in themes], default=0.0)
                    av = AVAIL_SCORE.get(a.get("availability"), 0.3)
                    cx = 1.0 if (context_dept and a.get("dept") == context_dept) else 0.0
                    c = {"semantic": float(sem[i]), "graph": g, "availability": av, "context": cx}
                    # availability only counts when the item is topically relevant (else it would reward irrelevant items)
                    rel_gate = min(1.0, (sem[i] + g) / 0.4)
                    final[i] = (WEIGHTS["semantic"] * sem[i] + WEIGHTS["graph"] * g +
                                rel_gate * (WEIGHTS["availability"] * av + WEIGHTS["context"] * cx))
                    comps.append(c)

        order = np.argsort(-final)[:k]
        results = []
        for i in order:
            if final[i] <= 0:
                continue
            results.append(self._package(self.items[i], float(final[i]), comps[i], method, themes, query, context_dept,
                                         self.coverage(query)))
        if not results or (method != "keyword" and results[0]["confidence"] < 0.15):
            return results, "no_match"
        return results, "ok"

    # ---------- confidence, review state, explanation ----------
    def _package(self, node, score, comps, method, themes, query, context_dept, cov=1.0):
        a = self.G.nodes[node]
        conf = float(min(1.0, score / 0.85)) if method == "hybrid" else float(min(1.0, score / 0.6))
        if method != "keyword":
            conf *= min(1.0, cov / 0.6)  # low query coverage -> lower confidence
        band = "High" if conf >= CONF_HIGH else "Medium" if conf >= CONF_MED else "Low"
        missing = is_incomplete(a)
        avail = a.get("availability")
        if avail == "unavailable":
            state, reason = "Blocked - unavailable", "Resource exists and is relevant but is currently restricted/unavailable."
        elif missing:
            state, reason = "Needs human review", "Incomplete record: missing " + ", ".join(missing) + "."
        elif band == "Low":
            state, reason = "Needs human review", "Low confidence match."
        elif band == "Medium" or avail == "limited":
            state, reason = "Review recommended", "Medium confidence or limited availability."
        else:
            state, reason = "Auto-recommended", "High confidence, complete record, available."
        best_theme = max(((t, s) for t, s in themes.items() if t in a.get("themes", [])), key=lambda x: x[1],
                         default=(None, 0))[0] or (max(themes, key=themes.get) if themes else None)
        res = {"id": node, "type": a["type"], "name": a["name"], "dept": a.get("dept"),
               "availability": avail, "score": round(score, 4), "confidence": round(conf, 3), "band": band,
               "components": {k: round(v, 3) for k, v in comps.items()}, "coverage": round(cov, 2),
               "state": state, "state_reason": reason, "missing_fields": missing,
               "cross_department": bool(context_dept and a.get("dept") != context_dept),
               "path": self.path(best_theme, node) if best_theme else [],
               "publications": self.supporting_publications(node, set(themes)),
               "evidence_terms": self.evidence_terms(query, node),
               "description": a.get("description", "")}
        res["explanation"] = self.explain(res, themes)
        return res

    def path(self, theme, node):
        try:
            p = nx.shortest_path(self.G, theme, node)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []
        out = []
        for i, n in enumerate(p):
            step = {"id": n, "name": self.G.nodes[n]["name"], "type": self.G.nodes[n]["type"]}
            if i > 0:
                step["via"] = self.G.edges[p[i - 1], n]["rel"]
            out.append(step)
        return out

    def supporting_publications(self, node, query_themes, limit=3):
        t = self.G.nodes[node]["type"]
        pubs = set()
        for nb in self.G.neighbors(node):
            if self.G.nodes[nb]["type"] == "Publication":
                pubs.add(nb)
        if t in ("Lab", "Facility"):
            labs = [node] if t == "Lab" else [n for n in self.G.neighbors(node) if self.G.nodes[n]["type"] == "Lab"]
            for lab in labs:
                pubs |= {n for n in self.G.neighbors(lab) if self.G.nodes[n]["type"] == "Publication"}
        if t == "Dataset":
            owner = self.G.nodes[node].get("owner_lab")
            if owner:
                pubs |= {n for n in self.G.neighbors(owner) if self.G.nodes[n]["type"] == "Publication"
                         and set(self.G.nodes[n]["themes"]) & set(self.G.nodes[node]["themes"])}
        node_themes = set(self.G.nodes[node].get("themes", []))
        ranked = sorted(pubs, key=lambda p: (-len((set(self.G.nodes[p]["themes"]) & query_themes) or
                                                  (set(self.G.nodes[p]["themes"]) & node_themes)),
                                             -self.G.nodes[p]["year"]))
        return [{"id": p, "title": self.G.nodes[p]["name"], "year": self.G.nodes[p]["year"]} for p in ranked[:limit]]

    def evidence_terms(self, query, node):
        qt = set(tokens(query))
        text = set(tokens(self._enriched_text(node)))
        return sorted(qt & text)

    def explain(self, r, themes):
        parts = []
        if themes:
            names = ", ".join(self.G.nodes[t]["name"] for t in sorted(themes, key=themes.get, reverse=True)[:2])
            parts.append(f"Your query matches the research theme(s): {names}.")
        if r["path"] and len(r["path"]) > 1:
            parts.append("Link in the knowledge network: " + " -> ".join(s["name"] for s in r["path"]) + ".")
        if r["evidence_terms"]:
            parts.append("Matching terms: " + ", ".join(r["evidence_terms"]) + ".")
        c = r["components"]
        if "graph" in c:
            parts.append(f"Score = semantic {c['semantic']:.2f}, theme/graph {c['graph']:.2f}, "
                         f"availability {c['availability']:.2f}.")
        if method_has_cov(r):
            parts.append(f"Only {r['coverage']:.0%} of your query terms were recognised, so confidence was reduced.")
        if r["publications"]:
            parts.append(f"Supported by {len(r['publications'])} related publication(s).")
        if r["cross_department"]:
            parts.append(f"Cross-departmental suggestion ({r['dept']}).")
        return " ".join(parts)


def method_has_cov(r):
    return r.get("coverage", 1.0) < 0.6


STATUS_MESSAGES = {
    "empty_query": "Please enter a research need.",
    "too_vague": "The query is too vague to match reliably. Add a topic, method or data type (for example 'crop disease images').",
    "no_match": "No confident match found. The results below (if any) are low-confidence and need human review.",
}
