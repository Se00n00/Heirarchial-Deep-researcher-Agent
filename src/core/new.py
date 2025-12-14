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


# 1. **Search**: Start by using `web_search_tool` to find relevant URLs.
# 2. **Visit**: Use `visit_page` or `download_tool` to get content from promising results.
# 3. **Inetract**: Use `page_up` and `page_down` to interact with visited page.
# 4. **Extract**: Look for the specific answer in the tool output.
# 5. **Answer**: Once you have the specific data, return `final_answer`.
#  - You can use other available tools also