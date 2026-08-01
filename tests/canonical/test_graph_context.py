from seion_core.canonical.context_compiler import classify_task
from seion_core.canonical.graph import build_graph


def test_task_classification_and_graph_shape(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src/x.py").write_text("def f(): pass\n", encoding="utf-8")
    graph = build_graph(tmp_path)
    assert classify_task("prove the theorem") == "proof"
    assert graph["nodes"]
    assert any(node["type"] == "SourceModule" for node in graph["nodes"])
