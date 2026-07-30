"""Phase 0 legacy ingestion for the spectral A-N certification track.

Reads the two named legacy assets (the v17 audit script and the
REPRO_SUMMARIES_A_TO_M_VALIDATED.txt run log) plus every run directory
under spectral/runs/, and produces a non-destructive evidence layer:

- immutable hash-verified copies of the two legacy files under
  spectral/legacy/v17/
- legacy_a_to_n_manifest.yaml: hashes and inventory of every legacy file
  and run directory
- legacy_run_lineage.json: resume-chain graph reconstructed from
  `resume_path` references
- legacy_run_dedup_report.md: dedup by script hash / config fingerprint /
  seed / precision / checkpoint hash / audit-state hash
- legacy_claim_reclassification.yaml: reclassifies every historical run
  against the mission's typed-gate vocabulary instead of trusting the
  legacy `master_score`

Nothing under spectral/runs/ or the original legacy files is modified.
Every number in the outputs is derived from a field actually present in
the source data; nothing is asserted without a corresponding parsed value.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
SPECTRAL_ROOT = REPO_ROOT / "spectral"
LEGACY_SCRIPT_SRC = SPECTRAL_ROOT / "seion_master_audit_A_to_N_v17_blackwell_repro_fix.py"
LEGACY_LOG_SRC = SPECTRAL_ROOT / "runs" / "REPRO_SUMMARIES_A_TO_M_VALIDATED.txt"
RUNS_DIR = SPECTRAL_ROOT / "runs"
LEGACY_DEST = SPECTRAL_ROOT / "legacy" / "v17"

HEADER_RE = re.compile(
    r"^={20,}\nRUN VALIDATED \(A-M SEQUENCE DETECTED\)\nDIRECTORY: (?P<name>.+)\n"
    r"FILE: (?P<file>.+)\nFULL PATH: (?P<path>.+)\n={20,}\n",
    re.MULTILINE,
)

# Fields excluded from the config fingerprint because they are path/identity
# artifacts of where a run happened to be launched from, not part of its
# scientific configuration.
FINGERPRINT_EXCLUDE_KEYS = {"outdir", "resume_path", "script_path"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def config_fingerprint(config: dict[str, Any]) -> str:
    trimmed = {k: v for k, v in config.items() if k not in FINGERPRINT_EXCLUDE_KEYS}
    payload = json.dumps(trimmed, sort_keys=True, default=str).encode("utf-8")
    return sha256_bytes(payload)


def audit_state_fingerprint(blocks: dict[str, Any]) -> str:
    payload = json.dumps(blocks, sort_keys=True, default=str).encode("utf-8")
    return sha256_bytes(payload)


@dataclass
class RunEvidence:
    name: str
    sources: list[str] = field(default_factory=list)
    config: dict[str, Any] = field(default_factory=dict)
    master_audit: dict[str, Any] = field(default_factory=dict)
    blocks: dict[str, Any] = field(default_factory=dict)
    env: dict[str, Any] = field(default_factory=dict)
    script_sha256_reported: str | None = None
    files_manifest: dict[str, Any] = field(default_factory=dict)
    on_disk_files: dict[str, str] = field(default_factory=dict)  # relpath -> sha256
    txt_log_lines: tuple[int, int] | None = None


def parse_txt_log(path: Path) -> dict[str, RunEvidence]:
    """Split the legacy repro-summary log into one RunEvidence per block."""
    text = path.read_text(encoding="utf-8")
    headers = list(HEADER_RE.finditer(text))
    runs: dict[str, RunEvidence] = {}
    for i, match in enumerate(headers):
        name = match.group("name").strip()
        body_start = match.end()
        body_end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        body = text[body_start:body_end].strip()
        try:
            payload = json.loads(body)
        except json.JSONDecodeError as exc:
            raise ValueError(f"failed to parse JSON body for run '{name}': {exc}") from exc
        line_start = text.count("\n", 0, match.start()) + 1
        line_end = text.count("\n", 0, body_end) + 1
        evidence = RunEvidence(
            name=name,
            sources=["txt_log:REPRO_SUMMARIES_A_TO_M_VALIDATED.txt"],
            config=payload.get("config", {}) or {},
            master_audit=payload.get("master_audit", {}) or {},
            blocks=payload.get("blocks", {}) or {},
            env=payload.get("env", {}) or {},
            script_sha256_reported=payload.get("script_sha256"),
            files_manifest=payload.get("files", {}) or {},
            txt_log_lines=(line_start, line_end),
        )
        runs[name] = evidence
    return runs


def hash_directory(directory: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in sorted(p for p in directory.rglob("*") if p.is_file()):
        rel = str(path.relative_to(directory)).replace("\\", "/")
        hashes[rel] = sha256_file(path)
    return hashes


def scan_run_directories(runs_dir: Path) -> dict[str, RunEvidence]:
    """Read every run directory on disk directly (ground truth, independent
    of whether the txt log also mentions it)."""
    out: dict[str, RunEvidence] = {}
    for entry in sorted(p for p in runs_dir.iterdir() if p.is_dir()):
        name = entry.name
        file_hashes = hash_directory(entry)
        evidence = RunEvidence(name=name, sources=["run_directory"], on_disk_files=file_hashes)
        summary_path = entry / "summary.json"
        if summary_path.exists():
            try:
                payload = json.loads(summary_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                payload = {}
            evidence.config = payload.get("config", {}) or {}
            evidence.master_audit = payload.get("master_audit", {}) or {}
            evidence.blocks = payload.get("blocks", {}) or {}
            evidence.env = payload.get("env", {}) or {}
            evidence.script_sha256_reported = payload.get("script_sha256")
            evidence.files_manifest = payload.get("files", {}) or {}
        out[name] = evidence
    return out


def merge_evidence(txt_runs: dict[str, RunEvidence], dir_runs: dict[str, RunEvidence]) -> dict[str, RunEvidence]:
    merged: dict[str, RunEvidence] = {}
    all_names = set(txt_runs) | set(dir_runs)
    for name in sorted(all_names):
        txt = txt_runs.get(name)
        d = dir_runs.get(name)
        if txt and d:
            txt.sources = txt.sources + d.sources
            txt.on_disk_files = d.on_disk_files
            merged[name] = txt
        elif txt:
            merged[name] = txt
        else:
            assert d is not None
            merged[name] = d
    return merged


def checkpoint_hash_for(evidence: RunEvidence) -> str | None:
    for key in ("best_model.pt", "latest_checkpoint.pt"):
        if key in evidence.on_disk_files:
            return evidence.on_disk_files[key]
    return None


def dedup_key(evidence: RunEvidence) -> tuple[str, str, Any, Any, str, str]:
    cfg = evidence.config
    return (
        evidence.script_sha256_reported or "UNKNOWN_SCRIPT_HASH",
        config_fingerprint(cfg) if cfg else "NO_CONFIG",
        cfg.get("seed"),
        cfg.get("dtype"),
        checkpoint_hash_for(evidence) or "NO_CHECKPOINT_HASH",
        audit_state_fingerprint(evidence.blocks) if evidence.blocks else "NO_BLOCKS",
    )


def resume_parent_name(evidence: RunEvidence) -> str | None:
    resume_path = evidence.config.get("resume_path")
    if not resume_path:
        return None
    # resume_path looks like "runs\\<parent_name>\\latest_checkpoint.pt"
    parts = re.split(r"[\\/]+", str(resume_path))
    parts = [p for p in parts if p and p != "runs"]
    if len(parts) >= 2:
        return parts[0]
    return None


def build_lineage(evidence_by_name: dict[str, RunEvidence]) -> dict[str, Any]:
    nodes = []
    edges = []
    for name, ev in evidence_by_name.items():
        parent = resume_parent_name(ev)
        resumed = bool(ev.config.get("resume"))
        nodes.append(
            {
                "name": name,
                "resume": resumed,
                "resume_path": ev.config.get("resume_path"),
                "strict_resume": ev.config.get("strict_resume"),
                "restore_rng": ev.config.get("restore_rng"),
                "resume_optimizer": ev.config.get("resume_optimizer"),
                "seed": ev.config.get("seed"),
                "lr": ev.config.get("lr"),
                "eval_mode": ev.config.get("eval_mode"),
                "is_root": parent is None or parent not in evidence_by_name,
            }
        )
        if parent and parent in evidence_by_name:
            edges.append({"child": name, "parent": parent})
        elif resumed and parent:
            edges.append({"child": name, "parent": parent, "parent_not_in_dataset": True})

    def depth(name: str, seen: set[str]) -> int:
        if name in seen:
            return 0  # cycle guard; should not occur but never trust blindly
        seen = seen | {name}
        parents = [e["parent"] for e in edges if e["child"] == name and not e.get("parent_not_in_dataset")]
        if not parents:
            return 0
        return 1 + max(depth(p, seen) for p in parents)

    for node in nodes:
        node["chain_depth"] = depth(node["name"], set())

    return {"nodes": nodes, "edges": edges}


CRITICAL_BLOCK_STATUS_VALUES = {"PASS", "PASS_STRONG", "WARN", "WARN_GEOMETRIC", "N/A"}


def reclassify_run(evidence: RunEvidence, dedup_key_value: tuple) -> dict[str, Any]:
    cfg = evidence.config
    ma = evidence.master_audit
    caveats: list[str] = []

    eval_mode = cfg.get("eval_mode")
    if eval_mode != "certification":
        caveats.append(
            f"eval_mode={eval_mode!r} (not 'certification'): thresholds_for_mode() applies looser "
            "screening tolerances (up to ~1000x looser per block); this run cannot support a "
            "certification-tier claim regardless of its reported master_score."
        )

    if cfg.get("resume") and cfg.get("restore_rng") is False:
        caveats.append(
            "restore_rng=false on a resumed run: the RNG stream was not restored from checkpoint, "
            "so the resumed segment is a fresh-seeded continuation, not a faithful replay of the "
            "original trajectory."
        )
    if cfg.get("resume") and cfg.get("strict_resume") is False:
        caveats.append(
            "strict_resume=false on a resumed run: checkpoint loading is non-strict, so silent "
            "shape/parameter mismatches between the checkpoint and current model would not raise."
        )
    lr = cfg.get("lr")
    if cfg.get("resume") and lr == 0:
        caveats.append(
            "lr=0 on a resumed run: this run performed no further optimization; it is a checkpoint "
            "replay / re-evaluation, not independent optimization evidence."
        )

    statuses = ma.get("statuses", {}) or {}
    unknown_statuses = sorted(set(statuses.values()) - CRITICAL_BLOCK_STATUS_VALUES)
    if unknown_statuses:
        caveats.append(f"unrecognized block status value(s) encountered: {unknown_statuses}")
    warn_blocks = sorted(k for k, v in statuses.items() if v in ("WARN", "WARN_GEOMETRIC"))
    na_blocks = sorted(k for k, v in statuses.items() if v == "N/A")

    reported_master_score = ma.get("master_score")

    if eval_mode != "certification":
        ceiling = "EMPIRICAL_SCREENING_PASS" if statuses and not warn_blocks else "EMPIRICAL_SCREENING_PASS"
        if warn_blocks:
            ceiling = "WARN"  # a run with any WARN block cannot be called a screening pass either
    else:
        ceiling = "NUMERICAL_SANITY_PASS" if not warn_blocks else "WARN"

    return {
        "legacy_master_score_DO_NOT_USE_AS_CERTIFICATE": reported_master_score,
        "legacy_statuses": statuses,
        "warn_blocks": warn_blocks,
        "na_blocks_scored_as_full_credit_in_legacy_scoring": na_blocks,
        "reclassified_status": ceiling,
        "caveats": caveats,
        "dedup_key": {
            "script_sha256": dedup_key_value[0],
            "config_fingerprint": dedup_key_value[1],
            "seed": dedup_key_value[2],
            "dtype": dedup_key_value[3],
            "checkpoint_sha256": dedup_key_value[4],
            "audit_state_fingerprint": dedup_key_value[5],
        },
    }


def copy_legacy_files() -> dict[str, Any]:
    LEGACY_DEST.mkdir(parents=True, exist_ok=True)
    entries = {}
    for src in (LEGACY_SCRIPT_SRC, LEGACY_LOG_SRC):
        dest = LEGACY_DEST / src.name
        src_hash = sha256_file(src)
        shutil.copy2(src, dest)
        dest_hash = sha256_file(dest)
        if src_hash != dest_hash:
            raise RuntimeError(f"copy verification failed for {src.name}: {src_hash} != {dest_hash}")
        entries[src.name] = {
            "original_path": str(src.relative_to(REPO_ROOT)).replace("\\", "/"),
            "copied_path": str(dest.relative_to(REPO_ROOT)).replace("\\", "/"),
            "sha256": src_hash,
            "size_bytes": src.stat().st_size,
        }
    return entries


def main() -> None:
    legacy_files = copy_legacy_files()
    txt_runs = parse_txt_log(LEGACY_LOG_SRC)
    dir_runs = scan_run_directories(RUNS_DIR)
    merged = merge_evidence(txt_runs, dir_runs)

    # --- legacy_a_to_n_manifest.yaml ---
    import yaml

    run_dir_inventory = {}
    for name, ev in merged.items():
        run_dir_inventory[name] = {
            "sources": ev.sources,
            "in_txt_log": any(s.startswith("txt_log") for s in ev.sources),
            "on_disk": "run_directory" in ev.sources,
            "file_count_on_disk": len(ev.on_disk_files),
            "txt_log_line_range": list(ev.txt_log_lines) if ev.txt_log_lines else None,
            "script_sha256_reported": ev.script_sha256_reported,
        }

    manifest = {
        "version": 1,
        "generated_by": "spectral/certification_v18/tools/ingest_legacy.py",
        "scope_class": "SPECTRAL_LEGACY_TRACK",
        "legacy_files": legacy_files,
        "current_repo_script_sha256": sha256_file(LEGACY_SCRIPT_SRC),
        "run_count_total_unique": len(merged),
        "run_count_from_txt_log": len(txt_runs),
        "run_count_directory_only": len([n for n, ev in merged.items() if "run_directory" in ev.sources and not any(s.startswith("txt_log") for s in ev.sources)]),
        "run_count_txt_log_only_no_directory": len([n for n, ev in merged.items() if not ("run_directory" in ev.sources) ]),
        "runs": run_dir_inventory,
    }
    (LEGACY_DEST / "legacy_a_to_n_manifest.yaml").write_text(
        yaml.safe_dump(manifest, sort_keys=False, width=100), encoding="utf-8"
    )

    # --- legacy_run_lineage.json ---
    lineage = build_lineage(merged)
    (LEGACY_DEST / "legacy_run_lineage.json").write_text(json.dumps(lineage, indent=2), encoding="utf-8")

    # --- dedup ---
    from collections import defaultdict

    groups: dict[tuple, list[str]] = defaultdict(list)
    keys_by_name: dict[str, tuple] = {}
    for name, ev in merged.items():
        key = dedup_key(ev)
        keys_by_name[name] = key
        groups[key].append(name)

    dedup_lines = [
        "# Legacy A-N run dedup report",
        "",
        f"- Unique run names found: {len(merged)} ({len(txt_runs)} from the txt log, "
        f"{len(dir_runs)} directories on disk, overlap {len(set(txt_runs) & set(dir_runs))}).",
        f"- Unique dedup groups (script_sha256, config_fingerprint, seed, dtype, "
        f"checkpoint_sha256, audit_state_fingerprint): {len(groups)}.",
        "",
        "## Groups",
        "",
    ]
    for key, names in sorted(groups.items(), key=lambda kv: kv[0][0] or ""):
        dedup_lines.append(f"### script={key[0][:12]}... seed={key[2]} dtype={key[3]}")
        dedup_lines.append(f"members: {', '.join(sorted(names))}")
        dedup_lines.append("")

    distinct_seeds = {merged[n].config.get("seed") for n in merged if merged[n].config}
    distinct_scripts = {merged[n].script_sha256_reported for n in merged if merged[n].script_sha256_reported}
    dedup_lines.append("## Cross-cutting findings")
    dedup_lines.append(f"- Distinct seeds observed across all runs with a parsed config: {sorted(s for s in distinct_seeds if s is not None)}")
    dedup_lines.append(f"- Distinct reported script_sha256 values: {len(distinct_scripts)} ({sorted(distinct_scripts)})")
    dedup_lines.append(
        f"- Current repo copy of the legacy script hashes to {sha256_file(LEGACY_SCRIPT_SRC)[:16]}...; "
        "compare against reported script_sha256 values above to check whether the script in the "
        "repository today matches what actually produced the historical runs."
    )
    (LEGACY_DEST / "legacy_run_dedup_report.md").write_text("\n".join(dedup_lines) + "\n", encoding="utf-8")

    # --- legacy_claim_reclassification.yaml ---
    reclass = {}
    for name, ev in merged.items():
        reclass[name] = reclassify_run(ev, keys_by_name[name])
    (LEGACY_DEST / "legacy_claim_reclassification.yaml").write_text(
        yaml.safe_dump(reclass, sort_keys=False, width=100), encoding="utf-8"
    )

    print(f"Wrote manifest, lineage, dedup report, and reclassification to {LEGACY_DEST}")
    print(f"Total unique runs: {len(merged)} | dedup groups: {len(groups)} | distinct seeds: {sorted(s for s in distinct_seeds if s is not None)}")


if __name__ == "__main__":
    main()
