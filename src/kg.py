"""Knowledge network: loads the JSON dataset into a typed networkx graph."""
import json
from pathlib import Path
import networkx as nx

DATA = Path(__file__).resolve().parents[1] / "data" / "university_kg.json"
RANKED_TYPES = ("Lab", "Dataset", "Facility")  # resource types the engine recommends


def load_kg(path=DATA):
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    G = nx.Graph()
    for t in d["themes"]:
        G.add_node(t["id"], **t)
    for key in ("labs", "datasets", "facilities", "publications"):
        for e in d[key]:
            G.add_node(e["id"], **e)

    def edge(a, b, rel):
        if a in G and b in G:
            G.add_edge(a, b, rel=rel)

    for e in d["labs"]:
        for t in e["themes"]:
            edge(e["id"], t, "studies")
    for e in d["datasets"]:
        for t in e["themes"]:
            edge(e["id"], t, "covers")
        edge(e["owner_lab"], e["id"], "owns")
    for e in d["facilities"]:
        for t in e["themes"]:
            edge(e["id"], t, "supports")
        for lab in e["labs"]:
            edge(e["id"], lab, "used_by")
    for e in d["publications"]:
        for t in e["themes"]:
            edge(e["id"], t, "about")
        edge(e["id"], e["lab"], "authored_by")
        for ds in e["datasets"]:
            edge(e["id"], ds, "uses")
    return G


def is_incomplete(attrs):
    """Record-quality check used by the human-review workflow."""
    missing = []
    if attrs.get("availability") is None:
        missing.append("availability")
    if not attrs.get("description"):
        missing.append("description")
    if not attrs.get("themes"):
        missing.append("themes")
    return missing
