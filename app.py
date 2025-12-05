from src.agent import planner

from fastapi import FastAPI, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

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
    try:
        async def event_generator():
            planner.forward(query)
            
        return StreamingResponse(event_generator(), media_type='text/plain')
    except Exception as e:
        return {
            "type":"SYSTEM",
            "heading":"Exception",
            "content": str(e)
        }