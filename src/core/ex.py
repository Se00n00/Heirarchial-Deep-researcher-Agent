from openai import OpenAI
import os
from dotenv import load_dotenv
from jinja2 import Template

load_dotenv()

client = OpenAI(
    api_key=os.environ["GROQ_API_KEY"],
    base_url="https://api.groq.com/openai/v1",
)

def render_yaml_template(self, file_path, var):
    with open(file_path, "r") as f:
      file_content = f.read()
    template = Template(file_content)
    rendered = template.render(**var)
    return rendered
  


response = client.responses.create(
    input="Explain the importance of fast language models, return is json format: 'name':'what are you answering', 'paramerers':'answering parameters'",
    model="openai/gpt-oss-20b",
)
print(response.output_text)