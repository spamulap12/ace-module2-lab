import os
import json
import logging
from typing import List, Dict, Any, Tuple, Optional
from models import Message, KPIValues

logger = logging.getLogger("gemini_agents")

# Try importing google.genai
try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False
    logger.warning("google-genai SDK not available, falling back to dynamic simulated AI responses.")

AGENT1_SYSTEM_INSTRUCTION = """
You are Agent 1, the Scenario Director & HR Coach for Cymbal AI's Leadership Simulator.
Your role is to guide an engineering manager candidate through exactly 3 sequential leadership phases:

Phase 1 (The Dispute):
- Alex (Senior Engineer) and Morgan (Tech Lead) are in an intense conflict over code reviews and refusing to collaborate.
- Ask the candidate how they plan to mediate this interpersonal conflict.

Phase 2 (The Crunch Time Dilemma):
- The critical Cymbal AI product launch is 48 hours away, but the team is 2 days behind schedule.
- Ask the candidate whether they will push the team harder, request a deadline extension from leadership, or reduce project scope.

Phase 3 (The Feedback Session):
- Junior Developer Jordan's work quality is slipping and missing deadlines due to stress.
- Ask the candidate to draft a direct, constructive feedback message to Jordan.

Goal & Rule:
- Be realistic, professional, and observant like a senior HR Director at Cymbal AI.
- When the candidate submits their final response for Phase 3, you MUST conclude the simulation and append the exact token string [SIMULATION_COMPLETE] at the very end of your response.
""".strip()

AGENT2_SYSTEM_INSTRUCTION = """
You are Agent 2, the Talent Evaluator for Cymbal AI.
Your job is to rigorously review the candidate's chat transcript and final team KPIs (Morale, Productivity, Burnout Risk) across the 3 leadership phases.

Evaluate against the standard Cymbal AI HR Leadership Rubric:
1. Empathy & Active Listening (0-100)
2. Decision-Making & Strategic Trade-offs (0-100)
3. Communication Clarity & Tone (0-100)
4. Team Sustainability & Crisis Management (0-100)

CRITICAL INSTRUCTION:
Do NOT produce overly positive or inflated evaluations. Give an honest, balanced, and constructive rating (`Strong Leader`, `Developing`, or `Needs Support`). Identify real operational flaws, trade-off blind spots, and communication weaknesses alongside strengths.

Return ONLY a valid JSON object matching this schema:
{
  "candidate_rating": "Strong Leader" | "Developing" | "Needs Support",
  "overall_score": 75,
  "metrics": {
    "empathy": { "score": 80, "analysis": "Detailed critique..." },
    "decision_making": { "score": 70, "analysis": "Detailed critique..." },
    "communication": { "score": 75, "analysis": "Detailed critique..." },
    "team_sustainability": { "score": 75, "analysis": "Detailed critique..." }
  },
  "key_strengths": ["Strength 1", "Strength 2"],
  "areas_for_growth": ["Growth Area 1", "Growth Area 2"],
  "executive_summary": "Comprehensive 2-3 sentence executive assessment."
}
""".strip()

def get_genai_client():
    if not HAS_GENAI:
        return None
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None
    try:
        return genai.Client(api_key=api_key)
    except Exception as e:
        logger.warning(f"Failed to initialize GenAI Client: {e}")
        return None

async def call_agent_1(
    current_phase: int,
    candidate_message: str,
    transcript: List[Message],
    kpis: KPIValues
) -> Tuple[str, int, bool]:
    """
    Returns: (agent_message, new_phase, is_completed_flag)
    """
    client = get_genai_client()
    
    # Target next phase
    next_phase = min(3, current_phase + 1) if current_phase < 3 else 3
    is_completed = (current_phase == 3)
    
    if client:
        try:
            # Build conversation history prompt
            prompt_history = "\n".join([f"{m.sender.upper()}: {m.text}" for m in transcript])
            full_prompt = f"""
Current Phase: {current_phase}
Current Team KPIs: Morale={kpis.morale}%, Productivity={kpis.productivity}%, Burnout Risk={kpis.burnout_risk}%

Conversation History:
{prompt_history}

Candidate's Latest Input:
{candidate_message}

Instruction:
Respond as Agent 1 (HR Advisor). 
If candidate just completed Phase 1 response, transition to Phase 2 (Crunch Time Dilemma).
If candidate completed Phase 2 response, transition to Phase 3 (Feedback Session for Jordan).
If candidate completed Phase 3 response, conclude gracefully and end your output with [SIMULATION_COMPLETE].
""".strip()

            models_to_try = ["gemini-3.6-flash", "gemini-2.5-flash", "gemini-1.5-flash"]
            response_text = None
            for model_name in models_to_try:
                try:
                    res = client.models.generate_content(
                        model=model_name,
                        contents=full_prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=AGENT1_SYSTEM_INSTRUCTION,
                            temperature=0.7
                        )
                    )
                    if res and res.text:
                        response_text = res.text
                        break
                except Exception as ex:
                    logger.info(f"Model {model_name} invocation failed: {ex}")
            
            if response_text:
                has_token = "[SIMULATION_COMPLETE]" in response_text
                return response_text, next_phase, (has_token or is_completed)
        except Exception as e:
            logger.error(f"Error calling Gemini API for Agent 1: {e}")
            
    # Fallback response generator if Gemini API key not present or call fails
    return generate_fallback_agent_1_response(current_phase, candidate_message, kpis)

def generate_fallback_agent_1_response(phase: int, message: str, kpis: KPIValues) -> Tuple[str, int, bool]:
    msg_len = len(message.strip())
    
    if phase == 1:
        text = (
            f"Thank you for that thoughtful response on mediating the Alex & Morgan conflict. "
            f"Your approach demonstrates clear intent to restore collaboration. "
            f"As a result, Team Morale is now at {kpis.morale}% and Productivity stands at {kpis.productivity}%.\n\n"
            f"--- **Phase 2: The Crunch Time Dilemma** ---\n"
            f"We have a new crisis. The flagship Cymbal AI product launch is scheduled in 48 hours, but our technical team is currently 2 days behind schedule due to the earlier conflict.\n\n"
            f"As the Engineering Manager, you face a critical dilemma:\n"
            f"1. **Push the team harder**: Mandate overtime to hit the original deadline (Increases Productivity, but spikes Burnout Risk & hurts Morale).\n"
            f"2. **Request an extension**: Ask executive leadership for a 3-day launch delay (Protects Morale & Burnout, but temporarily hurts Productivity).\n"
            f"3. **Scope reduction**: Cut non-essential features for a phased rollout.\n\n"
            f"How will you navigate this decision with your team and executive stakeholders?"
        )
        return text, 2, False
        
    elif phase == 2:
        text = (
            f"Understood. Your decision regarding the launch deadline has been communicated to the team and VP of Engineering. "
            f"Our metrics reflect the trade-off: Morale is at {kpis.morale}%, Productivity is at {kpis.productivity}%, and Burnout Risk is at {kpis.burnout_risk}%.\n\n"
            f"--- **Phase 3: The Feedback Session** ---\n"
            f"We have reached our final leadership challenge. Junior Developer Jordan has been struggling over the past sprint—missing deliverables and showing signs of withdrawal following the crunch period.\n\n"
            f"Please draft a constructive feedback email or message to Jordan that addresses performance expectations while maintaining empathy and psychological safety."
        )
        return text, 3, False
        
    else: # phase == 3
        text = (
            f"Thank you for drafting that message to Jordan. You structured the feedback with clear intent, setting actionable expectations while acknowledging employee context. "
            f"This concludes our 3-phase leadership simulation.\n\n"
            f"I am now handing over the full transcript and team dynamics metrics to **Agent 2 (Talent Evaluator)** for final evaluation.\n\n"
            f"[SIMULATION_COMPLETE]"
        )
        return text, 3, True


async def call_agent_2(
    transcript: List[Message],
    kpis: KPIValues
) -> Dict[str, Any]:
    client = get_genai_client()
    
    if client:
        try:
            prompt_history = "\n".join([f"Phase {m.phase} - {m.sender.upper()}: {m.text}" for m in transcript])
            full_prompt = f"""
Final Simulation Metrics:
- Morale: {kpis.morale}%
- Productivity: {kpis.productivity}%
- Burnout Risk: {kpis.burnout_risk}%

Candidate Transcript across 3 Phases:
{prompt_history}

Please review this candidate according to the Cymbal AI Leadership Rubric and return ONLY a valid JSON object matching the requested schema. Ensure the evaluation is balanced and not overly positive.
""".strip()

            models_to_try = ["gemini-3.6-flash", "gemini-2.5-flash", "gemini-1.5-flash"]
            for model_name in models_to_try:
                try:
                    res = client.models.generate_content(
                        model=model_name,
                        contents=full_prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=AGENT2_SYSTEM_INSTRUCTION,
                            response_mime_type="application/json",
                            temperature=0.3
                        )
                    )
                    if res and res.text:
                        parsed = json.loads(res.text)
                        return parsed
                except Exception as ex:
                    logger.info(f"Agent 2 model {model_name} failed: {ex}")
        except Exception as e:
            logger.error(f"Error calling Gemini API for Agent 2: {e}")
            
    # Fallback evaluation generator if Gemini API key not present or call fails
    return generate_fallback_agent_2_evaluation(transcript, kpis)

def generate_fallback_agent_2_evaluation(transcript: List[Message], kpis: KPIValues) -> Dict[str, Any]:
    # Analyze candidate text depth & KPI results to produce a balanced, non-inflated scorecard
    candidate_msgs = [m.text for m in transcript if m.sender == "user"]
    total_words = sum(len(m.split()) for m in candidate_msgs)
    
    # Calculate balanced scores
    empathy_score = int(min(90, max(50, round(kpis.morale * 0.8 + (100 - kpis.burnout_risk) * 0.2))))
    decision_score = int(min(90, max(55, round(kpis.productivity * 0.7 + kpis.morale * 0.3))))
    comm_score = int(min(92, max(60, 65 + min(25, total_words // 10))))
    sustain_score = int(min(90, max(50, round((100 - kpis.burnout_risk) * 0.6 + kpis.morale * 0.4))))
    
    overall = int(round((empathy_score + decision_score + comm_score + sustain_score) / 4))
    
    if overall >= 82:
        rating = "Strong Leader"
    elif overall >= 68:
        rating = "Developing"
    else:
        rating = "Needs Support"
        
    return {
        "candidate_rating": rating,
        "overall_score": overall,
        "metrics": {
            "empathy": {
                "score": empathy_score,
                "analysis": f"Demonstrated willingness to listen during mediation (Phase 1). Managed to keep team morale at {kpis.morale}%."
            },
            "decision_making": {
                "score": decision_score,
                "analysis": f"Handled deadline pressure with pragmatic trade-offs, holding productivity at {kpis.productivity}%."
            },
            "communication": {
                "score": comm_score,
                "analysis": "Articulated choices clearly in chat, though direct feedback in Phase 3 could benefit from firmer performance benchmarks."
            },
            "team_sustainability": {
                "score": sustain_score,
                "analysis": f"Maintained burnout risk at {kpis.burnout_risk}%. Showed awareness of team stress during crunch time."
            }
        },
        "key_strengths": [
            "Proactive conflict mediation approach in Phase 1.",
            "Strong focus on team psychological safety and open dialogue."
        ],
        "areas_for_growth": [
            "Could establish clearer quantitative milestones when managing delayed project timelines.",
            "Feedback delivery in Phase 3 tended toward high empathy but needed stronger accountability metrics."
        ],
        "executive_summary": f"The candidate demonstrated a solid '{rating}' profile. They exhibited genuine empathetic instincts and conflict resolution skills, but could further sharpen executive trade-off decision-making during high-pressure crunch periods."
    }
