import json

import numpy as np

from seion_core.research_v3.run_schema import (
    EXTREMIZER_FILES,
    MANDATORY_FILES,
    V3RunConfig,
    validate_run_artifacts,
    write_run_artifacts,
)
from seion_core.research_v3.typed_tree import Leaf, Node


def test_complete_run_artifact_contract(tmp_path, repo_root):
    tree = Node("mu", "tau", (Leaf(0, "tau"), Leaf(1, "tau")))
    config = V3RunConfig(
        block="A",
        instance_id="schema-test",
        method="exact",
        seed=0,
        precision="float64",
        device="cpu",
        parameters={"eta": 0.1},
        restarts=1,
    )
    run_dir = tmp_path / "run"
    write_run_artifacts(
        run_dir,
        repo_root=repo_root,
        config=config,
        tree=tree,
        type_signature={"tau": {"dimension": 2, "rank": 1}},
        law_tensors={"mu": np.zeros((2, 2, 2))},
        local_constants={"mu": {"M": 1.0, "rho": 0.1}},
        reference_metrics={"ambient": 0.1},
        optimization_history=[{"step": 0, "ratio": 1.0}],
        node_contributions=[{"path": "root", "value": 0.1}],
        final_metrics={"ambient": 0.1},
        certificate={"status": "CERTIFIED_UPPER_BOUND", "upper": 0.1},
        command="python schema-test",
        extremizer={
            "best_lower_bound": {"lower": 0.1},
            "certified_upper_bound": {"upper": 0.1},
            "optimality_gap": {"relative": 0.0},
            "tensor": np.zeros((2, 2, 2)),
            "inputs": np.ones((2, 1)),
            "independent_recheck": {"passed": True},
        },
    )
    validate_run_artifacts(run_dir, extremizer=True)
    names = {path.name for path in run_dir.iterdir()}
    assert set(MANDATORY_FILES).issubset(names)
    assert set(EXTREMIZER_FILES).issubset(names)
    manifest = json.loads((run_dir / "run_manifest.json").read_text())
    assert manifest["status"] == "COMPLETE"
    assert len(manifest["source_commit"]) == 40
