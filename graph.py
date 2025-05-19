from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
from agents.coordinator import DiagnosticAgent, AutomationAgent, WriterAgent
from agents.router import DSPyRouter  # Intelligent step planner

# Shared memory state
class GraphState(TypedDict, total=False):
    request: str
    diagnosis: Annotated[dict, "diagnosis"]
    script: Annotated[dict, "script"]
    email_draft: Annotated[str, "email_draft"]
    skip_diagnosis: bool
    skip_script: bool

# Agent instances
diagnostic_agent = DiagnosticAgent()
automation_agent = AutomationAgent()
writer_agent = WriterAgent()
router = DSPyRouter()

# Intelligent DSPy planner
def plan_steps(state: GraphState) -> GraphState:
    request = state["request"]
    steps = router.forward(request)

    #  Always force "Write email"
    if "Write email" not in steps:
        steps.append("Write email")
        print("[Plan] 'Write email' was added to DSPy steps manually.")

    print(f"[DSPy Planner] Final planned steps: {steps}")

    state["skip_diagnosis"] = "Run diagnosis" not in steps
    state["skip_script"] = "Generate script" not in steps
    return state

# Conditional diagnosis step
def run_diagnosis(state: GraphState) -> GraphState:
    if state.get("skip_diagnosis"):
        print("[Graph] Skipping diagnosis step")
        return state
    print("[Graph] Running diagnosis...")
    diagnosis = diagnostic_agent.run(state["request"])
    state["diagnosis"] = diagnosis
    return state

# Conditional script generation step
def run_script_generation(state: GraphState) -> GraphState:
    if state.get("skip_script"):
        print("[Graph] Skipping script generation step")
        return state

    print("[Graph] Running script generation...")

    for attempt in range(3):
        try:
            script = automation_agent.run(state["request"])
            state["script"] = script
            return state
        except Exception as e:
            print(f"[Script Retry {attempt + 1}] Failed: {e}")
            if attempt == 2:
                raise RuntimeError("Script agent failed after 3 retries.")

    return state  # Fallback (shouldn't be reached)


# Always run email writer
def run_writer(state: GraphState) -> GraphState:
    print("[Graph] Running email writer...")
    email = writer_agent.run(state)
    state["email_draft"] = email
    return state

# Build the LangGraph
builder = StateGraph(GraphState)

builder.add_node("plan", plan_steps)
builder.add_node("diagnose", run_diagnosis)
builder.add_node("generate_script", run_script_generation)
builder.add_node("write_email", run_writer)

builder.set_entry_point("plan")
builder.add_edge("plan", "diagnose")
builder.add_edge("diagnose", "generate_script")
builder.add_edge("generate_script", "write_email")
builder.add_edge("write_email", END)

graph = builder.compile()

# Local test
if __name__ == "__main__":
    input_state = {
        "request": "Why is my laptop unresponsive after boot? I just want to understand the issue and don't want a script."
    }
    final_state = graph.invoke(input_state)
    print("\n Final Result:")
    print(final_state)
