from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()


system_prompt = """
    You are a context management agent.

    Your task:
        - Extract only decision-relevant facts from the given observations.
        - Remove duplicates, noise, and procedural details.
        - Preserve information that helps a task manager complete the task.

    Output rules:
        - Return concise Markdown only (no JSON).
        - Use bullet points.
        - Do not add new information.
        - Keep the output as short as possible.

"""
user_prompt = """
    task manager is solving: {task}
    Observations till now: {observations}
"""

class Context_Manager:
  def __init__(self, model):
    self.inference_client = Groq(
      api_key=os.getenv("GROQ_API_KEY")
    )
    self.model = model

  def forward(self, task:str = "", observations:str = ""):

    context = [
        {"role": "system","content":system_prompt},
        {"role": "user", "content": user_prompt.format(task = task, observations = observations)}
    ]

    try:
      response = self.inference_client.chat.completions.create(
        model = self.model,
        messages = context,
        stream = False
      )

      
      raw = response.choices[0].message.content
      return raw
      
    except Exception as e:
        return f"Context manager failed. Returning original observations.\n\n{observations}"
        # If context_manager tools fails 