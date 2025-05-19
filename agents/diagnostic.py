import json
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

class DiagnosticAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-3.5-turbo")
        self.prompt = ChatPromptTemplate.from_template(
            "You are a diagnostic expert. A user reports the following issue:\n\n{issue}\n\n"
            "Analyze the root cause, list any evidence, and propose 2-3 solutions.\n"
            "Respond in this JSON format:\n"
            "{{\n"
            '  "root_cause": "...",\n'
            '  "evidence": ["...", "..."],\n'
            '  "solutions": [\n'
            '    {{"title": "...", "confidence": "high/medium/low"}},\n'
            "    ...\n"
            "  ]\n"
            "}}"
        )

    def run(self, issue: str) -> dict:
        messages = self.prompt.format_messages(issue=issue)
        response = self.llm.invoke(messages)  # Replace __call__ with invoke

        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            return {
                "root_cause": "Unable to parse GPT response",
                "evidence": [],
                "solutions": [
                    {"title": "Check GPT output format or retry", "confidence": "low"}
                ]
            }
