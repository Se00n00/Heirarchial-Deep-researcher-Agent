from pydantic import BaseModel
import os
from dotenv import load_dotenv

load_dotenv()


class ChatMessage(BaseModel):
    role: str  # 'user' or 'model'
    content: str

    @classmethod
    def from_dict(cls, d):
        return cls(role=d.get('role'), content=d.get('content'))


class GroqChatModel:
    """Adapter for groq.Client completion API.

    The adapter runs the async API call and returns a small object with
    `.content` and `.tool_calls` so the rest of the code can use it.
    """
    def __init__(self, model: str, api_key: str):
        self.model = model  # e.g. 'mixtral-8x7b-32768'
        self.api_key = api_key

    async def __call__(self, messages, tools_to_call_from=None):
        prompt = "\n".join([m.content for m in messages])

        import groq
        client = groq.AsyncClient(api_key=self.api_key)
        
        completion = await client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=self.model,
            temperature=0.5,
        )

        # Extract the response text
        text = completion.choices[0].message.content if completion.choices else ""

        class Resp:
            def __init__(self, content):
                self.content = content
                self.tool_calls = []

        return Resp(text)

        return await loop.run_in_executor(None, sync_call)



class ModelManager:
    def __init__(self):
        self.registered_models = {}
        # Use GROQ_API_KEY first, fall back to others if not found
        key = os.environ.get('GROQ_API_KEY')
        if key:
            self.registered_models['gemini-pro'] = GroqChatModel(
                model='llama-3.1-8b-instant',  # Llama model
                api_key=key,
            )
            # convenience alias
            self.registered_models.setdefault('gpt-4.1', self.registered_models['gemini-pro'])
        else:
            print('Warning: GROQ_API_KEY not set; no models registered')

model_manager = ModelManager()
