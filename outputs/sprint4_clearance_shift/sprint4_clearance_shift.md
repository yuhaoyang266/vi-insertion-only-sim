# Sprint 4 Clearance Shift

Source contract: 3DoF nominal-train Sprint 4A clearance-shift stress sweep

Sprint 4A evaluates each seed once and reuses the in-memory predictor across the clearance ladder because this repository does not persist paper-ready checkpoints today.

## Clearance Ladder

| Profile | Clearance range (mm) | Pure clearance shift |
| --- | --- | --- |
| clearance_easy | 0.950 - 1.350 | true |
| nominal | 0.700 - 1.100 | true |
| clearance_hard | 0.450 - 0.750 | true |

## Suite Summary

| Suite | easy success | nominal success | clearance_hard success | success drop | hard jam | hard final dist (mm) |
| --- | --- | --- | --- | --- | --- | --- |
| BC-only (stable 32/32) | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.899 |
| BC -> PPO | 0.800 | 0.800 | 0.808 | -0.008 | 0.000 | 1.067 |
| DAPG-lite | 0.800 | 0.800 | 0.768 | 0.032 | 0.050 | 1.617 |
| Fixed-impedance RL (stable BC 32/32) | 0.800 | 0.800 | 0.800 | 0.000 | 0.000 | 1.106 |

## Claim Boundary

Allowed:
- clearance-ladder robustness claims for the selected demo-supported 3DoF suites
- stating how success/contact degrades from easy to hard clearance under the nominal-train contract
- comparing the selected four suites within this single Sprint 4A clearance-shift contract

Not allowed:
- not a mixed-contract leaderboard
- not a replacement for the frozen five-profile manuscript benchmark
- not evidence that clearance dominates every other pressure axis in the repository
- not a hardware or sim-to-real claim
