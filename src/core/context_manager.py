from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()


system_prompt = """
  You are a tool-output summarization agent.

  Your task:
    - Read the raw output produced by a tool.
    - Extract only task-relevant, decision-useful facts.
    - Discard navigation text, UI elements, boilerplate, repetition, and procedural noise.
    - Preserve facts, results, constraints, errors, and signals that materially affect task completion.

  Output rules:
    - Output concise Markdown only.
    - Use bullet points.
    - Do NOT add, infer, or reinterpret information.
    - Do NOT explain or restate the task.
    - Include only extracted content.
    - Keep the summary extremely short (max 3–4 bullets; usually 1–2).
"""
user_prompt = """
  Task being solved: {task}
  Tool used: {tool_used}
  Raw tool output:
  {observations}
"""

class Context_Manager:
  def __init__(self, model):
    self.inference_client = Groq(
      api_key=os.getenv("GROQ_API_KEY")
    )
    self.model = model

  def forward(self, task:str = "", observations:str = "", tool_used:str = ""):

    context = [
        {"role": "system","content":system_prompt},
        {"role": "user", "content": user_prompt.format(task = task, observations = observations, tool_used = tool_used)}
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



# observation = """
#   nothing here 
# """
# c = Context_Manager(model="llama-3.1-8b-instant")
# print(c.forward(task="what is the current weather of japan", observations=observation))