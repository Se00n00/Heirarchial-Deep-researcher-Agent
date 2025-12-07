from groq import Groq
import os
from dotenv import load_dotenv
from jinja2 import Template

load_dotenv()
GROQ_API_KEY = os.environ["GROQ_API_KEY"]

client = Groq(
    api_key=GROQ_API_KEY
)
print(client.base_url)
def render_yaml_template(self, file_path, var):
    with open(file_path, "r") as f:
      file_content = f.read()
    template = Template(file_content)
    rendered = template.render(**var)
    return rendered
  


response = client.chat.completions.create(
    messages=[{
       "role":"system",
       "content":"""Explain the importance of fast language models, return is json format: 'name':'what are you answering', 'paramerers':'answering parameters'""",
    }],
    model="openai/gpt-oss-20b",
)
print(response)