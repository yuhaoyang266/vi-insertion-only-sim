# 3DoF Contact-Parameter Sensitivity

- most_sensitive_parameter: force_noise_std_range
- seed_summary_rows: 450
- paired_deltas_vs_nominal: 100

## Most Sensitive Parameters By Metric

| Metric | Parameter | Profile | Policy | Level | Nominal | Level value | Abs delta |
| --- | --- | --- | --- | --- | ---: | ---: | ---: |
| success_rate | force_noise_std_range | noisy_force | variable_impedance | high | 0.9333333333333332 | 0.75 | 0.18333333333333324 |
| jam_rate | contact_xy_scale | nominal | fixed_impedance | low | 0.0 | 0.0 | 0.0 |
| documented_force_jam_rate | contact_xy_scale | nominal | fixed_impedance | low | 0.0 | 0.0 | 0.0 |
| blocked_contact_termination_rate | contact_xy_scale | nominal | fixed_impedance | low | 0.0 | 0.0 | 0.0 |
| mean_final_distance | force_noise_std_range | noisy_force | variable_impedance | high | 0.0009687261678278459 | 0.001039402101685603 | 7.067593385775704e-05 |
| mean_peak_contact_force | wall_friction_range | high_friction | fixed_impedance | high | 4.410033061680831 | 5.502176716227773 | 1.0921436545469412 |
| p95_peak_contact_force | wall_friction_range | high_friction | fixed_impedance | high | 5.300233105432459 | 6.616821506652095 | 1.3165884012196365 |
| mean_contact_steps | wall_friction_range | high_friction | variable_impedance | high | 30.233333333333334 | 36.56666666666667 | 6.333333333333336 |
| mean_contact_work | wall_friction_range | high_friction | fixed_impedance | high | 0.018296049174432224 | 0.02287006146804028 | 0.004574012293608057 |

## Generated Summary Table

| Metric | Parameter | Parameter profile | Parameter delta | Profile | Profile parameter | Profile delta | VI-vs-fixed profile | VI-vs-fixed parameter | VI-vs-fixed delta |
| --- | --- | --- | ---: | --- | --- | ---: | --- | --- | ---: |
| success_rate | force_noise_std_range | noisy_force | 0.18333333333333324 | noisy_force | force_noise_std_range | -0.18333333333333324 | noisy_force | force_noise_std_range | -0.25 |
| jam_rate | contact_xy_scale | nominal | 0.0 | nominal | contact_xy_scale | 0.0 | high_friction | contact_transition_band_m | 0.0 |
| documented_force_jam_rate | contact_xy_scale | nominal | 0.0 | nominal | contact_xy_scale | 0.0 | high_friction | contact_transition_band_m | 0.0 |
| blocked_contact_termination_rate | contact_xy_scale | nominal | 0.0 | nominal | contact_xy_scale | 0.0 | high_friction | contact_transition_band_m | 0.0 |
| mean_final_distance | force_noise_std_range | noisy_force | 7.067593385775704e-05 | noisy_force | force_noise_std_range | 7.067593385775704e-05 | noisy_force | force_noise_std_range | 7.036736950220216e-05 |
| mean_peak_contact_force | wall_friction_range | high_friction | 1.0921436545469412 | high_friction | wall_friction_range | 1.0921436545469412 | high_friction | wall_friction_range | -4.010780255879497 |
| p95_peak_contact_force | wall_friction_range | high_friction | 1.3165884012196365 | high_friction | wall_friction_range | 1.3165884012196365 | high_friction | wall_friction_range | -4.85301947173681 |
| mean_contact_steps | wall_friction_range | high_friction | 6.333333333333336 | high_friction | wall_friction_range | 6.333333333333336 | noisy_force | force_noise_std_range | 34.06666666666666 |
| mean_contact_work | wall_friction_range | high_friction | 0.004574012293608057 | high_friction | wall_friction_range | 0.004574012293608057 | high_friction | wall_friction_range | -0.01821593592245126 |

## Rows

| Parameter | Level | Profile | Policy | Success | Jam | Peak force | Final distance |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| contact_xy_scale | low | nominal | fixed_impedance | 1.0 | 0.0 | 2.6532204315764396 | 0.0009690347321834007 |
| contact_xy_scale | low | nominal | variable_impedance | 1.0 | 0.0 | 0.7745358419863653 | 0.0009433850929147387 |
| contact_xy_scale | low | tight_clearance | fixed_impedance | 1.0 | 0.0 | 2.6532204315764396 | 0.0009690347321834007 |
| contact_xy_scale | low | tight_clearance | variable_impedance | 1.0 | 0.0 | 0.7745358419863653 | 0.0009433850929147387 |
| contact_xy_scale | low | high_friction | fixed_impedance | 1.0 | 0.0 | 4.410033061680831 | 0.0009690347321834007 |
| contact_xy_scale | low | high_friction | variable_impedance | 1.0 | 0.0 | 1.2159692081031162 | 0.0009439545445146299 |
| contact_xy_scale | low | offset_bias | fixed_impedance | 1.0 | 0.0 | 2.6532204315764396 | 0.0009690347321834007 |
| contact_xy_scale | low | offset_bias | variable_impedance | 1.0 | 0.0 | 0.7745358419863653 | 0.0009433850929147387 |
| contact_xy_scale | low | noisy_force | fixed_impedance | 1.0 | 0.0 | 2.784994494426659 | 0.0009690347321834007 |
| contact_xy_scale | low | noisy_force | variable_impedance | 0.9333333333333332 | 0.0 | 0.9503923418097641 | 0.0009687261678278459 |
| contact_xy_scale | nominal | nominal | fixed_impedance | 1.0 | 0.0 | 2.6532204315764396 | 0.0009690347321834007 |
| contact_xy_scale | nominal | nominal | variable_impedance | 1.0 | 0.0 | 0.7745358419863653 | 0.0009433850929147387 |
| contact_xy_scale | nominal | tight_clearance | fixed_impedance | 1.0 | 0.0 | 2.6532204315764396 | 0.0009690347321834007 |
| contact_xy_scale | nominal | tight_clearance | variable_impedance | 1.0 | 0.0 | 0.7745358419863653 | 0.0009433850929147387 |
| contact_xy_scale | nominal | high_friction | fixed_impedance | 1.0 | 0.0 | 4.410033061680831 | 0.0009690347321834007 |
| contact_xy_scale | nominal | high_friction | variable_impedance | 1.0 | 0.0 | 1.2159692081031162 | 0.0009439545445146299 |
| contact_xy_scale | nominal | offset_bias | fixed_impedance | 1.0 | 0.0 | 2.6532204315764396 | 0.0009690347321834007 |
| contact_xy_scale | nominal | offset_bias | variable_impedance | 1.0 | 0.0 | 0.7745358419863653 | 0.0009433850929147387 |
| contact_xy_scale | nominal | noisy_force | fixed_impedance | 1.0 | 0.0 | 2.784994494426659 | 0.0009690347321834007 |
| contact_xy_scale | nominal | noisy_force | variable_impedance | 0.9333333333333332 | 0.0 | 0.9503923418097641 | 0.0009687261678278459 |
| contact_xy_scale | high | nominal | fixed_impedance | 1.0 | 0.0 | 2.6532204315764396 | 0.0009690347321834007 |
| contact_xy_scale | high | nominal | variable_impedance | 1.0 | 0.0 | 0.7745358419863653 | 0.0009433850929147387 |
| contact_xy_scale | high | tight_clearance | fixed_impedance | 1.0 | 0.0 | 2.6532204315764396 | 0.0009690347321834007 |
| contact_xy_scale | high | tight_clearance | variable_impedance | 1.0 | 0.0 | 0.7745358419863653 | 0.0009433850929147387 |
| contact_xy_scale | high | high_friction | fixed_impedance | 1.0 | 0.0 | 4.410033061680831 | 0.0009690347321834007 |
| contact_xy_scale | high | high_friction | variable_impedance | 1.0 | 0.0 | 1.2159692081031162 | 0.0009439545445146299 |
| contact_xy_scale | high | offset_bias | fixed_impedance | 1.0 | 0.0 | 2.6532204315764396 | 0.0009690347321834007 |
| contact_xy_scale | high | offset_bias | variable_impedance | 1.0 | 0.0 | 0.7745358419863653 | 0.0009433850929147387 |
| contact_xy_scale | high | noisy_force | fixed_impedance | 1.0 | 0.0 | 2.784994494426659 | 0.0009690347321834007 |
| contact_xy_scale | high | noisy_force | variable_impedance | 0.9333333333333332 | 0.0 | 0.9503923418097641 | 0.0009687261678278459 |
| contact_z_scale | low | nominal | fixed_impedance | 1.0 | 0.0 | 2.6532204315764396 | 0.0009690347321834007 |
| contact_z_scale | low | nominal | variable_impedance | 1.0 | 0.0 | 0.7745358419863653 | 0.0009433850929147387 |
| contact_z_scale | low | tight_clearance | fixed_impedance | 1.0 | 0.0 | 2.6532204315764396 | 0.0009690347321834007 |
| contact_z_scale | low | tight_clearance | variable_impedance | 1.0 | 0.0 | 0.7745358419863653 | 0.0009433850929147387 |
| contact_z_scale | low | high_friction | fixed_impedance | 1.0 | 0.0 | 4.410033061680831 | 0.0009690347321834007 |
| contact_z_scale | low | high_friction | variable_impedance | 1.0 | 0.0 | 1.2159692081031162 | 0.0009439545445146299 |
| contact_z_scale | low | offset_bias | fixed_impedance | 1.0 | 0.0 | 2.6532204315764396 | 0.0009690347321834007 |
| contact_z_scale | low | offset_bias | variable_impedance | 1.0 | 0.0 | 0.7745358419863653 | 0.0009433850929147387 |
| contact_z_scale | low | noisy_force | fixed_impedance | 1.0 | 0.0 | 2.784994494426659 | 0.0009690347321834007 |
| contact_z_scale | low | noisy_force | variable_impedance | 0.9333333333333332 | 0.0 | 0.9503923418097641 | 0.0009687261678278459 |
| contact_z_scale | nominal | nominal | fixed_impedance | 1.0 | 0.0 | 2.6532204315764396 | 0.0009690347321834007 |
| contact_z_scale | nominal | nominal | variable_impedance | 1.0 | 0.0 | 0.7745358419863653 | 0.0009433850929147387 |
| contact_z_scale | nominal | tight_clearance | fixed_impedance | 1.0 | 0.0 | 2.6532204315764396 | 0.0009690347321834007 |
| contact_z_scale | nominal | tight_clearance | variable_impedance | 1.0 | 0.0 | 0.7745358419863653 | 0.0009433850929147387 |
| contact_z_scale | nominal | high_friction | fixed_impedance | 1.0 | 0.0 | 4.410033061680831 | 0.0009690347321834007 |
| contact_z_scale | nominal | high_friction | variable_impedance | 1.0 | 0.0 | 1.2159692081031162 | 0.0009439545445146299 |
| contact_z_scale | nominal | offset_bias | fixed_impedance | 1.0 | 0.0 | 2.6532204315764396 | 0.0009690347321834007 |
| contact_z_scale | nominal | offset_bias | variable_impedance | 1.0 | 0.0 | 0.7745358419863653 | 0.0009433850929147387 |
| contact_z_scale | nominal | noisy_force | fixed_impedance | 1.0 | 0.0 | 2.784994494426659 | 0.0009690347321834007 |
| contact_z_scale | nominal | noisy_force | variable_impedance | 0.9333333333333332 | 0.0 | 0.9503923418097641 | 0.0009687261678278459 |
| contact_z_scale | high | nominal | fixed_impedance | 1.0 | 0.0 | 2.6532204315764396 | 0.0009690347321834007 |
| contact_z_scale | high | nominal | variable_impedance | 1.0 | 0.0 | 0.7745358419863653 | 0.0009433850929147387 |
| contact_z_scale | high | tight_clearance | fixed_impedance | 1.0 | 0.0 | 2.6532204315764396 | 0.0009690347321834007 |
| contact_z_scale | high | tight_clearance | variable_impedance | 1.0 | 0.0 | 0.7745358419863653 | 0.0009433850929147387 |
| contact_z_scale | high | high_friction | fixed_impedance | 1.0 | 0.0 | 4.410033061680831 | 0.0009690347321834007 |
| contact_z_scale | high | high_friction | variable_impedance | 1.0 | 0.0 | 1.2159692081031162 | 0.0009439545445146299 |
| contact_z_scale | high | offset_bias | fixed_impedance | 1.0 | 0.0 | 2.6532204315764396 | 0.0009690347321834007 |
| contact_z_scale | high | offset_bias | variable_impedance | 1.0 | 0.0 | 0.7745358419863653 | 0.0009433850929147387 |
| contact_z_scale | high | noisy_force | fixed_impedance | 1.0 | 0.0 | 2.784994494426659 | 0.0009690347321834007 |
| contact_z_scale | high | noisy_force | variable_impedance | 0.9333333333333332 | 0.0 | 0.9503923418097641 | 0.0009687261678278459 |
| wall_friction_range | low | nominal | fixed_impedance | 1.0 | 0.0 | 2.00203984815647 | 0.0009690347321834007 |
| wall_friction_range | low | nominal | variable_impedance | 1.0 | 0.0 | 0.6122675709097501 | 0.0009404725410052502 |
| wall_friction_range | low | tight_clearance | fixed_impedance | 1.0 | 0.0 | 2.00203984815647 | 0.0009690347321834007 |
| wall_friction_range | low | tight_clearance | variable_impedance | 1.0 | 0.0 | 0.6122675709097501 | 0.0009404725410052502 |
| wall_friction_range | low | high_friction | fixed_impedance | 1.0 | 0.0 | 3.3180169036761566 | 0.0009690347321834007 |
| wall_friction_range | low | high_friction | variable_impedance | 1.0 | 0.0 | 0.9402139210530921 | 0.0009449344774092901 |
| wall_friction_range | low | offset_bias | fixed_impedance | 1.0 | 0.0 | 2.00203984815647 | 0.0009690347321834007 |
| wall_friction_range | low | offset_bias | variable_impedance | 1.0 | 0.0 | 0.6122675709097501 | 0.0009404725410052502 |
| wall_friction_range | low | noisy_force | fixed_impedance | 1.0 | 0.0 | 2.1298862930859337 | 0.0009690347321834007 |
| wall_friction_range | low | noisy_force | variable_impedance | 0.9499999999999998 | 0.0 | 0.7972918255205771 | 0.0009551785839100713 |
| wall_friction_range | nominal | nominal | fixed_impedance | 1.0 | 0.0 | 2.6532204315764396 | 0.0009690347321834007 |
| wall_friction_range | nominal | nominal | variable_impedance | 1.0 | 0.0 | 0.7745358419863653 | 0.0009433850929147387 |
| wall_friction_range | nominal | tight_clearance | fixed_impedance | 1.0 | 0.0 | 2.6532204315764396 | 0.0009690347321834007 |
| wall_friction_range | nominal | tight_clearance | variable_impedance | 1.0 | 0.0 | 0.7745358419863653 | 0.0009433850929147387 |
| wall_friction_range | nominal | high_friction | fixed_impedance | 1.0 | 0.0 | 4.410033061680831 | 0.0009690347321834007 |
| wall_friction_range | nominal | high_friction | variable_impedance | 1.0 | 0.0 | 1.2159692081031162 | 0.0009439545445146299 |
| wall_friction_range | nominal | offset_bias | fixed_impedance | 1.0 | 0.0 | 2.6532204315764396 | 0.0009690347321834007 |
| wall_friction_range | nominal | offset_bias | variable_impedance | 1.0 | 0.0 | 0.7745358419863653 | 0.0009433850929147387 |
| wall_friction_range | nominal | noisy_force | fixed_impedance | 1.0 | 0.0 | 2.784994494426659 | 0.0009690347321834007 |
| wall_friction_range | nominal | noisy_force | variable_impedance | 0.9333333333333332 | 0.0 | 0.9503923418097641 | 0.0009687261678278459 |
| wall_friction_range | high | nominal | fixed_impedance | 1.0 | 0.0 | 3.30466043731251 | 0.0009690347321834007 |
| wall_friction_range | high | nominal | variable_impedance | 1.0 | 0.0 | 0.9380790378964464 | 0.000935483090580004 |
| wall_friction_range | high | tight_clearance | fixed_impedance | 1.0 | 0.0 | 3.30466043731251 | 0.0009690347321834007 |
| wall_friction_range | high | tight_clearance | variable_impedance | 1.0 | 0.0 | 0.9380790378964464 | 0.000935483090580004 |
| wall_friction_range | high | high_friction | fixed_impedance | 1.0 | 0.0 | 5.502176716227773 | 0.0009690347321834007 |
| wall_friction_range | high | high_friction | variable_impedance | 1.0 | 0.0 | 1.491396460348276 | 0.0009371922063331107 |
| wall_friction_range | high | offset_bias | fixed_impedance | 1.0 | 0.0 | 3.30466043731251 | 0.0009690347321834007 |
| wall_friction_range | high | offset_bias | variable_impedance | 1.0 | 0.0 | 0.9380790378964464 | 0.000935483090580004 |
| wall_friction_range | high | noisy_force | fixed_impedance | 1.0 | 0.0 | 3.4465568862140876 | 0.0009690347321834007 |
| wall_friction_range | high | noisy_force | variable_impedance | 0.9333333333333332 | 0.0 | 1.1152111367267359 | 0.0009726729263861983 |
| force_noise_std_range | low | nominal | fixed_impedance | 1.0 | 0.0 | 2.641379990327517 | 0.0009690347321834007 |
| force_noise_std_range | low | nominal | variable_impedance | 1.0 | 0.0 | 0.7486976100272861 | 0.0009483681122471032 |
| force_noise_std_range | low | tight_clearance | fixed_impedance | 1.0 | 0.0 | 2.641379990327517 | 0.0009690347321834007 |
| force_noise_std_range | low | tight_clearance | variable_impedance | 1.0 | 0.0 | 0.7486976100272861 | 0.0009483681122471032 |
| force_noise_std_range | low | high_friction | fixed_impedance | 1.0 | 0.0 | 4.399680477661384 | 0.0009690347321834007 |
| force_noise_std_range | low | high_friction | variable_impedance | 1.0 | 0.0 | 1.1915590599263022 | 0.000938923676063982 |
| force_noise_std_range | low | offset_bias | fixed_impedance | 1.0 | 0.0 | 2.641379990327517 | 0.0009690347321834007 |
| force_noise_std_range | low | offset_bias | variable_impedance | 1.0 | 0.0 | 0.7486976100272861 | 0.0009483681122471032 |
| force_noise_std_range | low | noisy_force | fixed_impedance | 1.0 | 0.0 | 2.7507801745685927 | 0.0009690347321834007 |
| force_noise_std_range | low | noisy_force | variable_impedance | 1.0 | 0.0 | 0.8956134374221181 | 0.0009341889890531882 |
| force_noise_std_range | nominal | nominal | fixed_impedance | 1.0 | 0.0 | 2.6532204315764396 | 0.0009690347321834007 |
| force_noise_std_range | nominal | nominal | variable_impedance | 1.0 | 0.0 | 0.7745358419863653 | 0.0009433850929147387 |
| force_noise_std_range | nominal | tight_clearance | fixed_impedance | 1.0 | 0.0 | 2.6532204315764396 | 0.0009690347321834007 |
| force_noise_std_range | nominal | tight_clearance | variable_impedance | 1.0 | 0.0 | 0.7745358419863653 | 0.0009433850929147387 |
| force_noise_std_range | nominal | high_friction | fixed_impedance | 1.0 | 0.0 | 4.410033061680831 | 0.0009690347321834007 |
| force_noise_std_range | nominal | high_friction | variable_impedance | 1.0 | 0.0 | 1.2159692081031162 | 0.0009439545445146299 |
| force_noise_std_range | nominal | offset_bias | fixed_impedance | 1.0 | 0.0 | 2.6532204315764396 | 0.0009690347321834007 |
| force_noise_std_range | nominal | offset_bias | variable_impedance | 1.0 | 0.0 | 0.7745358419863653 | 0.0009433850929147387 |
| force_noise_std_range | nominal | noisy_force | fixed_impedance | 1.0 | 0.0 | 2.784994494426659 | 0.0009690347321834007 |
| force_noise_std_range | nominal | noisy_force | variable_impedance | 0.9333333333333332 | 0.0 | 0.9503923418097641 | 0.0009687261678278459 |
| force_noise_std_range | high | nominal | fixed_impedance | 1.0 | 0.0 | 2.665304853667829 | 0.0009690347321834007 |
| force_noise_std_range | high | nominal | variable_impedance | 1.0 | 0.0 | 0.7980815064505936 | 0.0009448187371099842 |
| force_noise_std_range | high | tight_clearance | fixed_impedance | 1.0 | 0.0 | 2.665304853667829 | 0.0009690347321834007 |
| force_noise_std_range | high | tight_clearance | variable_impedance | 1.0 | 0.0 | 0.7980815064505936 | 0.0009448187371099842 |
| force_noise_std_range | high | high_friction | fixed_impedance | 1.0 | 0.0 | 4.420505342356935 | 0.0009690347321834007 |
| force_noise_std_range | high | high_friction | variable_impedance | 1.0 | 0.0 | 1.2352473767091554 | 0.0009394065794846776 |
| force_noise_std_range | high | offset_bias | fixed_impedance | 1.0 | 0.0 | 2.665304853667829 | 0.0009690347321834007 |
| force_noise_std_range | high | offset_bias | variable_impedance | 1.0 | 0.0 | 0.7980815064505936 | 0.0009448187371099842 |
| force_noise_std_range | high | noisy_force | fixed_impedance | 1.0 | 0.0 | 2.8257442261407477 | 0.0009690347321834007 |
| force_noise_std_range | high | noisy_force | variable_impedance | 0.75 | 0.0 | 1.0325921541390886 | 0.001039402101685603 |
| contact_transition_band_m | low | nominal | fixed_impedance | 1.0 | 0.0 | 2.6532204315764396 | 0.0009690347321834007 |
| contact_transition_band_m | low | nominal | variable_impedance | 1.0 | 0.0 | 0.7745358419863653 | 0.0009433850929147387 |
| contact_transition_band_m | low | tight_clearance | fixed_impedance | 1.0 | 0.0 | 2.6532204315764396 | 0.0009690347321834007 |
| contact_transition_band_m | low | tight_clearance | variable_impedance | 1.0 | 0.0 | 0.7745358419863653 | 0.0009433850929147387 |
| contact_transition_band_m | low | high_friction | fixed_impedance | 1.0 | 0.0 | 4.410033061680831 | 0.0009690347321834007 |
| contact_transition_band_m | low | high_friction | variable_impedance | 1.0 | 0.0 | 1.2159692081031162 | 0.0009439545445146299 |
| contact_transition_band_m | low | offset_bias | fixed_impedance | 1.0 | 0.0 | 2.6532204315764396 | 0.0009690347321834007 |
| contact_transition_band_m | low | offset_bias | variable_impedance | 1.0 | 0.0 | 0.7745358419863653 | 0.0009433850929147387 |
| contact_transition_band_m | low | noisy_force | fixed_impedance | 1.0 | 0.0 | 2.784994494426659 | 0.0009690347321834007 |
| contact_transition_band_m | low | noisy_force | variable_impedance | 0.9333333333333332 | 0.0 | 0.9503923418097641 | 0.0009687261678278459 |
| contact_transition_band_m | nominal | nominal | fixed_impedance | 1.0 | 0.0 | 2.6532204315764396 | 0.0009690347321834007 |
| contact_transition_band_m | nominal | nominal | variable_impedance | 1.0 | 0.0 | 0.7745358419863653 | 0.0009433850929147387 |
| contact_transition_band_m | nominal | tight_clearance | fixed_impedance | 1.0 | 0.0 | 2.6532204315764396 | 0.0009690347321834007 |
| contact_transition_band_m | nominal | tight_clearance | variable_impedance | 1.0 | 0.0 | 0.7745358419863653 | 0.0009433850929147387 |
| contact_transition_band_m | nominal | high_friction | fixed_impedance | 1.0 | 0.0 | 4.410033061680831 | 0.0009690347321834007 |
| contact_transition_band_m | nominal | high_friction | variable_impedance | 1.0 | 0.0 | 1.2159692081031162 | 0.0009439545445146299 |
| contact_transition_band_m | nominal | offset_bias | fixed_impedance | 1.0 | 0.0 | 2.6532204315764396 | 0.0009690347321834007 |
| contact_transition_band_m | nominal | offset_bias | variable_impedance | 1.0 | 0.0 | 0.7745358419863653 | 0.0009433850929147387 |
| contact_transition_band_m | nominal | noisy_force | fixed_impedance | 1.0 | 0.0 | 2.784994494426659 | 0.0009690347321834007 |
| contact_transition_band_m | nominal | noisy_force | variable_impedance | 0.9333333333333332 | 0.0 | 0.9503923418097641 | 0.0009687261678278459 |
| contact_transition_band_m | high | nominal | fixed_impedance | 1.0 | 0.0 | 2.6532204315764396 | 0.0009690347321834007 |
| contact_transition_band_m | high | nominal | variable_impedance | 1.0 | 0.0 | 0.7745358419863653 | 0.0009433850929147387 |
| contact_transition_band_m | high | tight_clearance | fixed_impedance | 1.0 | 0.0 | 2.6532204315764396 | 0.0009690347321834007 |
| contact_transition_band_m | high | tight_clearance | variable_impedance | 1.0 | 0.0 | 0.7745358419863653 | 0.0009433850929147387 |
| contact_transition_band_m | high | high_friction | fixed_impedance | 1.0 | 0.0 | 4.410033061680831 | 0.0009690347321834007 |
| contact_transition_band_m | high | high_friction | variable_impedance | 1.0 | 0.0 | 1.2159692081031162 | 0.0009439545445146299 |
| contact_transition_band_m | high | offset_bias | fixed_impedance | 1.0 | 0.0 | 2.6532204315764396 | 0.0009690347321834007 |
| contact_transition_band_m | high | offset_bias | variable_impedance | 1.0 | 0.0 | 0.7745358419863653 | 0.0009433850929147387 |
| contact_transition_band_m | high | noisy_force | fixed_impedance | 1.0 | 0.0 | 2.784994494426659 | 0.0009690347321834007 |
| contact_transition_band_m | high | noisy_force | variable_impedance | 0.9333333333333332 | 0.0 | 0.9503923418097641 | 0.0009687261678278459 |
