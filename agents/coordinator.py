from agents.diagnostic import DiagnosticAgent
from agents.automation import AutomationAgent
from agents.writer import WriterAgent
import dspy
from agents.router import DSPyRouter

class CoordinatorAgent:
    def __init__(self):
        self.diagnostic = DiagnosticAgent()
        self.automation = AutomationAgent()
        self.writer = WriterAgent()

    def run(self, request: str) -> dict:
        diagnosis = self.diagnostic.run(request)
        script = self.automation.run(request)
        email = self.writer.run(diagnosis)
        return {
            "status": "completed",
            "diagnosis": diagnosis,
            "script": script,
            "email_draft": email
        }

class DSPyExecutor(dspy.Module):
    def __init__(self, agents: dict):
        super().__init__()
        self.router = DSPyRouter()
        self.agents = agents

    def forward(self, request: str):
        steps = self.router.forward(request)
        print("[DSPyExecutor] Planned steps:", steps)
        results = []

        # Build a shared state to pass between agents
        state = {"request": request}

        for step in steps:
            agent = self.agents.get(step)
            if agent:
                print(f"[DSPyExecutor] Running: {step}")
                if step == "Run diagnosis":
                    diagnosis = agent.run(request)
                    state["diagnosis"] = diagnosis
                    results.append({step: diagnosis})
                elif step == "Generate script":
                    script = agent.run(request)
                    state["script"] = script
                    results.append({step: script})
                elif step == "Write email":
                    email = agent.run(state)  # ✅ Now passing full state
                    state["email_draft"] = email
                    results.append({step: email})
            else:
                print(f"[DSPyExecutor] No agent found for step: {step}")

        return results
