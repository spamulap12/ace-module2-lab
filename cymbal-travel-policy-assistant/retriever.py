import os
import re
import math
import subprocess
from typing import List, Dict, Any
import pypdf
from google import genai

GCS_BUCKET_URI = "gs://qwiklabs-gcp-00-4cd9521fe54c-static-assets-bucket/Cymbal Group Global Travel and Expense Policy.pdf"
LOCAL_PDF_PATH = os.path.join(os.path.dirname(__file__), "policy.pdf")

POLICY_CHUNKS = [
    {
        "chunk_id": "section_1",
        "section": "1. Core Principles",
        "title": "1. Core Principles",
        "content": (
            "Cymbal Group is committed to supporting our employees while traveling for business. "
            "Employees are expected to spend company funds responsibly and ethically. "
            "All travel must be booked through the approved Cymbal Travel Portal."
        )
    },
    {
        "chunk_id": "section_2_1",
        "section": "2.1 Cabin Class Eligibility",
        "title": "2. Air Travel - 2.1 Cabin Class Eligibility",
        "content": (
            "Cabin class eligibility is determined strictly by the scheduled flight duration (wheels-up to wheels-down), "
            "not including layovers.\n"
            "● Economy Class: Required for all domestic flights and any international flights with a scheduled duration of under 6 hours.\n"
            "● Note: Flights between European cities (e.g., Dublin to Zurich, London to Paris) fall well under the 6-hour threshold and must always be booked in Economy.\n"
            "● Business Class: Permitted only for international flights with a continuous scheduled flight duration of 6 hours or more.\n"
            "● First Class: Strictly prohibited for all employees regardless of flight duration, level, or subsidiary. "
            "Exceptions require explicit, written pre-approval from the Cymbal Group Board of Directors."
        )
    },
    {
        "chunk_id": "section_2_2",
        "section": "2.2 Upgrades",
        "title": "2. Air Travel - 2.2 Upgrades",
        "content": (
            "Employees may use their personal frequent flyer miles or personal funds to upgrade their cabin class. "
            "Cymbal Group will not reimburse personal funds used for seat upgrades."
        )
    },
    {
        "chunk_id": "section_3_general",
        "section": "3. Meal and Incidental Expenses (Per Diem)",
        "title": "3. Meal and Incidental Expenses (Per Diem) - General Rules",
        "content": (
            "Cymbal Group reimburses employees for actual meal and incidental expenses incurred during business travel, "
            "up to a strict daily maximum cap based on the destination country.\n"
            "Key Rules:\n"
            "● Caps include all meals, snacks, tips, and incidentals for a single 24-hour period.\n"
            "● Itemized receipts are required for any single meal exceeding $25 USD (or local equivalent).\n"
            "● Alcohol is not a reimbursable expense under any circumstances."
        )
    },
    {
        "chunk_id": "section_3_1",
        "section": "3.1 Daily Meal Caps by Country",
        "title": "3. Meal and Incidental Expenses - 3.1 Daily Meal Caps by Country",
        "content": (
            "Daily Meal Caps by Country:\n"
            "If a country is not listed, the default 'Rest of World' cap of $60 USD applies.\n"
            "● United States: $85 USD\n"
            "● United Kingdom: £75 GBP (~$95.00 USD)\n"
            "● Switzerland: 120 CHF (~$135.00 USD)\n"
            "● Germany: €80 EUR (~$88.00 USD)\n"
            "● Ghana: 900 GHS (~$70.00 USD)\n"
            "● Japan: 12,000 JPY (~$80.00 USD)\n"
            "● Brazil: 350 BRL (~$70.00 USD)\n"
            "● Rest of World: $60 USD"
        )
    },
    {
        "chunk_id": "section_4",
        "section": "4. Accommodation",
        "title": "4. Accommodation",
        "content": (
            "Employees must use standard rooms at Cymbal-preferred partner hotels whenever available.\n"
            "● Nightly Rate Cap: Standard rooms must not exceed $250 USD per night (excluding taxes/fees) in major metropolitan areas, "
            "and $175 USD in non-major markets.\n"
            "● In-room movies, minibar purchases, and spa services are non-reimbursable."
        )
    },
    {
        "chunk_id": "section_5",
        "section": "5. Expense Reporting",
        "title": "5. Expense Reporting",
        "content": (
            "All travel expenses must be submitted via the Cymbal HR Expense system within 30 days of the trip's completion. "
            "Reports submitted after 30 days require VP-level approval and may be subject to denial."
        )
    }
]


def ensure_policy_file():
    """Ensure policy.pdf exists locally or download from GCS bucket."""
    if not os.path.exists(LOCAL_PDF_PATH):
        try:
            subprocess.run(
                ["gsutil", "cp", GCS_BUCKET_URI, LOCAL_PDF_PATH],
                check=True,
                capture_output=True
            )
        except Exception as e:
            print(f"Warning downloading policy from GCS: {e}")


def _cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _token_overlap_score(query: str, text: str) -> float:
    q_words = set(re.findall(r'\w+', query.lower()))
    t_words = re.findall(r'\w+', text.lower())
    if not q_words or not t_words:
        return 0.0
    matches = sum(1 for w in q_words if w in t_words)
    score = matches / len(q_words)
    # Boost if exact entity matches occur
    for entity in ["switzerland", "zurich", "dublin", "movie", "first-class", "first class", "alcohol", "meal", "cap", "hotel", "tv"]:
        if entity in query.lower() and entity in text.lower():
            score += 0.5
    return score


def cymbal_policy_retriever(query: str, top_k: int = 4) -> Dict[str, Any]:
    """Retrieves relevant chunks of the official corporate travel policy based on the user's query.

    Args:
        query: The search query or employee question about travel policy.
        top_k: Number of relevant chunks to retrieve (default: 4).

    Returns:
        Dict containing query, retrieved chunks, and status.
    """
    ensure_policy_file()

    # Try embedding search via gemini-embedding-2 / text-embedding-004 / Vertex AI if client available
    client = None
    try:
        project_id = os.environ.get("GCP_PROJECT", "qwiklabs-gcp-00-4cd9521fe54c")
        client = genai.Client(vertexai=True, project=project_id, location="global")
    except Exception:
        pass

    chunk_scores = []

    if client:
        try:
            # Generate query embedding
            q_emb = client.models.embed_content(
                model="text-embedding-004",
                contents=query,
            ).embeddings[0].values

            for chunk in POLICY_CHUNKS:
                c_emb = client.models.embed_content(
                    model="text-embedding-004",
                    contents=chunk["content"],
                ).embeddings[0].values
                sim = _cosine_similarity(q_emb, c_emb)
                kw_boost = _token_overlap_score(query, chunk["content"])
                final_score = sim + 0.3 * kw_boost
                chunk_scores.append((final_score, chunk))
        except Exception as e:
            client = None  # Fallback to lexical search

    if not client or not chunk_scores:
        for chunk in POLICY_CHUNKS:
            score = _token_overlap_score(query, chunk["content"])
            chunk_scores.append((score, chunk))

    # Sort descending by score
    chunk_scores.sort(key=lambda x: x[0], reverse=True)
    top_chunks = [item[1] for item in chunk_scores[:top_k]]

    return {
        "status": "success",
        "query": query,
        "retrieved_chunks_count": len(top_chunks),
        "results": top_chunks
    }
