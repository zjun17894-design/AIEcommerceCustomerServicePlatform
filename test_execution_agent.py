from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from home_agent.agents.execution import ExecutionAgent
from home_agent.models import ServiceAction, DeviceCommand


def _make_action(requires_confirmation=True):
    return ServiceAction(
        action_type="adjust_temp",
        device_id="ac_living",
        command=DeviceCommand.SET_TEMPERATURE,
        params={"temperature": 23},
        requires_confirmation=requires_confirmation,
        reason="test",
    )


def test_execute_requires_confirmation_stores_pending():
    """需要确认的 action 暂存到 pending_confirmations"""
    iot_ctrl = MagicMock()
    agent = ExecutionAgent(iot_ctrl)

    action = _make_action(requires_confirmation=True)
    agent.execute(action, "test_user")

    assert len(agent.pending_confirmations) == 1
    iot_ctrl.execute_action.assert_not_called()


def test_execute_no_confirm_executes_immediately():
    """不需要确认的 action 直接执行"""
    iot_ctrl = MagicMock()
    iot_ctrl.execute_action.return_value = True
    agent = ExecutionAgent(iot_ctrl)

    action = _make_action(requires_confirmation=False)
    result = agent.execute(action, "test_user")

    assert result is True
    iot_ctrl.execute_action.assert_called_once()


def test_confirm_action_accepted():
    """用户确认接受 action"""
    iot_ctrl = MagicMock()
    iot_ctrl.execute_action.return_value = True
    feedback_handler = MagicMock()
    agent = ExecutionAgent(iot_ctrl)
    agent.set_feedback_handler(feedback_handler)

    action = _make_action()
    agent.execute(action, "test_user")
    action_id = next(iter(agent.pending_confirmations))

    agent.confirm_action(action_id, True)

    assert len(agent.pending_confirmations) == 0
    iot_ctrl.execute_action.assert_called()
    feedback_handler.collect_feedback.assert_called()


def test_confirm_action_rejected():
    """用户拒绝 action"""
    iot_ctrl = MagicMock()
    feedback_handler = MagicMock()
    agent = ExecutionAgent(iot_ctrl)
    agent.set_feedback_handler(feedback_handler)

    action = _make_action()
    agent.execute(action, "test_user")
    action_id = next(iter(agent.pending_confirmations))

    agent.confirm_action(action_id, False)

    assert len(agent.pending_confirmations) == 0
    iot_ctrl.execute_action.assert_not_called()
    feedback_handler.collect_feedback.assert_called()
    assert feedback_handler.collect_feedback.call_args[0][0].accepted is False


def test_cleanup_expired_confirmations():
    """清理超时未确认的 actions"""
    iot_ctrl = MagicMock()
    agent = ExecutionAgent(iot_ctrl)

    action = _make_action()
    agent.execute(action, "test_user")
    assert len(agent.pending_confirmations) == 1

    # 修改 sent_at 为 20 分钟前
    for key in agent.pending_confirmations:
        agent.pending_confirmations[key]["sent_at"] = datetime.now() - timedelta(seconds=1000)

    agent.cleanup_expired_confirmations(timeout_seconds=900)
    assert len(agent.pending_confirmations) == 0
