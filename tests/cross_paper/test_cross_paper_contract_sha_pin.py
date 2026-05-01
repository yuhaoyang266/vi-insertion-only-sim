import re
from pathlib import Path

from vi_full import cross_paper_bridge


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_cross_paper_contract_sha_pin_matches_document() -> None:
    contract_path = REPO_ROOT / cross_paper_bridge.CONTRACT_RELATIVE_PATH

    assert contract_path.exists()
    assert cross_paper_bridge.compute_contract_sha(contract_path) == cross_paper_bridge.CONTRACT_SHA
    assert re.fullmatch(r"[0-9a-f]{64}", cross_paper_bridge.CONTRACT_SHA)
    assert "Paper-B verification commit: `3eb8408`" in contract_path.read_text(encoding="utf-8")


def test_cross_paper_contract_path_stays_inside_repo() -> None:
    contract_path = cross_paper_bridge.resolve_contract_path(REPO_ROOT)

    assert contract_path == REPO_ROOT / "docs" / "cross_paper_interface_contract.md"
