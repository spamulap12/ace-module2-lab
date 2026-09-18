# ruff: noqa
import os
import logging
import google.auth
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google.adk.agents import Agent
from google.adk.models import Gemini
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.genai import types

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cymbal_policy_concierge")

# Set environment credentials for ADK and google-genai
try:
    _, project_id = google.auth.default()
    os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
except Exception as e:
    logger.warning(f"Could not load default GCP credentials: {e}")

os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

# Ensure parent directory is in sys.path so travel_policy_agent package can be imported
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the agent from the package
from travel_policy_agent import root_agent


session_service = InMemorySessionService()
runner = Runner(agent=root_agent, session_service=session_service, app_name="cymbal-travel-policy")

# --- FastAPI App ---
app = FastAPI(
    title="Cymbal Group Travel Policy Concierge",
    description="API for corporate travel and expense policy questions"
)

# Enable CORS so frontend on separate port can communicate
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None

class ChatResponse(BaseModel):
    response: str
    session_id: str

@app.get("/")
def read_root():
    return {
        "status": "online",
        "agent": "Cymbal Group Travel Policy Concierge",
        "framework": "Google ADK"
    }

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    session_id = request.session_id
    if not session_id:
        session = session_service.create_session_sync(
            app_name="cymbal-travel-policy",
            user_id="default_user"
        )
        session_id = session.id
    else:
        try:
            session = session_service.get_session_sync(
                app_name="cymbal-travel-policy",
                user_id="default_user",
                session_id=session_id
            )
            if not session:
                session = session_service.create_session_sync(
                    app_name="cymbal-travel-policy",
                    user_id="default_user",
                    session_id=session_id
                )
        except Exception:
            session = session_service.create_session_sync(
                app_name="cymbal-travel-policy",
                user_id="default_user",
                session_id=session_id
            )

    # Wrap query into the ADK expected type.Content
    message = types.Content(
        role="user",
        parts=[types.Part.from_text(text=request.message)]
    )

    try:
        # Run ADK agent
        events = runner.run(
            new_message=message,
            user_id="default_user",
            session_id=session_id,
            run_config=RunConfig(streaming_mode=StreamingMode.NONE),
        )
        
        response_text = ""
        for event in events:
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        response_text += part.text

        if not response_text:
            response_text = "I'm sorry, I could not process your request at this time."

        return ChatResponse(response=response_text.strip(), session_id=session_id)

    except Exception as e:
        logger.error(f"Error executing agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
