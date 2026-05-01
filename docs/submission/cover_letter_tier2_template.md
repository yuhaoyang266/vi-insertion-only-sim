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
include a contract-level cross-sim dry-run smoke, a five-profile 20-episode-per-seed within-A
contact-parameter sensitivity artifact, an alternative within-A contact-model cross-check, and an
offline demonstration dataset with a `bc_offline_stub` baseline smoke. These artifacts are presented
as a conservative checkpoint with role-separated Paper-B provenance. They do not claim Paper-B
physics ranking, hardware validation, or trained IQL/CQL results; those remain deferred until real
Paper-A policy artifacts, completed Paper-B episode records, and an actual offline-RL training path
exist.

The repository package includes the LaTeX source, paper-facing artifacts, cross-paper contract,
focused reproduction scripts, reviewer smoke tests, and progress log entries that record command
outputs and artifact paths. The paper-facing numbers remain tied to checked-in artifacts and are
kept separate from the external-validity smoke scaffolds.

Sincerely,

Anonymous Authors
