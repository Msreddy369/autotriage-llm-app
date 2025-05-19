from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

class WriterAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-3.5-turbo")
        self.prompt = ChatPromptTemplate.from_template(
            "Summarize this diagnosis and proposed solutions into a short email:\n\n{diagnosis}"
        )

    def run(self, state: dict) -> str:
        diagnosis = state.get("diagnosis", {
            "root_cause": "N/A",
            "evidence": [],
            "solutions": []
        })
        messages = self.prompt.format_messages(diagnosis=diagnosis)
        response = self.llm.invoke(messages)
        return response.content

    
