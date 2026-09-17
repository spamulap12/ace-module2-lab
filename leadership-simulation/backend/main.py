import datetime
import logging
from typing import Dict, Any
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from models import (
    StartResponse, ChatRequest, ChatResponse, SessionStateResponse,
    Message, KPIValues, KPIDeltas
)
from session_manager import session_store
from kpi_engine import calculate_kpi_updates
from gemini_agents import call_agent_1, call_agent_2

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cymbal_simulator")

app = FastAPI(
    title="Cymbal Leadership Simulator API",
    description="Backend API powering the gamified HR leadership simulation for Cymbal AI",
    version="1.0.0"
)

# Enable CORS for frontend on port 3002 and local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3002", "http://127.0.0.1:3002", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "Cymbal Leadership Simulator API", "timestamp": datetime.datetime.now().isoformat()}

@app.post("/api/start", response_model=StartResponse)
def start_session():
    session_id = session_store.create_session()
    sess = session_store.get_session(session_id)
    
    return StartResponse(
        session_id=session_id,
        current_phase=sess["current_phase"],
        kpis=sess["kpis"],
        initial_message=sess["transcript"][0].text,
        memos=sess["memos"]
    )

@app.post("/api/chat", response_model=ChatResponse)
async def chat_interaction(payload: ChatRequest):
    sess = session_store.get_session(payload.session_id)
    if not sess:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session ID '{payload.session_id}' not found."
        )

    if sess["is_completed"]:
        return ChatResponse(
            session_id=payload.session_id,
            current_phase=sess["current_phase"],
            agent_message="The simulation is already complete. View your evaluation scorecard below.",
            kpis=sess["kpis"],
            kpi_deltas=KPIDeltas(),
            is_completed=True,
            evaluation=sess["evaluation"]
        )

    curr_phase = sess["current_phase"]
    curr_kpis = sess["kpis"]
    turn_count = sess["turn_count"] + 1

    # Record user message in transcript
    user_msg = Message(
        sender="user",
        text=payload.message,
        phase=curr_phase,
        timestamp=datetime.datetime.now().strftime("%H:%M:%S")
    )
    sess["transcript"].append(user_msg)

    # Compute updated KPIs and deltas
    updated_kpis, kpi_deltas = calculate_kpi_updates(curr_phase, payload.message, curr_kpis)
    sess["kpis"] = updated_kpis

    # Call Agent 1 for response and potential phase advance
    agent_text, next_phase, is_agent1_done = await call_agent_1(
        current_phase=curr_phase,
        candidate_message=payload.message,
        transcript=sess["transcript"],
        kpis=updated_kpis
    )

    # Update phase
    sess["current_phase"] = next_phase
    sess["turn_count"] = turn_count

    # Fail-safe graduation check (If turn_count >= 3 or Agent 1 outputs completion marker)
    is_completed = is_agent1_done or (turn_count >= 3)
    sess["is_completed"] = is_completed

    # Record Agent 1 message in transcript
    agent_msg = Message(
        sender="agent",
        text=agent_text,
        phase=next_phase,
        timestamp=datetime.datetime.now().strftime("%H:%M:%S")
    )
    sess["transcript"].append(agent_msg)

    # If simulation is completed, invoke Agent 2 for Evaluation Scorecard
    evaluation = sess["evaluation"]
    if is_completed and not evaluation:
        logger.info(f"Triggering Agent 2 Evaluation for session {payload.session_id}")
        evaluation = await call_agent_2(sess["transcript"], updated_kpis)
        sess["evaluation"] = evaluation

    # Update session store
    session_store.update_session(payload.session_id, sess)

    return ChatResponse(
        session_id=payload.session_id,
        current_phase=sess["current_phase"],
        agent_message=agent_text,
        kpis=updated_kpis,
        kpi_deltas=kpi_deltas,
        is_completed=is_completed,
        evaluation=evaluation
    )

@app.get("/api/session/{session_id}", response_model=SessionStateResponse)
def get_session_state(session_id: str):
    sess = session_store.get_session(session_id)
    if not sess:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session ID '{session_id}' not found."
        )

    return SessionStateResponse(
        session_id=sess["session_id"],
        current_phase=sess["current_phase"],
        turn_count=sess["turn_count"],
        kpis=sess["kpis"],
        transcript=sess["transcript"],
        is_completed=sess["is_completed"],
        evaluation=sess["evaluation"],
        memos=sess["memos"]
    )

@app.post("/api/reset/{session_id}")
def reset_session(session_id: str):
    new_id = session_store.create_session()
    new_sess = session_store.get_session(new_id)
    return {
        "status": "reset",
        "old_session_id": session_id,
        "new_session_id": new_id,
        "current_phase": new_sess["current_phase"],
        "kpis": new_sess["kpis"],
        "initial_message": new_sess["transcript"][0].text,
        "memos": new_sess["memos"]
    }
