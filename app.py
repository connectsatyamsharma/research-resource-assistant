"""Streamlit research-planning interface. Run: streamlit run app.py"""
import datetime as dt

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
import streamlit as st

from src.retrieval import Engine, STATUS_MESSAGES

st.set_page_config(page_title="Research Resource Discovery Assistant", layout="wide")


@st.cache_resource
def get_engine():
    return Engine()


eng = get_engine()
EXAMPLES = ["labs working on tumor detection in MRI scans", "datasets for training chatbots in Hindi",
            "AI for crop yield using satellite and weather data", "secure IoT sensor networks in smart cities",
            "quantum photonics", "tomato blight detection", "blockchain voting system"]
STATE_ICON = {"Auto-recommended": "🟢", "Review recommended": "🟡", "Needs human review": "🟠",
              "Blocked - unavailable": "🔴"}

if "review_log" not in st.session_state:
    st.session_state.review_log = []
if "query" not in st.session_state:
    st.session_state.query = ""

st.title("University Research Resource Discovery and Evidence Mapping Assistant")
st.caption("Semantic network + information retrieval + explainable recommendation. "
           "Data in this demo is synthetic (see docs/ASSUMPTIONS_AND_ACCEPTANCE.md).")

with st.sidebar:
    st.header("Research context")
    depts = sorted({a.get("dept") for _, a in eng.G.nodes(data=True) if a.get("dept")})
    dept = st.selectbox("Your department (optional)", ["(none)"] + depts)
    k = st.slider("Number of recommendations", 3, 10, 5)
    st.markdown("**Try an example**")
    for ex in EXAMPLES:
        if st.button(ex, key="ex_" + ex):
            st.session_state.query = ex
    st.markdown("---")
    st.markdown("**State legend**\n\n🟢 Auto-recommended  \n🟡 Review recommended  \n🟠 Needs human review  \n🔴 Blocked - unavailable")

query = st.text_input("Describe your research need", key="query", placeholder="e.g. datasets for crop disease detection")
ctx = None if dept == "(none)" else dept
tab_rec, tab_cmp, tab_graph, tab_review = st.tabs(["Recommendations", "Compare with keyword search",
                                                    "Knowledge graph view", "Human review log"])

results, status = eng.search(query, "hybrid", k=k, context_dept=ctx) if query.strip() else ([], "empty_query")

with tab_rec:
    if status != "ok":
        st.warning(STATUS_MESSAGES[status])
    for r in results:
        icon = STATE_ICON[r["state"]]
        with st.expander(f"{icon} {r['name']}  ·  {r['type']}  ·  {r['dept']}  ·  confidence {r['confidence']:.0%} ({r['band']})",
                         expanded=(r is results[0])):
            c1, c2 = st.columns([2, 1])
            with c1:
                st.write(r["description"] or "_No description on record._")
                st.markdown(f"**Why recommended:** {r['explanation']}")
                if r["path"]:
                    st.markdown("**Relationship path:** " + " → ".join(
                        f"{s['name']} *({s.get('via', 'query theme')})*" for s in r["path"]))
                if r["publications"]:
                    st.markdown("**Supporting publications:**")
                    for p in r["publications"]:
                        st.markdown(f"- {p['title']} ({p['year']})")
                else:
                    st.markdown("**Supporting publications:** none on record")
            with c2:
                st.progress(r["confidence"])
                st.markdown(f"**State:** {icon} {r['state']}")
                st.caption(r["state_reason"])
                st.markdown(f"**Availability:** {r['availability'] or 'unknown'}")
                if r["cross_department"]:
                    st.info("Cross-departmental suggestion")
                st.caption("Score breakdown: " + ", ".join(f"{k_}={v:.2f}" for k_, v in r["components"].items()))
            if r["state"] != "Auto-recommended":
                note = st.text_input("Reviewer note", key=f"note_{r['id']}")
                b1, b2, b3 = st.columns(3)
                for col, label in ((b1, "Approve"), (b2, "Reject"), (b3, "Escalate")):
                    if col.button(label, key=f"{label}_{r['id']}"):
                        st.session_state.review_log.append({
                            "time": dt.datetime.now().strftime("%H:%M:%S"), "query": query, "resource": r["name"],
                            "state_before": r["state"], "decision": label, "note": note})
                        st.success(f"Logged: {label}")

with tab_cmp:
    if query.strip():
        kw, kst = eng.search(query, "keyword", k=k)
        c1, c2 = st.columns(2)
        c1.subheader("Keyword baseline")
        if kw:
            c1.dataframe(pd.DataFrame([{"resource": r["name"], "type": r["type"], "score": r["score"]} for r in kw]),
                         hide_index=True)
        else:
            c1.info("Keyword search found nothing.")
        c2.subheader("Hybrid (selected approach)")
        if results:
            c2.dataframe(pd.DataFrame([{"resource": r["name"], "type": r["type"], "confidence": r["confidence"]}
                                       for r in results]), hide_index=True)
        else:
            c2.info(STATUS_MESSAGES.get(status, "No results."))
    else:
        st.info("Enter a query to compare.")
    try:
        st.markdown("**Offline evaluation (see results/summary_metrics.csv)**")
        st.dataframe(pd.read_csv("results/summary_metrics.csv"), hide_index=True)
    except FileNotFoundError:
        st.caption("Run `python -m src.evaluate` to generate metrics.")

with tab_graph:
    if results:
        sub = nx.Graph()
        for r in results[:3]:
            for a, b in zip(r["path"], r["path"][1:]):
                sub.add_edge(a["name"], b["name"], rel=b.get("via", ""))
            for p in r["publications"][:2]:
                sub.add_edge(r["name"], p["title"][:28] + "…", rel="supported_by")
        if sub.number_of_nodes():
            fig, ax = plt.subplots(figsize=(9, 5))
            pos = nx.spring_layout(sub, seed=3, k=0.9)
            nx.draw_networkx(sub, pos, ax=ax, node_color="#cfe3ff", node_size=1800, font_size=7, edge_color="#999")
            nx.draw_networkx_edge_labels(sub, pos, ax=ax, edge_labels=nx.get_edge_attributes(sub, "rel"), font_size=6)
            ax.axis("off")
            st.pyplot(fig)
    else:
        st.info("Run a query to see relationship paths.")

with tab_review:
    if st.session_state.review_log:
        st.dataframe(pd.DataFrame(st.session_state.review_log), hide_index=True)
    else:
        st.info("No review decisions yet. Items that are not 'Auto-recommended' can be approved, rejected or escalated.")
