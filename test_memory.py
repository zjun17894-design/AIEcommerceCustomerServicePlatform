import pytest
from unittest.mock import patch
from datetime import datetime
from home_agent.core.memory import AgentMemory
from home_agent.models import SceneDescription, ServiceAction, UserFeedback, DeviceCommand


def test_store_user_behavior_inserts(mock_memory, mock_milvus_client, sample_scene):
    """store_user_behavior() 插入成功"""
    mock_memory.store_user_behavior("test_user", sample_scene)
    assert mock_milvus_client.insert.called


def test_get_recent_actions_with_feedback(mock_memory, mock_milvus_client, sample_action):
    """get_recent_actions_with_feedback() 返回 action + feedback_accepted"""
    mock_milvus_client.query.return_value = [
        {
            "scene_json": {
                "action_taken": sample_action.__dict__,
                "feedback": {"accepted": True},
            }
        }
    ]

    results = mock_memory.get_recent_actions_with_feedback("test_user", limit=10)

    assert len(results) == 1
    assert results[0]["action"] is not None
    assert results[0]["feedback_accepted"] is True


def test_get_recent_actions_with_feedback_rejected(mock_memory, mock_milvus_client, sample_action):
    """返回 rejected 状态的反馈"""
    mock_milvus_client.query.return_value = [
        {
            "scene_json": {
                "action_taken": sample_action.__dict__,
                "feedback": {"accepted": False},
            }
        }
    ]

    results = mock_memory.get_recent_actions_with_feedback("test_user", limit=10)

    assert results[0]["feedback_accepted"] is False


def test_get_recent_actions_with_feedback_no_feedback(mock_memory, mock_milvus_client, sample_action):
    """返回无反馈状态的 action"""
    mock_milvus_client.query.return_value = [
        {
            "scene_json": {
                "action_taken": sample_action.__dict__,
                "feedback": None,
            }
        }
    ]

    results = mock_memory.get_recent_actions_with_feedback("test_user", limit=10)

    assert results[0]["feedback_accepted"] is None
