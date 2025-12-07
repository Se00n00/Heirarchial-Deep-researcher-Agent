from groq import Groq
import os
from dotenv import load_dotenv
load_dotenv()


client = Groq(
    api_key=os.environ["GROQ_API_KEY"],
)
print(client.base_url)

resp = client.chat.completions.create(
    model="openai/gpt-oss-20b",
    messages=[{"role": "user", "content": "hi"}]
)
print(resp)
