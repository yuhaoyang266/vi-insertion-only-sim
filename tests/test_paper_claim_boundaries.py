"""Claim-boundary tests for paper/main.tex.

Enforces that manuscript prose remains benchmark-local, teacher-coupled, and
free of universal generalization claims.  Each test greps for unsafe phrases
and either rejects them outright or checks that they only appear inside
whitelisted (already-qualified) lines.
"""
from __future__ import annotations

import re
from pathlib import Path

PAPER = Path(__file__).resolve().parents[1] / "paper" / "main.tex"


def _lines() -> list[str]:
    return PAPER.read_text(encoding="utf-8").splitlines()


def test_no_state_of_the_art() -> None:
    for i, line in enumerate(_lines(), 1):
        assert "state of the art" not in line.lower(), (
            f"line {i}: 'state of the art' found — use benchmark-local framing"
        )


_UNIVERSAL_PHRASE_WHITELIST = [
    r"rather than",
    r"instead of",
    r"not\b",
]


def test_no_universal_method_claim() -> None:
    unsafe = [
        r"universal\s+robotics?\s+method",
        r"universal\s+insertion\s+metric",
        r"general\s+sim.to.real\s+claim",
    ]
    for i, line in enumerate(_lines(), 1):
        for pat in unsafe:
            if re.search(pat, line, re.IGNORECASE):
                assert any(re.search(w, line, re.IGNORECASE) for w in _UNIVERSAL_PHRASE_WHITELIST), (
                    f"line {i}: unqualified '{pat}' match: {line.strip()}"
                )


# Phrases that are only allowed inside whitelisted (already-qualified) lines.
_UNIVERSAL_WHITELIST = [
    "not a universal",
    "not.*universal",
    "rather than.*universal",
    "beyond.*universal",
    "benchmark.local",
    "teacher.coupled",
    "teacher-independent",
    "no universal",
    "instead of.*assigning",
    "instead of",
]


def test_universal_appears_only_qualified() -> None:
    for i, line in enumerate(_lines(), 1):
        if re.search(r"\buniversal\b", line, re.IGNORECASE):
            assert any(re.search(w, line, re.IGNORECASE) for w in _UNIVERSAL_WHITELIST), (
                f"line {i}: 'universal' without qualifying context: {line.strip()}"
            )


_SCI_WHITELIST = [
    "benchmark.local",
    "not.*proof",
    "not.*generali[sz]",
    "diagnostic",
    "complement",
    "support.coverage",
    "teacher.coupled",
]


def test_sci_not_generalization_proof() -> None:
    for i, line in enumerate(_lines(), 1):
        if re.search(r"\bSCI\b", line) and re.search(r"generali[sz]|proof|prove", line, re.IGNORECASE):
            assert any(re.search(w, line, re.IGNORECASE) for w in _SCI_WHITELIST), (
                f"line {i}: SCI framed as generalization proof: {line.strip()}"
            )


_DAPG_WHITELIST = [
    "matched.protocol",
    "mechanism control",
    "not.*faithful",
    "not.*full reproduction",
    "not.*reproduction",
    "abbreviated",
]


def test_dapg_lite_not_faithful_reproduction() -> None:
    for i, line in enumerate(_lines(), 1):
        if re.search(r"DAPG.lite", line, re.IGNORECASE):
            if re.search(r"reproduc|faithful|prior|original", line, re.IGNORECASE):
                assert any(re.search(w, line, re.IGNORECASE) for w in _DAPG_WHITELIST), (
                    f"line {i}: DAPG-lite framed as faithful reproduction: {line.strip()}"
                )


_PPO_WHITELIST = [
    "not.*never",
    "not.*all PPO",
    "does not.*in principle",
    "in principle",
    "without proving",
    "not that.*never",
    "not that",
    "not.*coarse",
    "too coarse",
    "saying that",
    "not reach useful contact",
    "not.*every",
    "benchmark.local",
    "under the present interface",
    "non.contact failure",
    "non-contact",
]


def test_ppo_not_implied_universal_failure() -> None:
    for i, line in enumerate(_lines(), 1):
        if re.search(r"PPO", line) and re.search(r"fail|cannot|impossible|never", line, re.IGNORECASE):
            assert any(re.search(w, line, re.IGNORECASE) for w in _PPO_WHITELIST), (
                f"line {i}: PPO implied as universally failing: {line.strip()}"
            )


_CEILING_WHITELIST = [
    "not.*support.*ranking",
    "not.*meaningful",
    "does not support",
    "ceiling.sat",
    "budget.sensitive",
    "local",
    "protocol",
    "not.*leaderboard",
    "not.*global",
    "evidence role",
    "Pareto",
    "Instead",
]


def test_near_ceiling_not_global_ranking() -> None:
    for i, line in enumerate(_lines(), 1):
        if re.search(r"1\.000|near.ceiling|ceiling", line, re.IGNORECASE):
            if re.search(r"ranking|superior|outperform|best|better than", line, re.IGNORECASE):
                assert any(re.search(w, line, re.IGNORECASE) for w in _CEILING_WHITELIST), (
                    f"line {i}: near-ceiling framed as global ranking: {line.strip()}"
                )


def test_sgvi_is_benchmark_local() -> None:
    text = PAPER.read_text(encoding="utf-8")
    assert "benchmark-local" in text or "benchmark.local" in text, (
        "paper must contain 'benchmark-local' scoping for SG-VI"
    )


_SIM2REAL_WHITELIST = [
    "no",
    "not",
    "without",
    "beyond",
    "limitation",
    "simulation.only",
    "proxy",
    "rather than",
    "instead of",
    "still",
    "but",
    "no.real.robot",
    "no.hardware",
    "calibration",
]


def test_no_sim_to_real_claim() -> None:
    for i, line in enumerate(_lines(), 1):
        if re.search(r"sim.to.real|real.robot|hardware", line, re.IGNORECASE):
            assert any(re.search(w, line, re.IGNORECASE) for w in _SIM2REAL_WHITELIST), (
                f"line {i}: unqualified sim-to-real/hardware claim: {line.strip()}"
            )
