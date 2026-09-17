# Specification: Cymbal Leadership Simulator

## Overview
The **Cymbal Leadership Simulator** is an interactive, gamified HR screening and team dynamics evaluation platform designed for Cymbal AI. Rather than relying on traditional Q&A or technical coding assessments, this system evaluates candidate leadership, empathy, crisis management, and decision-making through an immersive "team dynamics" simulation.

Candidates step into the role of an engineering manager within a modern corporate workspace dashboard ("Leadership Workspace"). Through real-time messaging, inbox memos, and dynamic KPI monitoring, candidates navigate interpersonal team conflicts, deadline crunches, and delicate employee performance reviews.

---

## 1. High-Level Architecture

### Technology Stack
- **Backend**: Python 3.10+ with **FastAPI** and Uvicorn server.
- **AI Platform**: **Gemini Enterprise Agent Platform / Google GenAI SDK** (`google-genai` / `google-generativeai`) configured with `gemini-3.6-flash` and defaulting to region `us-central1`.
- **Frontend**: Express/Node.js or static HTML5 / Vanilla CSS3 / JavaScript dashboard styled like a high-tech corporate manager workspace.
- **Communication Protocol**: Standard RESTful HTTP endpoints (`/api/start`, `/api/chat`, `/api/session/{id}`) for conversation flow, dynamic KPI metric updates, and evaluation scorecard delivery.
- **CORS Configuration**: Configured via FastAPI `CORSMiddleware` to explicitly allow local origins (`http://localhost:3002`, `http://127.0.0.1:3002`).

### High-Level Data Flow
```
 ┌─────────────────────────────────────────────────────────┐
 │             Frontend: Leadership Workspace              │
 │  ┌─────────────────┬──────────────────┬──────────────┐  │
 │  │ Communication   │  Leadership KPIs │ Inbox / Memos│  │
 │  │ Hub (Slack UI)  │  (Dynamic Gauges)│ (Context)    │  │
 │  └─────────────────┴──────────────────┴──────────────┘  │
 └───────────────┬─────────────────────────▲───────────────┘
                 │ POST /api/chat          │ JSON Response
                 ▼                         │ & Updated KPIs
 ┌─────────────────────────────────────────────────────────┐
 │                   FastAPI Backend                       │
 │      (Session Manager, KPI Engine & Router)             │
 └───────────────┬─────────────────────────┬───────────────┘
                 │                         │
     Phase 1-3   │                         │ [SIMULATION_COMPLETE]
     Prompts     ▼                         ▼ or Fail-Safe Trigger
 ┌───────────────────────────┐ ┌───────────────────────────┐
 │   Agent 1: Scenario       │ │   Agent 2: Talent         │
 │   Director & HR Coach     │ │   Evaluator               │
 │   (gemini-3.6-flash)      │ │   (gemini-3.6-flash)      │
 └───────────────────────────┘ └───────────────────────────┘
```

---

## 2. The "Leadership Workspace" UI (Visual Experience)

The frontend presents a responsive three-panel executive manager dashboard designed with modern glassmorphism, crisp typography, and high-impact data visualization:

### Panel 1: The Communication Hub (Slack-Style Chat Interface)
- **Role**: Primary interaction channel between the candidate and **Agent 1** (acting as HR Advisor & Direct Report).
- **Features**:
  - Agent header with avatar, role badge ("HR Advisor"), and status indicator ("Online").
  - Dynamic indicator showing current simulation phase (`Phase 1 of 3: Conflict Mediation`).
  - Styled chat transcript bubbles distinguishing candidate inputs from Agent responses.
  - Typing indicator during backend AI generation.
  - Interactive input field with send button and auto-expanding text box.

### Panel 2: The Leadership KPIs (Dynamic Metric Gauges)
- **Role**: Real-time visualization of team health and operational stability.
- **Metrics**:
  - 😊 **Team Morale**: Starts at **70%**. (Visual: Emerald green gauge transitions to amber/red under stress).
  - 📈 **Productivity**: Starts at **80%**. (Visual: Indigo/blue progress indicator).
  - 🔥 **Burnout Risk**: Starts at **30%**. (Visual: Sky blue transitions to high-alert orange/red).
- **Behaviors**:
  - Gauges animate smoothly whenever the backend returns updated KPI values.
  - Micro-floating tags (e.g., `+10% Morale`, `-15% Productivity`) highlight immediate impacts of candidate decisions.

### Panel 3: The Inbox / Memo Panel (Contextual Documentation)
- **Role**: Delivers background documents, urgent emails, and team files relevant to the active scenario phase.
- **Features**:
  - Interactive item list displaying unread counts and priority tags.
  - **Phase 1 Content**: Formal complaint letter from Senior Engineer Alex regarding code review conflicts with Tech Lead Morgan.
  - **Phase 2 Content**: Urgent memo from VP of Engineering highlighting a critical upcoming product launch deadline.
  - **Phase 3 Content**: Confidential performance note regarding Junior Developer Jordan's recent slipping deliverables.
  - Modal/Drawer preview allowing full reading of email text and attachments.

---

## 3. Two-Agent Simulator Setup

The core simulation is powered by two specialized AI agents executing distinct workflows:

### Agent 1: The Scenario Director & HR Coach
- **Model**: `gemini-3.6-flash`
- **Region**: `us-central1`
- **Behavior**: Guides the candidate sequentially through exactly 3 leadership phases:
  1. **Phase 1: The Dispute**
     - *Scenario*: Two core team members (Alex and Morgan) refuse to work together following an aggressive code review argument.
     - *Task*: Candidate must describe how they will mediate the conflict and re-establish collaboration.
  2. **Phase 2: The Crunch Time Dilemma**
     - *Scenario*: The product launch is 48 hours away, but the team is 2 days behind schedule.
     - *Task*: Candidate must choose a strategy:
       - *Option A (Push Hard)*: Improves Productivity (+15%), but increases Burnout Risk (+25%) and damages Morale (-15%).
       - *Option B (Request Extension)*: Protects Morale (+10%) and reduces Burnout Risk (-15%), but temporarily lowers Productivity (-10%).
       - *Option C (Hybrid/Scope Reduction)*: Balanced impact across metrics.
  3. **Phase 3: The Feedback Session**
     - *Scenario*: Address slipping performance with sensitive developer Jordan.
     - *Task*: Candidate drafts a constructive, empathetic feedback email to Jordan.
- **Termination Marker**: Upon completing Phase 3, Agent 1 appends the exact control token `[SIMULATION_COMPLETE]` at the end of its response.

### Agent 2: The Talent Evaluator
- **Model**: `gemini-3.6-flash`
- **Region**: `us-central1`
- **Behavior**: Automatically invoked when `[SIMULATION_COMPLETE]` is emitted or when fail-safe graduation triggers.
- **Evaluation Criteria**:
  - **Empathy & Active Listening** (Score 0-100)
  - **Decision-Making & Strategic Trade-offs** (Score 0-100)
  - **Communication Clarity & Constructive Tone** (Score 0-100)
  - **Team Health & Crisis Management** (Score 0-100)
- **Feedback Quality Rules**:
  - Must deliver **balanced, realistic, and uninflated evaluations**.
  - Must highlight specific flaws or missed nuances alongside strengths.
  - Must assign an overall classification: `Strong Leader`, `Developing`, or `Needs Support`.
- **JSON Scorecard Schema**:
  ```json
  {
    "candidate_rating": "Developing",
    "overall_score": 76,
    "metrics": {
      "empathy": { "score": 80, "analysis": "Demonstrated initial warmth..." },
      "decision_making": { "score": 70, "analysis": "Favored short-term output..." },
      "communication": { "score": 78, "analysis": "Feedback was clear but..." },
      "team_sustainability": { "score": 75, "analysis": "Monitored burnout adequately..." }
    },
    "key_strengths": [
      "Quick response time in mediating team tension.",
      "Empathetic tone in direct feedback communications."
    ],
    "areas_for_growth": [
      "Tended to compromise productivity during crisis moments.",
      "Could set firmer performance expectations earlier."
    ],
    "executive_summary": "The candidate shows strong potential with empathetic instincts, but requires further development in managing critical deadline trade-offs."
  }
  ```

---

## 4. State Management & KPI Logic

### Session State Schema
- `session_id`: Unique identifier (UUID).
- `current_phase`: Integer (`1`, `2`, or `3`).
- `turn_count`: Integer tracking candidate interactions.
- `kpi_values`:
  - `morale`: Float (Starts at `70.0`, clamped `0.0 - 100.0`)
  - `productivity`: Float (Starts at `80.0`, clamped `0.0 - 100.0`)
  - `burnout_risk`: Float (Starts at `30.0`, clamped `0.0 - 100.0`)
- `transcript`: List of conversation turns (`sender`, `text`, `phase`, `timestamp`).
- `is_completed`: Boolean (`True` once evaluation is finished).
- `evaluation`: Structured JSON scorecard or `null`.

### Dynamic KPI Rules Engine
- **Phase 1 Rules**:
  - High empathy / active resolution: Morale `+10`, Productivity `+5`, Burnout Risk `-5`.
  - Authoritarian / dismissive response: Morale `-15`, Productivity `-10`, Burnout Risk `+15`.
- **Phase 2 Rules**:
  - Push hard choice: Productivity `+15`, Burnout Risk `+25`, Morale `-15`.
  - Extension choice: Morale `+10`, Burnout Risk `-15`, Productivity `-10`.
  - Scope reduction / hybrid: Productivity `+5`, Morale `+5`, Burnout Risk `0`.
- **Phase 3 Rules**:
  - Constructive empathetic email: Morale `+10`, Productivity `+10`, Burnout Risk `-5`.
  - Harsh or overly blunt response: Morale `-20`, Productivity `-5`, Burnout Risk `+15`.

### Fail-Safe Graduation
- If `turn_count >= 3` and `is_completed` is still `false`, the backend automatically transitions the session to `is_completed = true` and invokes Agent 2, ensuring graceful termination even if `[SIMULATION_COMPLETE]` was omitted.

---

## 5. API Specification

### `POST /api/start`
- **Summary**: Creates a new session and returns initial KPIs and Phase 1 context.
- **Response**:
  ```json
  {
    "session_id": "c7a8b9f0-1234-5678-9abc-def012345678",
    "current_phase": 1,
    "kpis": { "morale": 70.0, "productivity": 80.0, "burnout_risk": 30.0 },
    "initial_message": "Welcome to the Cymbal Leadership Simulator! I am your HR Advisor...",
    "memos": [ ... ]
  }
  ```

### `POST /api/chat`
- **Summary**: Accepts candidate response, advances phase/turn count, calculates updated KPIs, and returns Agent 1 reply or Agent 2 scorecard.
- **Request**:
  ```json
  {
    "session_id": "c7a8b9f0-1234-5678-9abc-def012345678",
    "message": "I will bring Alex and Morgan into a 1-on-1 mediation session..."
  }
  ```
- **Response**:
  ```json
  {
    "session_id": "c7a8b9f0-1234-5678-9abc-def012345678",
    "current_phase": 2,
    "agent_message": "Thank you. Moving on to Phase 2...",
    "kpis": { "morale": 80.0, "productivity": 85.0, "burnout_risk": 25.0 },
    "kpi_deltas": { "morale": 10.0, "productivity": 5.0, "burnout_risk": -5.0 },
    "is_completed": false,
    "evaluation": null
  }
  ```

### `GET /api/session/{session_id}`
- **Summary**: Retrieves current state, history, and evaluation scorecard.

---

## 6. Scaffolding Directives

@AGY_DIRECTIVE: Build a FastAPI backend in `backend/` using Python 3, implementing endpoints `/api/start`, `/api/chat`, and `/api/session/{session_id}` powered by Gemini SDK (`gemini-3.6-flash`) defaulting to region `us-central1`.
@AGY_DIRECTIVE: Build an interactive corporate dashboard in `frontend/` featuring a Slack-style Communication Hub, dynamic KPI visual progress bars, and an Inbox/Memo panel context drawer.
@AGY_DIRECTIVE: Create a unified bash launcher script `run_local.sh` using Python 3 that installs dependencies and launches the backend on port 8000 and the frontend on port 3002 with CORS enabled.
