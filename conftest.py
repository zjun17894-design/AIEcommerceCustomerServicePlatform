import pytest
import os
import sys
from unittest.mock import MagicMock, patch
from datetime import datetime

# 确保 src 目录在 Python 路径中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from home_agent.models import SceneDescription, ServiceAction, UserFeedback, DeviceCommand


@pytest.fixture
def sample_scene():
    """创建标准测试场景"""
    return SceneDescription(
        timestamp=datetime.now(),
        user_id="test_user",
        location="living_room",
        time_context="evening",
        activity="watching_tv",
        environmental={"temperature": 24.0, "humidity": 50.0},
        raw_sensors=["ac_living", "light_living", "tv_living"],
    )


@pytest.fixture
def sample_action():
    """创建标准测试动作"""
    return ServiceAction(
        action_type="adjust_temp",
        device_id="ac_living",
        command=DeviceCommand.SET_TEMPERATURE,
        params={"temperature": 23},
        priority=3,
        reason="Test action",
        requires_confirmation=True,
    )


@pytest.fixture
def sample_feedback(sample_scene, sample_action):
    """创建标准测试反馈"""
    return UserFeedback(
        user_id="test_user",
        action_id="test_action_1",
        accepted=True,
        timestamp=datetime.now(),
        associated_scene=sample_scene,
        associated_action=sample_action,
    )


def _make_mock_milvus_client():
    """创建 Milvus 客户端 mock"""
    client = MagicMock()
    client.has_collection = MagicMock(return_value=True)
    client.insert = MagicMock(return_value={"insert_count": 1})
    client.query = MagicMock(return_value=[])
    client.search = MagicMock(return_value=[])
    client.load_collection = MagicMock()
    client.create_collection = MagicMock()
    client.prepare_index_params = MagicMock(return_value=MagicMock())
    return client


@pytest.fixture
def mock_milvus_client():
    """Milvus 客户端 mock fixture"""
    return _make_mock_milvus_client()


@pytest.fixture
def mock_memory(mock_milvus_client):
    """完整 mock 的 AgentMemory，跳过真实 Milvus 连接"""
    with patch("home_agent.core.memory.MilvusClient", return_value=mock_milvus_client):
        from home_agent.core.memory import AgentMemory
        mem = AgentMemory()
        mem.client = mock_milvus_client
        with patch.object(mem, '_embed', return_value=[0.1] * 1024):
            yield mem


@pytest.fixture
def mock_dashscope_response():
    """DashScope API 固定 mock 响应"""
    return {
        "choices": [
            {
                "message": {
                    "content": '{"should_act": true, "action_type": "adjust_temp", "device": "ac_living", "params": {"temperature": 23}, "priority": 3, "reason": "User pattern match", "requires_confirmation": true}'
                }
            }
        ]
    }
