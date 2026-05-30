from home_agent.agents.conflict import ConflictArbitrationAgent
from home_agent.models import ServiceAction, DeviceCommand


def _make_temp_action(device_id, temperature):
    return ServiceAction(
        action_type="adjust_temp",
        device_id=device_id,
        command=DeviceCommand.SET_TEMPERATURE,
        params={"temperature": temperature},
        reason="test",
    )


def test_single_user_no_arbitration():
    """单用户不仲裁，返回原动作"""
    agent = ConflictArbitrationAgent()
    agent.register_user_presence("user1", "living_room")
    actions = [_make_temp_action("ac_living", 24)]

    result = agent.arbitrate(actions, {})
    assert len(result) == 1
    assert result[0].params["temperature"] == 24


def test_multi_user_average_arbitration():
    """多用户取平均值仲裁"""
    from home_agent.config import config
    original_mode = config.CONFLICT_MODE
    config.CONFLICT_MODE = "average"

    try:
        agent = ConflictArbitrationAgent()
        agent.register_user_presence("user1", "living_room")
        agent.register_user_presence("user2", "living_room")
        actions = [
            _make_temp_action("ac_living", 22),
            _make_temp_action("ac_living", 26),
        ]

        result = agent.arbitrate(actions, {})
        assert len(result) == 1
        assert result[0].params["temperature"] == 24  # (22 + 26) / 2
    finally:
        config.CONFLICT_MODE = original_mode


def test_no_conflict_different_devices():
    """不同设备无冲突，全部返回"""
    agent = ConflictArbitrationAgent()
    agent.register_user_presence("user1", "living_room")
    agent.register_user_presence("user2", "bedroom")
    actions = [
        _make_temp_action("ac_living", 22),
        _make_temp_action("ac_bedroom", 26),
    ]

    result = agent.arbitrate(actions, {})
    assert len(result) == 2
