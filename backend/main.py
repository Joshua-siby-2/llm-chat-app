from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import ollama
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict

# Setup
app = FastAPI()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Models
class ChatRequest(BaseModel):
    message: str
    model: str = "mistral"


class ChatHistory(BaseModel):
    conversations: List[Dict] = []
    current_messages: List[Dict] = []


# State
chat_history = ChatHistory()
last_request_time = None


# Endpoints
@app.get("/health")
async def health_check():
    return {"status": "healthy", "models": ollama.list().get("models", [])}


@app.post("/chat")
async def chat(request: Request):
    global last_request_time

    # Rate limiting
    if last_request_time and datetime.now() - last_request_time < timedelta(seconds=1):
        raise HTTPException(status_code=429, detail="Too many requests")
    last_request_time = datetime.now()

    try:
        data = await request.json()
        req = ChatRequest(**data)

        # Add user message to history
        chat_history.current_messages.append({"role": "user", "content": req.message})

        def generate():
            try:
                assistant_response = ""
                stream = ollama.chat(
                    model=req.model,
                    messages=chat_history.current_messages,
                    stream=True
                )

                for chunk in stream:
                    if not chunk.get("message"):
                        continue

                    content = chunk["message"].get("content", "")
                    assistant_response += content

                    yield f"data: {json.dumps({
                        'content': content,
                        'model': req.model
                    })}\n\n"

                # Save completed conversation
                chat_history.current_messages.append({
                    "role": "assistant",
                    "content": assistant_response,
                    "model": req.model
                })

            except ollama.ResponseError as e:
                logger.error(f"Ollama error: {e.error}")
                yield f"data: {{\"error\": \"{e.error}\"}}\n\n"
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                yield f"data: {{\"error\": \"Service error\"}}\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")


@app.post("/new_chat")
async def new_chat():
    if chat_history.current_messages:
        chat_history.conversations.append({
            "timestamp": datetime.now().isoformat(),
            "messages": chat_history.current_messages.copy()
        })
    chat_history.current_messages = []
    return {"status": "new chat started"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")