from vi_full.three_dof_config import ThreeDoFResetConfig
from vi_full.three_dof_training import (
    ThreeDoFDemoDataset,
    ThreeDoFPPOTrainConfig,
    _build_3dof_demo_dataset_metadata,
    _build_3dof_training_summary,
    serialize_3dof_train_config,
)
from vi_full.three_dof_policies import resolve_3dof_teacher_spec


def test_serialize_3dof_train_config_includes_resolved_teacher_spec() -> None:
    spec = resolve_3dof_teacher_spec(policy_name="variable_impedance")
    config = ThreeDoFPPOTrainConfig(
        bc_demo_policy_name="fixed_impedance",
        bc_demo_teacher_spec=spec,
    )

    serialized = serialize_3dof_train_config(config)

    assert serialized["bc_demo_policy_name"] == "fixed_impedance"
    assert serialized["bc_demo_teacher_spec"]["preset_name"] == "teacher_variable_variable"
    assert (
        serialized["bc_demo_teacher_spec"]["motion_rule"]
        == "contact_aware_variable_motion"
    )


def test_demo_dataset_metadata_hash_changes_when_teacher_spec_changes() -> None:
    variable_config = ThreeDoFPPOTrainConfig(
        bc_demo_teacher_spec=resolve_3dof_teacher_spec(policy_name="variable_impedance")
    )
    fixed_config = ThreeDoFPPOTrainConfig(
        bc_demo_teacher_spec=resolve_3dof_teacher_spec(policy_name="fixed_impedance")
    )

    variable_metadata = _build_3dof_demo_dataset_metadata(
        variable_config,
        reset_config=ThreeDoFResetConfig(),
    )
    fixed_metadata = _build_3dof_demo_dataset_metadata(
        fixed_config,
        reset_config=ThreeDoFResetConfig(),
    )

    assert variable_metadata["dataset_hash"] != fixed_metadata["dataset_hash"]


def test_demo_dataset_metadata_includes_teacher_metadata() -> None:
    config = ThreeDoFPPOTrainConfig(
        bc_demo_policy_name="fixed_impedance",
        bc_demo_teacher_spec=resolve_3dof_teacher_spec(policy_name="teacher_pose_variable"),
    )

    metadata = _build_3dof_demo_dataset_metadata(
        config,
        reset_config=ThreeDoFResetConfig(),
    )

    assert metadata["bc_demo_policy_name"] == "fixed_impedance"
    assert metadata["teacher_preset_name"] == "teacher_pose_variable"
    assert metadata["teacher_motion_rule"] == "pose_feedback"
    assert metadata["teacher_impedance_rule"] == "contact_aware_variable_impedance"
    assert metadata["bc_demo_teacher_spec"]["preset_name"] == "teacher_pose_variable"


def test_training_summary_includes_teacher_metadata() -> None:
    config = ThreeDoFPPOTrainConfig(
        bc_demo_teacher_spec=resolve_3dof_teacher_spec(policy_name="fixed_impedance")
    )
    demo_dataset = ThreeDoFDemoDataset(
        observations=[],
        actions=[],
        dataset_id="demo",
        dataset_path="generated://demo",
        dataset_hash="123456789abc",
    )

    summary = _build_3dof_training_summary(
        config=config,
        demo_dataset=demo_dataset,
    )

    assert summary["teacher_preset_name"] == "teacher_pose_fixed"
    assert summary["teacher_motion_rule"] == "pose_feedback"
    assert summary["teacher_impedance_rule"] == "fixed"
