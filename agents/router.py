import dspy
import json

class PlanSteps(dspy.Signature):
    request = dspy.InputField()
    steps = dspy.OutputField(
        desc=(
            "Return the minimal JSON list of steps required for this task using ONLY the following:\n"
            "- 'Run diagnosis'\n"
            "- 'Generate script'\n"
            "- 'Write email'\n\n"
            "If the user explicitly asks for a script and does NOT request help understanding or troubleshooting, "
            "do NOT include 'Run diagnosis'. Only include it when the user asks about causes or problems.\n\n"
            "If the user says they do not want a script or diagnosis, respect that. "
            "Always include 'Write email' unless the user clearly says not to.\n\n"
            "Output must be a JSON list of steps."
        )
    )

class DSPyRouter(dspy.Module):
    def __init__(self):
        super().__init__()
        self.predict = dspy.Predict(PlanSteps)

    def forward(self, request: str) -> list[str]:
        try:
            print("[DSPyRouter] Request:", request)

            if not dspy.settings.lm:
                raise RuntimeError("DSPy LM is not configured. Call `dspy.settings.configure(...)` early in main.py")

            output = self.predict(request=request)
            raw = output.steps
            print("[DSPyRouter] Raw LLM Output:", raw)
            print("[DSPyRouter] Type of output.steps:", type(raw))

            # Case 1: Proper list from DSPy
            if isinstance(raw, list):
                return [step.strip("- ").strip() for step in raw]

            # Case 2: Stringified list (e.g., "['Generate script']")
            if isinstance(raw, str):
                try:
                    parsed = json.loads(raw.replace("'", '"'))
                    if isinstance(parsed, list):
                        return [step.strip("- ").strip() for step in parsed]
                except json.JSONDecodeError:
                    pass

                # Case 3: Newline-separated list in string
                if "\n" in raw:
                    print("[DSPyRouter] Fixing newline-delimited string...")
                    raw_lines = [line.strip("- ").strip() for line in raw.split("\n") if line.strip()]
                    return raw_lines

                # Fallback: single step, cleanup dash
                return [raw.strip("- ").strip()]

            raise ValueError("Unexpected DSPy output format")

        except Exception as e:
            print(f"[DSPyRouter Fallback] {e}")
            return ["Generate script"]
