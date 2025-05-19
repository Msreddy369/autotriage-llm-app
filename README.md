# AIAutopilot System

This project implements an intelligent LLM-based IT automation system capable of:

- Diagnosing user-reported technical issues
- Generating actionable PowerShell scripts
- Summarizing findings via email
- Dynamically planning execution steps using a DSPy router
- Supporting manual approval flows and retry logic

## Project Structure

```
AIAUTOPILOT_FASTAPI/
├── agents/               # LLM-based modular agent logic
│   ├── automation.py     # Generates PowerShell scripts
│   ├── coordinator.py    # Central DSPy-based executor
│   ├── diagnostic.py     # Identifies root causes and solutions
│   ├── router.py         # DSPyRouter for intelligent step planning
│   └── writer.py         # Summarizes diagnosis into an email draft
│
├── config/
│   └── dspy_setup.py     # Configures DSPy (LLM backend)
│
├── models/               # Pydantic models for FastAPI schema
│   ├── status.py         # Enum for task statuses
│   └── task.py           # Task request model
│
├── routes/
│   └── tasks.py          # FastAPI endpoints (execute, approve, reject)
│
├── tests/
│   └── test_app.py       # Pytest test cases for all flows
│
├── graph.py              # LangGraph state machine for agent orchestration
├── main.py               # FastAPI app launcher
├── requirements.txt      # Python dependencies (no version pins)
└── README.md             # Project documentation
```

## Features

- LLM-based step planner using **DSPy**
- Execution orchestrated with **LangGraph**
- Modular, testable agents (diagnostic, scripting, summarization)
- Conditional step execution based on LLM reasoning
- Approval workflows (`/approve`, `/reject`)
- Retry logic for agent errors (e.g., script generation)
- Full test suite with `pytest`

## Getting Started

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure DSPy with OpenAI API Key

Open the file `config/dspy_setup.py` and replace `"your-openai-api-key"` with your actual key:

```python
import dspy
from dspy import OpenAI

# Set up DSPy LLM configuration
dspy.settings.configure(
    lm=OpenAI(
        model="gpt-3.5-turbo",
        api_key="your-openai-api-key"
    )
)
```

### 3. Run FastAPI Server

```bash
uvicorn main:app --reload
```

### 4. Access Swagger UI

```
http://localhost:8000/docs
```

## API Endpoints

### POST /api/v1/execute

Triggers a new task. Accepts natural language input and decides the necessary steps dynamically.

**Request Body:**
```json
{
  "request": "Describe the issue here...",
  "require_approval": true
}
```

### POST /api/v1/plans/{task_id}/approve

Approves a pending plan and executes only the planned steps.

### POST /api/v1/plans/{task_id}/reject

Rejects the pending task. It will not be executed.

### GET /api/v1/tasks/{task_id}

Retrieves the current status of a task.

## How It Works

1. **DSPyRouter** receives a user request and outputs a list of required steps:
   - "Run diagnosis"
   - "Generate script"
   - "Write email"

2. **LangGraph** builds a flow dynamically:
   - Conditionally skips steps like diagnosis/script if not required.
   - Always writes an email unless explicitly omitted.

3. **Agents** are executed one by one. Retry is built-in for script generation.

## Testing the System

### Run All Tests

```bash
PYTHONPATH=. pytest tests/
```

### Run Individual Test

```bash
PYTHONPATH=. pytest tests/test_app.py::test_approval_flow
```

### Covered Scenarios

- Happy path (all agents run)
- Approval flow
- Rejection handling
- Script-only and diagnosis-only paths
- Retry handling for agent failure (e.g., script agent)
- Email is always sent unless excluded

## Example API Input & Output

### Example A: Direct Execution

**Request:**
```json
{
  "request": "Diagnose why CPU usage on my server is high and give me a script to log it.",
  "require_approval": false
}
```

### Example B: Approval Flow

**Request:**
```json
{
  "request": "Restrict RDP access to 10.0.0.0/24 for 3 Azure VMs.",
  "require_approval": true
}
```

## Dependencies

See `requirements.txt`:

```
fastapi
uvicorn
dspy
langgraph
langchain
langchain-openai
pydantic
pytest
httpx
```