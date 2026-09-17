import os
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from agent import TravelPolicyAgent, clear_session_history

app = FastAPI(
    title="Cymbal Group Travel Policy Agent API",
    description="FastAPI Backend for Cymbal Group Travel Policy Concierge powered by Google ADK and Gemini 3.6 Flash",
    version="1.0.0"
)

# Enable CORS for local Node.js / React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize global TravelPolicyAgent instance
agent = TravelPolicyAgent()


class ChatRequest(BaseModel):
    message: str = Field(..., description="Employee's travel policy question")
    session_id: Optional[str] = Field("default_session", description="Session identifier for conversation memory")


class ContextChunk(BaseModel):
    chunk_id: str
    section: str
    title: str
    content: str


class ChatResponse(BaseModel):
    response: str
    retrieved_context: List[ContextChunk]
    session_id: str


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "cymbal-travel-policy-agent",
        "version": "1.0.0"
    }


@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")
    
    session_id = request.session_id or "default_session"
    result = agent.process_message(request.message.strip(), session_id=session_id)
    
    return ChatResponse(
        response=result["response"],
        retrieved_context=result["retrieved_context"],
        session_id=session_id
    )


@app.post("/clear_session")
def clear_session(session_id: str = "default_session"):
    clear_session_history(session_id)
    return {"status": "success", "message": f"Session memory cleared for {session_id}"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
