import uuid
import datetime
from typing import Dict, Optional, List
from models import KPIValues, Message, Memo, SessionStateResponse

class SessionStore:
    def __init__(self):
        self._sessions: Dict[str, Dict] = {}

    def create_session(self) -> str:
        session_id = str(uuid.uuid4())
        
        initial_kpis = KPIValues(morale=70.0, productivity=80.0, burnout_risk=30.0)
        
        initial_memos = [
            Memo(
                id="memo-p1",
                phase=1,
                title="Formal Complaint: Code Review Conflict",
                sender="Alex (Senior Engineer)",
                subject="Urgent: Unprofessional conduct during PR #402 review",
                date=datetime.datetime.now().strftime("%b %d, %Y - %H:%M"),
                priority="High",
                content=(
                    "Hi Manager,\n\n"
                    "I am writing to formally lodge a complaint regarding Morgan's comments on PR #402 yesterday. "
                    "Morgan's review was dismissive and personally critical rather than focused on technical architecture. "
                    "At this stage, I refuse to continue pair programming or sharing code review duties with Morgan until management addresses this behavior.\n\n"
                    "Best regards,\nAlex"
                ),
                read=False
            ),
            Memo(
                id="memo-p2",
                phase=2,
                title="CRITICAL: VP Engineering Launch Directive",
                sender="VP of Engineering",
                subject="48-Hour Launch Deadline Warning - Cymbal AI v2.0",
                date=datetime.datetime.now().strftime("%b %d, %Y - %H:%M"),
                priority="Urgent",
                content=(
                    "Engineering Team,\n\n"
                    "We are 48 hours away from the publicized Cymbal AI v2.0 press launch. "
                    "According to our metrics dashboard, critical integration tests are 2 days behind schedule.\n\n"
                    "As Engineering Manager, you must decide immediately whether to mandate crunch time to hit our date, "
                    "request a formal launch extension from executive leadership, or cut non-essential scope.\n\n"
                    "Regards,\nVP of Engineering"
                ),
                read=False
            ),
            Memo(
                id="memo-p3",
                phase=3,
                title="Confidential: Jordan Performance Tracker",
                sender="HR Operations",
                subject="Sprint Retrospective: Jordan (Junior Developer)",
                date=datetime.datetime.now().strftime("%b %d, %Y - %H:%M"),
                priority="Medium",
                content=(
                    "Manager Confidential Memo:\n\n"
                    "Jordan has missed deliverables for two consecutive sprints and appears disengaged during team standups. "
                    "Jordan is a high-potential junior engineer, but recent crunch stress seems to have impacted output.\n\n"
                    "Please schedule a direct 1-on-1 feedback session to set clear expectations while offering appropriate support.\n\n"
                    "HR Talent Team"
                ),
                read=False
            )
        ]

        initial_greeting = (
            "Welcome to the Cymbal Leadership Simulator! I am your HR Advisor & Executive Coach.\n\n"
            "You have just taken over as Engineering Manager for the Cymbal AI core platform team. "
            "Your performance will be measured across **Team Morale (70%)**, **Productivity (80%)**, and **Burnout Risk (30%)**.\n\n"
            "--- **Phase 1: The Dispute** ---\n"
            "We have an immediate interpersonal crisis. Senior Engineer Alex and Tech Lead Morgan got into a heated argument over PR #402. "
            "Alex has submitted a formal complaint (check your Inbox Panel) and both are refusing to work together.\n\n"
            "How do you plan to mediate this conflict and get the team collaborating again?"
        )

        initial_msg = Message(
            sender="agent",
            text=initial_greeting,
            phase=1,
            timestamp=datetime.datetime.now().strftime("%H:%M:%S")
        )

        self._sessions[session_id] = {
            "session_id": session_id,
            "current_phase": 1,
            "turn_count": 0,
            "kpis": initial_kpis,
            "transcript": [initial_msg],
            "memos": initial_memos,
            "is_completed": False,
            "evaluation": None
        }

        return session_id

    def get_session(self, session_id: str) -> Optional[Dict]:
        return self._sessions.get(session_id)

    def update_session(self, session_id: str, data: Dict):
        if session_id in self._sessions:
            self._sessions[session_id].update(data)

session_store = SessionStore()
