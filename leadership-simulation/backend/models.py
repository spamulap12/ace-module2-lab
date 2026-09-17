from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class KPIValues(BaseModel):
    morale: float = Field(default=70.0, ge=0.0, le=100.0, description="Team Morale percentage")
    productivity: float = Field(default=80.0, ge=0.0, le=100.0, description="Productivity percentage")
    burnout_risk: float = Field(default=30.0, ge=0.0, le=100.0, description="Burnout Risk percentage")

class KPIDeltas(BaseModel):
    morale: float = 0.0
    productivity: float = 0.0
    burnout_risk: float = 0.0

class Message(BaseModel):
    sender: str  # "user" or "agent"
    text: str
    phase: int
    timestamp: str

class Memo(BaseModel):
    id: str
    phase: int
    title: str
    sender: str
    subject: str
    date: str
    content: str
    priority: str  # "High", "Medium", "Urgent"
    read: bool = False

class StartResponse(BaseModel):
    session_id: str
    current_phase: int
    kpis: KPIValues
    initial_message: str
    memos: List[Memo]

class ChatRequest(BaseModel):
    session_id: str
    message: str

class MetricDetail(BaseModel):
    score: int
    analysis: str

class EvaluationMetrics(BaseModel):
    empathy: MetricDetail
    decision_making: MetricDetail
    communication: MetricDetail
    team_sustainability: MetricDetail

class EvaluationScorecard(BaseModel):
    candidate_rating: str  # "Strong Leader", "Developing", or "Needs Support"
    overall_score: int
    metrics: EvaluationMetrics
    key_strengths: List[str]
    areas_for_growth: List[str]
    executive_summary: str

class ChatResponse(BaseModel):
    session_id: str
    current_phase: int
    agent_message: str
    kpis: KPIValues
    kpi_deltas: KPIDeltas
    is_completed: bool = False
    evaluation: Optional[Dict[str, Any]] = None

class SessionStateResponse(BaseModel):
    session_id: str
    current_phase: int
    turn_count: int
    kpis: KPIValues
    transcript: List[Message]
    is_completed: bool
    evaluation: Optional[Dict[str, Any]] = None
    memos: List[Memo]
