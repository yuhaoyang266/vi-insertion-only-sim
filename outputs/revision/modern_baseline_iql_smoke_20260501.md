# Modern Baseline Smoke

- algorithm: bc_offline_stub
- status: bc_offline_stub
- target_algorithm: iql_offline
- dataset_source: artifacts/main_benchmark/three_dof_offline_demo_dataset_20260501.json
- dataset_sha256: 14116380517c3f0c201f5a371ba52a5af6d84498c13d4c44b7445c0b43ce44e2
- dataset_size_bytes: 885498
- observation_shape: [42, 14]
- action_shape: [42, 5]
- sample_count: 1299
- baseline_dataset_sample_count: 1299
- baseline_eval_rows: 5

## BC Offline Stub Rows

| Profile | Success | Jam | Peak force | Final distance | Contact steps |
| --- | ---: | ---: | ---: | ---: | ---: |
| nominal | 1.0 | 0.0 | 0.5992486759366799 | 0.0009603550036752709 | 27.666666666666668 |
| tight_clearance | 1.0 | 0.0 | 0.5992486759366799 | 0.0009603550036752709 | 27.666666666666668 |
| high_friction | 1.0 | 0.0 | 1.0321016148673807 | 0.0009449074814718108 | 28.666666666666668 |
| offset_bias | 1.0 | 0.0 | 0.5992486759366799 | 0.0009603550036752709 | 27.666666666666668 |
| noisy_force | 1.0 | 0.0 | 0.8537779309022068 | 0.0009529167562723154 | 44.333333333333336 |

## Blocked On

- IQL/CQL training dependency and hyperparameter file
- comparison protocol against existing five-suite benchmark rows
