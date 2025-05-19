from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
import json

class AutomationAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-3.5-turbo")

        self.prompt = ChatPromptTemplate.from_template(
            "You're an IT automation assistant.\n"
            "Given this issue:\n\n{issue}\n\n"
            "Respond ONLY in this exact JSON format:\n"
            "{{\n"
            '  "language": "powershell",\n'
            '  "code": "...",\n'
            '  "lint_passed": true\n'
            "}}\n"
            "Do NOT add any explanation or plain text. Respond with just the JSON."
        )

    def run(self, issue: str) -> dict:
        messages = self.prompt.format_messages(issue=issue)
        response = self.llm.invoke(messages)  # Replace __call__ with invoke

        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            return {
                "language": "unknown",
                "code": "# GPT response was not valid JSON.",
                "lint_passed": False
            }


