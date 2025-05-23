from fastapi import APIRouter, Path
from uuid import uuid4
from datetime import datetime
import time

from models.task import TaskRequest
from models.status import TaskStatus
from agents.router import DSPyRouter
from agents.coordinator import DSPyExecutor
from agents.automation import AutomationAgent
from agents.diagnostic import DiagnosticAgent
from agents.writer import WriterAgent

router = APIRouter()
router_module = DSPyRouter()  # Step planner

# DSPy agent executor (used in /approve)
agents = {
    "Generate script": AutomationAgent(),
    "Run diagnosis": DiagnosticAgent(),
    "Write email": WriterAgent()
}
executor = DSPyExecutor(agents)

# In-memory DBs
approved_db = {}
pending_db = {}
rejected_db = {}

# /execute - Step Planning + Store Plan
@router.post("/api/v1/execute")
def execute_task(task: TaskRequest):
    task_id = f"plan-{uuid4()}" if task.require_approval else str(uuid4())
    created_at = datetime.utcnow().isoformat()

    if task.require_approval:
        steps = router_module(request=task.request)
        print("🔥 DSPy Planned Steps:", steps)

        plan = {
            "task_id": task_id,
            "status": TaskStatus.PENDING,
            "original_request": task.request,
            "created_at": created_at,
            "plan": {
                "steps": steps,
                "summary": "Plan dynamically generated by DSPy based on the request"
            }
        }

        pending_db[task_id] = plan
        return plan

    # ✅ Direct execution (if no approval needed) using LangGraph
    from graph import graph
    start_time = time.time()
    result = graph.invoke({"request": task.request})
    duration = round(time.time() - start_time, 2)

    result["task_id"] = task_id
    result["status"] = TaskStatus.COMPLETED
    result["created_at"] = created_at
    result["duration_seconds"] = duration

    approved_db[task_id] = result
    return result

# /approve - Execute only planned steps
@router.post("/api/v1/plans/{plan_id}/approve")
def approve_plan(plan_id: str = Path(...)):
    if plan_id in rejected_db:
        return {
            "task_id": plan_id,
            "status": TaskStatus.REJECTED,
            "detail": "Cannot approve a task that was already rejected."
        }

    if plan_id in approved_db:
        return {
            "task_id": plan_id,
            "status": TaskStatus.COMPLETED,
            "detail": "Task was already approved and executed."
        }

    if plan_id not in pending_db:
        return {
            "task_id": plan_id,
            "status": TaskStatus.NOT_FOUND,
            "detail": "Task ID not found in pending plans"
        }

    original_request = pending_db[plan_id]["original_request"]
    print("[APPROVE] Executing selected steps only:")
    start_time = time.time()
    result_data = executor(original_request)
    duration = round(time.time() - start_time, 2)

    result = {
        "task_id": plan_id,
        "status": TaskStatus.COMPLETED,
        "created_at": datetime.utcnow().isoformat(),
        "duration_seconds": duration,
        "result": result_data
    }

    approved_db[plan_id] = result
    del pending_db[plan_id]

    return result

# /tasks/{id} - Get status
@router.get("/api/v1/tasks/{task_id}")
def get_task_status(task_id: str):
    if task_id in approved_db:
        return approved_db[task_id]

    if task_id in pending_db:
        return {
            "task_id": task_id,
            "status": TaskStatus.PENDING,
            "plan": pending_db[task_id].get("plan")
        }

    if task_id in rejected_db:
        return {
            "task_id": task_id,
            "status": TaskStatus.REJECTED,
            "detail": "This task was explicitly rejected and will not be executed."
        }

    return {
        "task_id": task_id,
        "status": TaskStatus.NOT_FOUND,
        "detail": "Task ID does not exist"
    }

# /reject - Reject a pending plan
@router.post("/api/v1/plans/{plan_id}/reject")
def reject_plan(plan_id: str = Path(...)):
    if plan_id in approved_db:
        return {
            "task_id": plan_id,
            "status": TaskStatus.COMPLETED,
            "detail": "Task was already approved and executed. Cannot reject it."
        }

    if plan_id in rejected_db:
        return {
            "task_id": plan_id,
            "status": TaskStatus.REJECTED,
            "detail": "Task was already rejected."
        }

    if plan_id not in pending_db:
        return {
            "task_id": plan_id,
            "status": TaskStatus.NOT_FOUND,
            "detail": "Task ID not found in pending plans"
        }

    rejected_db[plan_id] = pending_db[plan_id]
    del pending_db[plan_id]

    return {
        "task_id": plan_id,
        "status": TaskStatus.REJECTED,
        "detail": "Task has been rejected and removed from queue"
    }
