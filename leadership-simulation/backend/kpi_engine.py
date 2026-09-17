from models import KPIValues, KPIDeltas

def calculate_kpi_updates(current_phase: int, candidate_message: str, current_kpis: KPIValues) -> tuple[KPIValues, KPIDeltas]:
    msg_lower = candidate_message.lower()
    
    delta_morale = 0.0
    delta_prod = 0.0
    delta_burnout = 0.0
    
    if current_phase == 1:
        # Dispute Mediation Phase
        empathetic_keywords = ["mediate", "1-on-1", "listen", "collaborate", "compromise", "align", "empathy", "discuss", "understand", "both sides", "coaching", "psychological safety"]
        harsh_keywords = ["fire", "replace", "ignore", "force", "mandate", "demand", "demote", "pick side", "ultimatum", "blame"]
        
        has_empathy = any(kw in msg_lower for kw in empathetic_keywords)
        has_harsh = any(kw in msg_lower for kw in harsh_keywords)
        
        if has_harsh:
            delta_morale = -15.0
            delta_prod = -10.0
            delta_burnout = 15.0
        elif has_empathy or len(candidate_message.split()) > 15:
            delta_morale = 10.0
            delta_prod = 5.0
            delta_burnout = -5.0
        else:
            delta_morale = 5.0
            delta_prod = 2.0
            delta_burnout = -2.0

    elif current_phase == 2:
        # Crunch Time Dilemma Phase
        push_keywords = ["push", "crunch", "overtime", "work late", "weekend", "strict deadline", "hit date", "deliver at all costs", "no delay"]
        extension_keywords = ["extension", "delay", "push back", "negotiate time", "ask vp", "postpone", "more time"]
        scope_keywords = ["scope", "cut features", "mvp", "phase release", "prioritize", "de-scope", "tradeoff", "stagger"]
        
        has_push = any(kw in msg_lower for kw in push_keywords)
        has_extension = any(kw in msg_lower for kw in extension_keywords)
        has_scope = any(kw in msg_lower for kw in scope_keywords)
        
        if has_push and not has_scope:
            delta_prod = 15.0
            delta_burnout = 25.0
            delta_morale = -15.0
        elif has_extension:
            delta_morale = 10.0
            delta_burnout = -15.0
            delta_prod = -10.0
        elif has_scope or (has_push and has_extension):
            delta_prod = 5.0
            delta_morale = 5.0
            delta_burnout = 0.0
        else:
            delta_prod = 5.0
            delta_morale = 2.0
            delta_burnout = 5.0

    elif current_phase == 3:
        # Feedback Session Phase
        supportive_keywords = ["support", "growth", "coaching", "help", "expectations", "empathetic", "constructive", "resources", "pair", "feedback", "check-in"]
        punitive_keywords = ["fire", "written warning", "pip", "unacceptable", "terminate", "fail", "blame", "dismiss"]
        
        has_support = any(kw in msg_lower for kw in supportive_keywords)
        has_punitive = any(kw in msg_lower for kw in punitive_keywords)
        
        if has_punitive:
            delta_morale = -20.0
            delta_prod = -5.0
            delta_burnout = 15.0
        elif has_support or len(candidate_message.split()) > 12:
            delta_morale = 10.0
            delta_prod = 10.0
            delta_burnout = -5.0
        else:
            delta_morale = 5.0
            delta_prod = 5.0
            delta_burnout = 0.0

    # Calculate new values clamped strictly to [0.0, 100.0]
    new_morale = max(0.0, min(100.0, round(current_kpis.morale + delta_morale, 1)))
    new_prod = max(0.0, min(100.0, round(current_productivity_with_delta(current_kpis.productivity, delta_prod), 1)))
    new_burnout = max(0.0, min(100.0, round(current_kpis.burnout_risk + delta_burnout, 1)))
    
    updated_kpis = KPIValues(
        morale=new_morale,
        productivity=new_prod,
        burnout_risk=new_burnout
    )
    
    deltas = KPIDeltas(
        morale=delta_morale,
        productivity=delta_prod,
        burnout_risk=delta_burnout
    )
    
    return updated_kpis, deltas

def current_productivity_with_delta(current_prod: float, delta_prod: float) -> float:
    return current_prod + delta_prod
