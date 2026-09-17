import os
import logging
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.sessions.base_session_service import GetSessionConfig
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.genai import types
from google.adk.cli.fast_api import get_fast_api_app
from google.adk.cli.utils.agent_loader import AgentLoader

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cymbal_policy_concierge")

# Import the agent
from app.agent import root_agent

# Get resolved single agent name from ADK AgentLoader to guarantee matching fast_api expectations
loader = AgentLoader(".")
app_name = loader.single_agent_name or "travel_policy_agent"

# Initialize full ADK FastAPI app with Reasoning Engine endpoints (/api/reasoning_engine, etc.)
app = get_fast_api_app(
    agents_dir=".",
    web=False,
    auto_create_session=True,
    gemini_enterprise_app_name=app_name,
)
app.title = "Cymbal Group Travel Policy Concierge API"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Session Service and Runner for direct /chat endpoint
session_service = InMemorySessionService()
runner = Runner(
    agent=root_agent,
    session_service=session_service,
    auto_create_session=True,
    app_name="cymbal_policy_concierge"
)

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default_user"

class ChatResponse(BaseModel):
    response: str

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        session_config = GetSessionConfig(num_recent_events=20)
        run_config = RunConfig(
            streaming_mode=StreamingMode.NONE,
            get_session_config=session_config
        )
        response_text = ""
        new_message = types.Content(
            role="user",
            parts=[types.Part(text=request.message)]
        )
        async for event in runner.run_async(
            new_message=new_message,
            user_id=request.session_id,
            session_id=request.session_id,
            run_config=run_config
        ):
            logger.info(f"Received event from {event.author}: {event.content}")
            if event.content and event.content.parts and event.author != "user":
                for part in event.content.parts:
                    if part.text:
                        response_text += part.text
        return ChatResponse(response=response_text)
    except Exception as e:
        logger.error(f"Error during chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
