from src.agent import planner

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
            async for log in planner.forward(query):

                print("LOG:", log)

                # Format output
                payload = json.dumps(log) + "\n"

                yield payload
                await asyncio.sleep(0.001)

            yield json.dumps({"type": "DONE"}) + "\n"

        except Exception as e:
            import traceback

            yield json.dumps({
                "type": "ERROR",
                "heading": "Exception",
                "content": str(e),
                "traceback": traceback.format_exc()
            }) + "\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
