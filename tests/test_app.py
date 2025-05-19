import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_happy_path():
    response = client.post("/api/v1/execute", json={
        "request": "My application crashes after login. Please help resolve it.",
        "require_approval": False
    })
    assert response.status_code == 200
    data = response.json()
    assert "diagnosis" in data
    assert "script" in data
    assert "email_draft" in data
    assert data["status"] == "completed"

def test_approval_flow():
    res = client.post("/api/v1/execute", json={
        "request": "My PC overheats frequently after updates.",
        "require_approval": True
    })
    assert res.status_code == 200
    task_id = res.json()["task_id"]

    approve = client.post(f"/api/v1/plans/{task_id}/approve")
    assert approve.status_code == 200
    result = approve.json()
    assert result["status"] == "completed"
    assert "result" in result
    assert isinstance(result["result"], list)

def test_rejection_flow():
    res = client.post("/api/v1/execute", json={
        "request": "Diagnose why my internet is slow.",
        "require_approval": True
    })
    assert res.status_code == 200
    task_id = res.json()["task_id"]

    reject = client.post(f"/api/v1/plans/{task_id}/reject")
    assert reject.status_code == 200
    assert reject.json()["status"] == "rejected"

def test_script_compiles():
    res = client.post("/api/v1/execute", json={
        "request": "Give me a PowerShell script to clean up temp files",
        "require_approval": False
    })
    assert res.status_code == 200
    script = res.json().get("script", {})
    assert script.get("lint_passed", False) is True
    assert "Remove-Item" in script.get("code", "")

def test_step_planning_without_diagnosis():
    res = client.post("/api/v1/execute", json={
        "request": "Provide a PowerShell script to disable startup apps. I don't need a diagnosis.",
        "require_approval": False
    })
    assert res.status_code == 200
    data = res.json()
    assert "diagnosis" not in data
    assert "script" in data
    assert "email_draft" in data

def test_agent_retry(monkeypatch):
    from agents.automation import AutomationAgent
    from fastapi.testclient import TestClient
    from main import app

    client = TestClient(app)
    attempts = {"count": 0}

    def flaky_run(self, request):  # Fix here
        attempts["count"] += 1
        if attempts["count"] < 2:
            raise RuntimeError("Simulated failure")
        return {
            "language": "powershell",
            "code": "Write-Host 'Recovered on retry'",
            "lint_passed": True
        }

    monkeypatch.setattr(AutomationAgent, "run", flaky_run)

    response = client.post("/api/v1/execute", json={
        "request": "Give me a PowerShell script to restart network services",
        "require_approval": False
    })

    assert response.status_code == 200
    data = response.json()
    assert "script" in data
    assert data["script"]["code"] == "Write-Host 'Recovered on retry'"
    assert attempts["count"] >= 2  # confirms it retried
