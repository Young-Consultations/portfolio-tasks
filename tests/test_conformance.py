import json
from pathlib import Path

from scripts.run_tc_mvp_ci_001 import (
    EXPECTED_COMPATIBILITY_BLOBS,
    git_blob_sha1,
    run,
    validate_pin,
)


def test_complete_shared_oracle_passes_through_real_adapter_seam() -> None:
    assert run() == []
    report = json.loads(Path(".ai-sdlc/conformance/tc-mvp-ci-001.json").read_text(encoding="utf-8"))
    assert len(report["scenario_results"]) == 29
    assert sum(row["adapter_invoked"] for row in report["scenario_results"]) == 22
    assert all(row["result"] == "pass" for row in report["scenario_results"])
    assert report["failures"] == []
    assert all(value == 0 for value in report["effect_traps"].values())


def test_evidence_pin_binds_exact_shared_and_target_files() -> None:
    pin = json.loads(Path("config/mvp-conformance-pin.json").read_text(encoding="utf-8"))
    assert validate_pin(pin) == []
    for relative, expected in EXPECTED_COMPATIBILITY_BLOBS.items():
        assert git_blob_sha1(Path(relative).read_bytes()) == expected
    report = json.loads(Path(".ai-sdlc/conformance/tc-mvp-ci-001.json").read_text(encoding="utf-8"))
    assert report["adapter_revision"] == pin["adapter_revision"]
    assert report["compatibility_sha"] == pin["compatibility_sha"]


def test_evidence_does_not_claim_activation_or_production_readiness() -> None:
    report = json.loads(Path(".ai-sdlc/conformance/tc-mvp-ci-001.json").read_text(encoding="utf-8"))
    assert report["production_readiness_claim"] is False
    assert report["activation_requested"] is False
    assert report["activation_evidence_sufficient"] is True
    assert report["adapter_tag_published"] is False
    assert report["receiver_live_verification"] == "pending-ai-sdlc-v2.3.1-tag"
