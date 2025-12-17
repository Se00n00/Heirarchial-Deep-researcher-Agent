from src.agent import create_agent

from fastapi import FastAPI, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import asyncio

import json

#------------------------ SETUP: CORS
app = FastAPI()
origins = [
    "http://localhost:4200",   # Angular dev server
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # or ["*"] for open access
    allow_credentials=True,
    allow_methods=["*"],          # very important: allows OPTIONS
    allow_headers=["*"],
)

#------------------------------------------------------------------------#
# ------------------------ [ENDPOINT: / ]----------------------------#
#------------------------------------------------------------------------#
@app.get("/")
def home():
    return {"message":"It is going to be SOTA"}


#------------------------------------------------------------------------#
# ------------------------ [ENDPOINT: /chat ]----------------------------#
#------------------------------------------------------------------------#
class RequestModel(BaseModel):
    query: str


@app.post("/chat")
async def chat(request: RequestModel):
    query = request.query

    async def event_generator():
        try:
            # ← This is a SYNC generator → we must use normal 'for', not 'async for'
            agent = create_agent()
            for log in agent.forward(query):

                # Decide what format you want to send
                if isinstance(log, dict):
                    payload = json.dumps(log) + "\n"
                else:
                    payload = json.dumps({"content": str(log)}) + "\n"

                # Must yield str or bytes!
                yield payload

                # Very important: give the event loop a breath
                await asyncio.sleep(0.01)


        except Exception as e:
            import traceback
            error_payload = {
                "type": "ERROR",
                "heading": "Exception",
                "content": str(e),
                "traceback": traceback.format_exc()
            }
            yield json.dumps(error_payload) + "\n"

    # Use text/event-stream for proper SSE (recommended)
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # disables nginx buffering
        }
    )