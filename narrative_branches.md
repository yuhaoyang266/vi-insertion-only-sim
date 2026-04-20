# Sprint 2A Narrative Branch Lock

## Pre-Registered Branches

### Branch A: pure RL cannot enter useful contact under the frozen 3DoF contract

Pure RL baselines remain outside useful contact under the frozen nominal-train, nominal-eval 3DoF
pilot contract. The paper may use this as a controlled negative result: broader pure-RL families
do not cross the contact gate within the tested budget range.

### Branch B: off-policy reaches contact but remains sample-inefficient

At least one off-policy family enters contact, but remains clearly weaker than demo-supported
anchors. The paper would then emphasize sample-efficiency differentiation rather than a pure
contact-gate failure.

### Branch C: off-policy approaches demo-supported performance

At least one pure-RL off-policy family approaches the demo-supported anchor closely enough that
the paper must pivot toward benchmark methodology and algorithmic comparison rather than claiming
demonstration support as the primary gate.

## Selected Branch

Selected branch: A

Selection date: 2026-04-20 Asia/Shanghai

Evidence source:

- `outputs/pilot_report/three_dof_cross_family_pilot_report.json`
- `outputs/pilot_chunks/three_dof_cross_family_pilot__*.json`

## Branch-A Evidence Table

| method | 50k final dist | 100k final dist | 200k final dist | contact? |
| --- | ---: | ---: | ---: | --- |
| PPO | 31.02 mm | 29.47 mm | 25.48 mm | no |
| SAC | 23.27 mm | 17.58 mm | 16.67 mm | no |
| TD3 | 30.78 mm | 28.62 mm | 25.56 mm | no |

The Sprint 1 pilot does not show successful insertion or contact entry for any pure-RL family.
The only visible algorithmic separation is terminal distance-to-contact, where SAC is consistently
best.
Therefore, the paper should not claim that SAC solves the task; it should claim that broader
pure-RL families still fail to cross the contact gate under the frozen contract.

## Claim Boundary

Allowed:

- Pure RL remains outside useful contact under the frozen 3DoF nominal-train, nominal-eval,
  50k/100k/200k contract.
- SAC reduces terminal distance-to-contact more than PPO or TD3 in this pilot.

Not allowed:

- SAC solves insertion.
- Off-policy methods reach useful contact.
- This pilot proves pure RL can never solve insertion.
