# Cover Letter Draft

Dear Editors,

Please consider our manuscript, **"Support-Gated Variable-Impedance Learning in a 3DoF Insertion
Benchmark,"** for review.

This submission studies a controlled, simulation-only 3DoF analytical insertion benchmark with an
explicit variable-impedance action interface. The paper's contribution is intentionally narrow. We
frame the result as a benchmark-local, teacher-coupled learnability study rather than as a general
robotics theorem or a broad algorithm leaderboard. Within this controlled setting, the paper makes
three main points.

First, it packages the main recipe as **Support-Gated Variable-Impedance Learning (SG-VI)**:
explicit variable-impedance commands, behavior-cloning warm-start, and factorized support controls
over demonstrations, resets, and PPO budget. Second, it introduces **Support Coverage Index (SCI)**,
a benchmark-local quantized rollout-to-demonstration support-overlap diagnostic that makes the
learnability gate measurable rather than only descriptive. Third, it shows that under the matched
3DoF contract, PPO, SAC, and TD3 from scratch remain outside useful contact, while BC-based support
reopens the contact gate and variable impedance retains a localized high-friction load/work
advantage once contact is reached.

The manuscript also keeps its limits explicit. The benchmark is simulation-only, translational, and
teacher-coupled; it does not claim hardware validation, sim-to-real transfer, or a teacher-
independent causal result. We believe this controlled framing is appropriate for readers interested
in contact-rich insertion, demonstration-guided policy learning, and the boundary between upstream
support design and downstream optimizer choice.

The repository package accompanying the manuscript includes the LaTeX source, figure assets, frozen
artifacts, and focused reproduction/export entrypoints used to support the paper-facing claims.

Thank you for your consideration.

Sincerely,

Yu Haoyang
