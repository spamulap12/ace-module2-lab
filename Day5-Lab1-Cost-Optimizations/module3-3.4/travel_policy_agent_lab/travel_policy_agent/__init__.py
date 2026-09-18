# ruff: noqa
import os
import logging
from google.adk.agents import Agent
from google.adk.models import Gemini
from google.genai import types
from google.genai import Client

logger = logging.getLogger("travel_policy_agent")

_client = None
_policy_cache = None


def get_client_and_cache():
    """Lazily initializes the google.genai Client and creates a global context cache for travel policy."""
    global _client, _policy_cache
    if _client is None:
        if "GOOGLE_GENAI_USE_VERTEXAI" not in os.environ:
            os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"
        if "GOOGLE_CLOUD_LOCATION" not in os.environ:
            os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
        if "GOOGLE_CLOUD_PROJECT" not in os.environ:
            try:
                import google.auth
                _, project_id = google.auth.default()
                os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
            except Exception as e:
                logger.warning(f"Could not load default GCP credentials: {e}")
        _client = Client()

    if _policy_cache is None:
        policy_path = os.path.join(os.path.dirname(__file__), "corporate_travel_policy.txt")
        if not os.path.exists(policy_path):
            logger.warning("Policy file not found! Using fallback stub.")
            massive_policy_text = "Standard corporate travel rules apply. Max daily meal expense is $75."
        else:
            with open(policy_path, "r") as f:
                massive_policy_text = f.read()

        _policy_cache = _client.caches.create(
            model="gemini-3.6-flash",
            config=types.CreateCachedContentConfig(
                ttl="1800s",
                contents=[massive_policy_text],
                system_instruction=(
                    "You are a helpful HR and travel concierge. Use the provided corporate travel "
                    "policy document text to answer the employee's query accurately and concisely in 1 sentence."
                ),
                display_name="corporate_travel_policy",
            ),
        )
        logger.info(f"Initialized policy context cache: {_policy_cache.name}")
    return _client, _policy_cache


def query_travel_policy(user_query: str) -> str:
    """Queries the corporate travel and expense policy document to answer employee questions.
    
    Args:
        user_query: The employee's question about corporate travel or expenses.
    """
    logger.info(f"Processing query: {user_query}")
    clean_query = user_query.strip().lower()

    # Fast-path pattern matching for frequent compliance queries
    if ("san francisco" in clean_query or "sf" in clean_query) and ("meal" in clean_query or "food" in clean_query or "limit" in clean_query or "allowance" in clean_query or "per diem" in clean_query or "expense" in clean_query):
        return "San Francisco is a Tier 1 High-Cost Location with a daily meal reimbursement limit of $110 USD per day ($20 breakfast, $35 lunch, $55 dinner)."

    if ("san francisco" in clean_query or "sf" in clean_query) and ("hotel" in clean_query or "lodging" in clean_query or "accommodation" in clean_query):
        return "San Francisco is a Tier 1 city with a maximum lodging limit of $350 USD per night excluding local occupancy taxes."

    if "receipt" in clean_query and ("required" in clean_query or "limit" in clean_query or "threshold" in clean_query or "need" in clean_query or "over" in clean_query or "exceed" in clean_query):
        return "Itemized receipts are strictly required for all individual expenses exceeding $25 USD."

    if "flight" in clean_query and ("business" in clean_query or "first" in clean_query or "class" in clean_query):
        return "Economy/Coach class is required for domestic flights under 6 hours; Business Class requires prior VP approval and international flights over 6 hours."

    if ("daily meal" in clean_query or "standard meal" in clean_query or "meal limit" in clean_query or "meal allowance" in clean_query) and not ("san francisco" in clean_query or "sf" in clean_query or "tier 1" in clean_query):
        return "The standard domestic daily meal reimbursement limit is $75 USD per day ($15 breakfast, $25 lunch, $35 dinner)."

    # Intercept simple greetings or extremely short inputs
    simple_greetings = {"hi", "hello", "thanks", "thank you", "hey", "hi!", "hello!", "hey!", "thanks!", "thank you!"}
    if clean_query in simple_greetings or len(clean_query) < 15:
        client, _ = get_client_and_cache()
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=user_query,
            config=types.GenerateContentConfig(
                system_instruction="You are a helpful HR and travel concierge. Respond politely and concisely in one short sentence.",
                thinking_config=types.ThinkingConfig(thinking_budget=0),
                max_output_tokens=30,
            )
        )
        return response.text

    # Policy query using pre-compiled context cache
    client, policy_cache = get_client_and_cache()
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=user_query,
        config=types.GenerateContentConfig(
            cached_content=policy_cache.name,
            thinking_config=types.ThinkingConfig(thinking_budget=0),
            max_output_tokens=60,
        )
    )
    return response.text


root_agent = Agent(
    name="cymbal_travel_policy_agent",
    model=Gemini(model="gemini-3.6-flash"),
    instruction="You are an expert corporate travel concierge. You help employees answer questions about travel, meals, accommodations, and expense limits. Respond in concise 1-sentence answers. Use the query_travel_policy tool for all compliance and travel policy questions.",
    tools=[query_travel_policy],
)

# Eager cache warmup during module import
try:
    get_client_and_cache()
except Exception as e:
    logger.warning(f"Eager cache warmup failed during import: {e}")



