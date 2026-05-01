# 3DoF Alternative Contact-Model Cross-Check

- claim_scope: within-A fallback contact-law cross-check; not a second-simulator or hardware-validity claim
- contact_models: within_a_base_contact_law, within_a_soft_wall_contact_cross_check
- changed_fields: contact_xy_scale, contact_z_scale, in_hole_drag_scale, contact_transition_band_m

## Rows

| Contact model | Profile | Policy | Success | Jam | Peak force | Final distance | Contact steps | Contact work |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| within_a_base_contact_law | nominal | fixed_impedance | 1.0 | 0.0 | 1.9679313389014121 | 0.0009690347321834005 | 11.0 | 0.008006676601477086 |
| within_a_soft_wall_contact_cross_check | nominal | fixed_impedance | 1.0 | 0.0 | 2.1587948162452486 | 0.0009690347321834005 | 11.0 | 0.008807344261624793 |
| within_a_base_contact_law | nominal | variable_impedance | 1.0 | 0.0 | 0.5992486759366799 | 0.0009603550036752709 | 27.666666666666668 | 0.0020324459065739625 |
| within_a_soft_wall_contact_cross_check | nominal | variable_impedance | 1.0 | 0.0 | 0.6470506278837823 | 0.0009603550036752709 | 27.333333333333332 | 0.0022356904972313588 |
| within_a_base_contact_law | tight_clearance | fixed_impedance | 1.0 | 0.0 | 1.9679313389014121 | 0.0009690347321834005 | 11.0 | 0.008006676601477086 |
| within_a_soft_wall_contact_cross_check | tight_clearance | fixed_impedance | 1.0 | 0.0 | 2.1587948162452486 | 0.0009690347321834005 | 11.0 | 0.008807344261624793 |
| within_a_base_contact_law | tight_clearance | variable_impedance | 1.0 | 0.0 | 0.5992486759366799 | 0.0009603550036752709 | 27.666666666666668 | 0.0020324459065739625 |
| within_a_soft_wall_contact_cross_check | tight_clearance | variable_impedance | 1.0 | 0.0 | 0.6470506278837823 | 0.0009603550036752709 | 27.333333333333332 | 0.0022356904972313588 |
| within_a_base_contact_law | high_friction | fixed_impedance | 1.0 | 0.0 | 3.7901227987738495 | 0.0009690347321834005 | 11.0 | 0.01567586851884786 |
| within_a_soft_wall_contact_cross_check | high_friction | fixed_impedance | 1.0 | 0.0 | 4.164353681492483 | 0.0009690347321834005 | 11.0 | 0.017243455370732644 |
| within_a_base_contact_law | high_friction | variable_impedance | 1.0 | 0.0 | 1.0321016148673807 | 0.0009449074814718108 | 28.666666666666668 | 0.0038745874211428793 |
| within_a_soft_wall_contact_cross_check | high_friction | variable_impedance | 1.0 | 0.0 | 1.1082349681879913 | 0.0009703858743111827 | 29.666666666666668 | 0.004152017969593672 |
| within_a_base_contact_law | offset_bias | fixed_impedance | 1.0 | 0.0 | 1.9679313389014121 | 0.0009690347321834005 | 11.0 | 0.008006676601477086 |
| within_a_soft_wall_contact_cross_check | offset_bias | fixed_impedance | 1.0 | 0.0 | 2.1587948162452486 | 0.0009690347321834005 | 11.0 | 0.008807344261624793 |
| within_a_base_contact_law | offset_bias | variable_impedance | 1.0 | 0.0 | 0.5992486759366799 | 0.0009603550036752709 | 27.666666666666668 | 0.0020324459065739625 |
| within_a_soft_wall_contact_cross_check | offset_bias | variable_impedance | 1.0 | 0.0 | 0.6470506278837823 | 0.0009603550036752709 | 27.333333333333332 | 0.0022356904972313588 |
| within_a_base_contact_law | noisy_force | fixed_impedance | 1.0 | 0.0 | 2.2769172161004247 | 0.0009690347321834005 | 11.0 | 0.008959609629311934 |
| within_a_soft_wall_contact_cross_check | noisy_force | fixed_impedance | 1.0 | 0.0 | 2.489345531842756 | 0.0009690347321834005 | 11.0 | 0.009855570592243129 |
| within_a_base_contact_law | noisy_force | variable_impedance | 1.0 | 0.0 | 0.8537779309022068 | 0.0009529167562723154 | 44.333333333333336 | 0.0015189647022796455 |
| within_a_soft_wall_contact_cross_check | noisy_force | variable_impedance | 1.0 | 0.0 | 0.906558382239974 | 0.0009529167562723154 | 44.333333333333336 | 0.0016708611725076105 |

## Paired Deltas

| Profile | Policy | Success delta | Jam delta | Peak-force delta | Final-distance delta |
| --- | --- | ---: | ---: | ---: | ---: |
| high_friction | fixed_impedance | 0.0 | 0.0 | 0.3742308827186336 | 0.0 |
| high_friction | variable_impedance | 0.0 | 0.0 | 0.07613335332061055 | 2.547839283937193e-05 |
| noisy_force | fixed_impedance | 0.0 | 0.0 | 0.21242831574233145 | 0.0 |
| noisy_force | variable_impedance | 0.0 | 0.0 | 0.05278045133776721 | 0.0 |
| nominal | fixed_impedance | 0.0 | 0.0 | 0.19086347734383646 | 0.0 |
| nominal | variable_impedance | 0.0 | 0.0 | 0.04780195194710246 | 0.0 |
| offset_bias | fixed_impedance | 0.0 | 0.0 | 0.19086347734383646 | 0.0 |
| offset_bias | variable_impedance | 0.0 | 0.0 | 0.04780195194710246 | 0.0 |
| tight_clearance | fixed_impedance | 0.0 | 0.0 | 0.19086347734383646 | 0.0 |
| tight_clearance | variable_impedance | 0.0 | 0.0 | 0.04780195194710246 | 0.0 |
