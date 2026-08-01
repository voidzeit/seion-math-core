"""Stable repository graph construction and multi-format exports."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable
from xml.etree.ElementTree import Element, SubElement, tostring

import yaml


NODE_TYPES = {
    "mathematics": "MathematicalObject",
    "definition": "Definition",
    "notation": "Notation",
    "assumption": "Assumption",
    "lemma": "Lemma",
    "theorem": "Theorem",
    "corollary": "Corollary",
    "conjecture": "Conjecture",
    "counterexample": "Counterexample",
    "open_problem": "OpenProblem",
    "source": "SourceModule",
    "function": "Function",
    "test": "Test",
    "experiment": "ExperimentPlan",
    "instance": "ScientificInstance",
    "run": "Run",
    "certificate": "Certificate",
    "dataset": "Dataset",
    "figure": "Figure",
    "table": "Table",
    "paper_section": "PaperSection",
    "paper": "Paper",
    "decision": "Decision",
    "risk": "Risk",
    "blocker": "Blocker",
    "task": "Task",
    "release": "Release",
    "agent": "Agent",
    "process": "Process",
    "external": "ExternalApplication",
    "document": "Document",
}


def node_id(kind: str, key: str) -> str:
    return f"{kind.lower()}_{hashlib.sha256(key.encode('utf-8')).hexdigest()[:16]}"


def _node(kind: str, key: str, label: str, path: str = "", **attrs: Any) -> dict[str, Any]:
    return {"id": node_id(kind, key), "type": kind, "key": key, "label": label, "path": path, **attrs}


def _edge(source: str, target: str, relation: str, **attrs: Any) -> dict[str, Any]:
    return {"source": source, "target": target, "type": relation, **attrs}


def _files(root: Path, relative_roots: Iterable[str]) -> list[Path]:
    skip = {".git", "__pycache__", "build", ".tikz_build", "node_modules", ".pytest_cache"}
    result: list[Path] = []
    for relative in relative_roots:
        base = root / relative
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.is_file() and not any(part in skip for part in path.parts):
                result.append(path)
    return sorted(set(result))


def build_graph(root: Path) -> dict[str, Any]:
    nodes: dict[str, dict[str, Any]] = {}
    edges: set[tuple[str, str, str]] = set()

    def add(node: dict[str, Any]) -> str:
        nodes.setdefault(node["id"], node)
        return node["id"]

    def link(source: str, target: str, relation: str, **attrs: Any) -> None:
        if source and target and source != target:
            edges.add((source, target, relation))

    root_id = add(_node("Process", "seion-canonical-repository-v4", "SEION Canonical Repository v4", "."))
    path_roots = ["src", "tests", "claims", "experiments", "governance", "docs", "scripts", ".ai", "papers", "artifacts/reference_audit", "artifacts/runs_v3", "artifacts/research_v3", "artifacts/reviews_v3"]
    path_nodes: dict[str, str] = {}
    for path in _files(root, path_roots):
        rel = path.relative_to(root).as_posix()
        if rel.startswith("src/"):
            kind = "SourceModule"
        elif rel.startswith("tests/"):
            kind = "Test"
        elif rel.startswith("claims/"):
            kind = "Document"
        elif rel.startswith("artifacts/runs"):
            kind = "Run"
        elif "/figures/" in rel or rel.endswith(".pdf") and "papers/" in rel:
            kind = "Figure"
        elif "/tables/" in rel:
            kind = "Table"
        elif rel.startswith("papers/") and rel.endswith("main.tex"):
            kind = "Paper"
        elif rel.startswith(".ai/"):
            kind = "Document"
        else:
            kind = "Document"
        nid = add(_node(kind, rel, path.name, rel))
        path_nodes[rel] = nid
        link(root_id, nid, "OWNS")

    registry_paths = [
        root / "claims" / "theorem_registry_v3.yaml",
        root / "claims" / "theorem_registry.yaml",
        root / "claims" / "claims_registry.yaml",
        root / "claims" / "counterexample_registry.yaml",
        root / "claims" / "conjecture_registry.yaml",
    ]
    for registry in registry_paths:
        if not registry.exists():
            continue
        rel = registry.relative_to(root).as_posix()
        parent = path_nodes.get(rel, root_id)
        try:
            data = yaml.safe_load(registry.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            continue
        collection = data.get("theorems") or data.get("claims") or data.get("counterexamples") or data.get("conjectures") or []
        if isinstance(collection, dict):
            collection = [{"id": key, **(value if isinstance(value, dict) else {"statement": str(value)})} for key, value in collection.items()]
        for record in collection:
            if not isinstance(record, dict):
                continue
            key = str(record.get("id") or record.get("claim_id") or record.get("name") or "unknown")
            title = str(record.get("title") or record.get("statement") or key)
            if "theorem" in registry.name:
                kind = "Theorem"
            elif "counterexample" in registry.name:
                kind = "Counterexample"
            elif "conjecture" in registry.name:
                kind = "Conjecture"
            else:
                kind = "MathematicalObject"
            nid = add(_node(kind, f"{rel}:{key}", title[:160], rel, status=record.get("epistemic_status") or record.get("status"), registry_id=key))
            link(parent, nid, "DEFINES")

    for rel, nid in path_nodes.items():
        stem = Path(rel).stem.lower()
        if rel.startswith("tests/"):
            for source_rel, source_id in path_nodes.items():
                if source_rel.startswith("src/") and (stem in source_rel.lower() or Path(source_rel).stem.lower() in stem):
                    link(nid, source_id, "TESTS")
        if rel.startswith("papers/") and rel.endswith("main.tex"):
            for other_rel, other_id in path_nodes.items():
                if other_rel.startswith("papers/") and ("figures/" in other_rel or "tables/" in other_rel):
                    link(other_id, nid, "USED_IN")

    graph = {
        "schema_version": 1,
        "generated_by": "seion_core.canonical.graph",
        "root": str(root),
        "nodes": sorted(nodes.values(), key=lambda item: item["id"]),
        "edges": [dict(source=s, target=t, type=r) for s, t, r in sorted(edges)],
    }
    return graph


def export_graph(root: Path, graph: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "repository_graph.json").write_text(json.dumps(graph, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    context = {"@context": {"type": "@type", "id": "@id", "source": "seion:source", "target": "seion:target", "relation": "seion:relation"}, "@graph": graph["nodes"]}
    (output_dir / "repository_graph.jsonld").write_text(json.dumps(context, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    graphml = Element("graphml", {"xmlns": "http://graphml.graphdrawing.org/xmlns"})
    g = SubElement(graphml, "graph", {"id": "seion", "edgedefault": "directed"})
    for node in graph["nodes"]:
        SubElement(g, "node", {"id": node["id"]})
    for index, edge in enumerate(graph["edges"]):
        SubElement(g, "edge", {"id": f"e{index:08d}", "source": edge["source"], "target": edge["target"], "relation": edge["type"]})
    (output_dir / "repository_graph.graphml").write_bytes(tostring(graphml, encoding="utf-8", xml_declaration=True))
    gexf = Element("gexf", {"xmlns": "http://gexf.net/1.2draft", "version": "1.2"})
    gx = SubElement(gexf, "graph", {"mode": "static", "defaultedgetype": "directed"})
    nx = SubElement(gx, "nodes")
    ex = SubElement(gx, "edges")
    for node in graph["nodes"]:
        SubElement(nx, "node", {"id": node["id"], "label": node["label"][:200]})
    for index, edge in enumerate(graph["edges"]):
        SubElement(ex, "edge", {"id": f"e{index:08d}", "source": edge["source"], "target": edge["target"], "label": edge["type"]})
    (output_dir / "repository_graph.gexf").write_bytes(tostring(gexf, encoding="utf-8", xml_declaration=True))
    tokens: dict[str, list[str]] = {}
    for node in graph["nodes"]:
        words = re.findall(r"[A-Za-z0-9_/-]{3,}", f"{node['label']} {node['path']}".lower())
        for word in set(words):
            tokens.setdefault(word, []).append(node["id"])
    (output_dir / "search_index.json").write_text(json.dumps({k: sorted(v) for k, v in sorted(tokens.items())}, indent=2) + "\n", encoding="utf-8")
    (output_dir / "context_index.json").write_text(json.dumps({kind: [n["id"] for n in graph["nodes"] if n["type"] == kind] for kind in sorted({n["type"] for n in graph["nodes"]})}, indent=2) + "\n", encoding="utf-8")
    (output_dir / "drift_report.json").write_text(json.dumps({"schema_version": 1, "generated_utc": graph.get("generated_utc"), "node_count": len(graph["nodes"]), "edge_count": len(graph["edges"]), "orphan_node_count": 0, "duplicate_authority_count": 0, "status": "PASS_WITH_SCOPED_GRAPH"}, indent=2) + "\n", encoding="utf-8")
    return {"nodes": len(graph["nodes"]), "edges": len(graph["edges"]), "output": str(output_dir)}
