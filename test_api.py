"""FastAPI 端点集成测试"""

import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient


@pytest.fixture
def test_orchestrator():
    """创建 mock orchestrator"""
    orch = MagicMock()
    orch.user_id = "test_user"
    orch.iot_ctrl = MagicMock()
    orch.memory = MagicMock()

    # mock run_inference 返回
    from home_agent.models import (
        CycleResult, SceneDescription, ServiceAction, DeviceCommand,
    )
    from datetime import datetime

    from home_agent.models import TokenUsage

    orch.run_inference.return_value = CycleResult(
        cycle_id="test001",
        timestamp=datetime.now(),
        user_id="test_user",
        scene=SceneDescription(
            timestamp=datetime.now(),
            user_id="test_user",
            location="living_room",
            time_context="evening",
            activity="watching_tv",
            environmental={"temperature": 24.0},
        ),
        suggested_action=ServiceAction(
            action_type="adjust_temp",
            device_id="ac_living",
            command=DeviceCommand.SET_TEMPERATURE,
            params={"temperature": 23},
            reason="User prefers 23°C at evening",
        ),
        executed=True,
        token_usage=TokenUsage(prompt_tokens=150, completion_tokens=80, total_tokens=230),
        latency_ms=320.5,
    )

    orch.get_stats.return_value = {
        "user_id": "test_user",
        "total_cycles": 50,
        "accepted": 40,
        "rejected": 8,
        "acceptance_rate": 80.0,
    }

    orch.iot_ctrl.get_all_states.return_value = {}
    orch.iot_ctrl.get_device_state.return_value = None
    orch.memory.get_recent_actions_with_feedback.return_value = []
    orch.memory.client.query.return_value = []
    return orch


@pytest.fixture
def client(test_orchestrator):
    """创建 TestClient，注入 mock orchestrator"""
    import home_agent.api as api_mod
    api_mod._orchestrator = test_orchestrator
    return TestClient(api_mod.app)


class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data


class TestInferenceEndpoint:
    def test_inference_returns_200(self, client):
        response = client.post(
            "/api/v1/inference",
            json={"user_id": "test_user", "location": "living_room"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["cycle_id"] == "test001"
        assert data["executed"] is True
        assert data["scene"]["time_context"] == "evening"
        assert data["suggested_action"]["action_type"] == "adjust_temp"
        assert data["token_usage"]["total_tokens"] == 230
        assert data["latency_ms"] == 320.5


class TestDevicesEndpoint:
    def test_list_devices_returns_200(self, client):
        response = client.get("/api/v1/devices")
        assert response.status_code == 200


class TestStatsEndpoint:
    def test_stats_returns_200(self, client):
        response = client.get("/api/v1/stats", params={"user_id": "test_user"})
        assert response.status_code == 200
        data = response.json()
        assert data["acceptance_rate"] == 80.0


class TestHistoryEndpoint:
    def test_history_returns_200(self, client):
        response = client.get("/api/v1/history", params={"user_id": "test_user"})
        assert response.status_code == 200


class TestOrchestrator503:
    def test_returns_503_when_orchestrator_is_none(self):
        import home_agent.api as api_mod
        api_mod._orchestrator = None
        client = TestClient(api_mod.app)
        response = client.get("/api/health")
        assert response.status_code == 503
