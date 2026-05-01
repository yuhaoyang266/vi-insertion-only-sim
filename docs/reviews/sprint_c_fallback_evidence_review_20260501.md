# Sprint C Fallback Evidence Review (2026-05-01)

## Scope

This review covers the within-A fallback evidence packet after the Repair A-C fixes and the Week 1 alternative contact-law cross-check. It does not claim Paper-B physics ranking, hardware validation, or trained IQL/CQL results.

## Artifacts Reviewed

- `outputs/revision/contact_parameter_sensitivity_20260501.json`
- `outputs/revision/contact_parameter_sensitivity_20260501.csv`
- `outputs/revision/contact_parameter_sensitivity_20260501.md`
- `outputs/revision/alt_contact_model_cross_check_20260501.json`
- `outputs/revision/alt_contact_model_cross_check_20260501.csv`
- `outputs/revision/alt_contact_model_cross_check_20260501.md`

## Evidence Readout

- Contact-parameter sensitivity now covers all five profiles, seeds `0 1 2`, fixed/variable handcrafted policies, and `20` episodes per seed.
- The sensitivity JSON records `150` aggregate rows, `450` seed-summary rows, `100` paired deltas versus nominal levels, and deterministic bootstrap CI rows for each summary metric.
- The largest success-rate sensitivity remains `force_noise_std_range` on `noisy_force` with the variable-impedance policy at the `high` level: success changes from `0.9333333333333332` nominal to `0.75`.
- Force/work/contact-step sensitivity is dominated by `wall_friction_range` on `high_friction`: peak-force delta `1.0921436545469412`, p95 peak-force delta `1.3165884012196365`, contact-step delta `6.333333333333336`, and contact-work delta `0.004574012293608057`.
- Largest VI-vs-fixed divergence is `mean_contact_steps` on `noisy_force` / `force_noise_std_range`: variable minus fixed is `34.06666666666666`.
- The alternative contact-law cross-check is a within-A fallback only. It has `20` rows and `10` paired base-vs-alternative deltas across five profiles and two handcrafted policies.

## Learned-Suite Proxy Status

No local learned policy artifacts or deterministic reconstructed policy files were found under the repository. Week 2 therefore keeps learned-suite proxy rows out of the evidence packet rather than fabricating policy-backed claims.

## Claim Boundary

The current fallback packet supports a conservative external-validity discussion inside the Paper-A simulator family. It does not support claims about Paper-B 7-DoF MuJoCo ranking, real hardware robustness, or trained offline RL baselines.
