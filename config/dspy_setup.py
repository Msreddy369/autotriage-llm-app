import dspy
import os

openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set. Please set it to your OpenAI API key.")

# Alternative configuration using dspy.LM
dspy.settings.configure(lm=dspy.LM(model="gpt-3.5-turbo", api_key=openai_api_key))
print("DSPy configured with OpenAI GPT-3.5-turbo")