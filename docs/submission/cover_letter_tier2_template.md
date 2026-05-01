# Tier-2 Cover Letter Template

Dear Editor,

Please consider the enclosed manuscript, "Support-Gated Learnability and Variable-Impedance Load
Paths in a 3DoF Insertion Benchmark," for review.

The manuscript presents a simulation-only insertion benchmark for support-gated learnability under
an explicit 3DoF variable-impedance action interface. The central claim remains bounded: the paper
studies when demonstration support opens useful contact under a matched benchmark and when variable
impedance changes the local high-friction load path. It does not claim hardware validation,
force-bounded safety guarantees, or a general sim-to-real metric.

For a Tier-2 venue, the submission now has a documented external-validity path. The bridge
uses `docs/cross_paper_interface_contract.md` to pin the interface between this paper's analytical
3DoF benchmark and the companion Paper-B MuJoCo safety-layer environment. The current artifacts
include a contract-level cross-sim dry-run smoke, a within-A contact-parameter sensitivity smoke,
and an IQL/CQL offline-baseline scaffold. These artifacts are presented as a conservative checkpoint,
with role-separated Paper-B provenance, not as unlanded cross-simulator physics results.

The repository package includes the LaTeX source, paper-facing artifacts, cross-paper contract,
focused reproduction scripts, reviewer smoke tests, and progress log entries that record command
outputs and artifact paths. The paper-facing numbers remain tied to checked-in artifacts and are
kept separate from the external-validity smoke scaffolds.

Sincerely,

Anonymous Authors
