import json
import asyncio
import os
import sys
import time
import uuid
import pandas as pd

import vertexai
import google.auth
from google.cloud import aiplatform
from google.cloud.aiplatform.metadata.metadata_store import _MetadataStore
from google.cloud.aiplatform.compat.types import execution_v1 as gca_execution_compat
from vertexai.evaluation import EvalTask, MetricPromptTemplateExamples, PointwiseMetric

# Set environment variables for Vertex AI Gemini API access
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "true"
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"

# Discover project ID
credentials, project_id = google.auth.default()
if not project_id:
    project_id = "qwiklabs-gcp-00-fa85aa96fe4d"
os.environ["GOOGLE_CLOUD_PROJECT"] = project_id

# 1. Initialize Vertex AI in region us-central1
REGION = "us-central1"
print(f"Initializing Vertex AI in region {REGION} for project {project_id}...")
vertexai.init(project=project_id, location=REGION)
aiplatform.init(project=project_id, location=REGION)

# 2. Ensure default Vertex AI Metadata Store is created
print("Ensuring default Vertex AI Metadata Store exists...")
_MetadataStore.ensure_default_metadata_store_exists(project=project_id, location=REGION)

# Add travel_policy_agent package directory to python path
agent_dir = os.path.join(os.path.dirname(__file__), "travel_policy_agent")
if agent_dir not in sys.path:
    sys.path.insert(0, agent_dir)

from travel_policy_agent.agent import root_agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.genai import types

# 3. Load Policy Context and evaluation.json test cases
policy_path = os.path.join(agent_dir, "travel_policy_agent", "corporate_travel_policy.txt")
with open(policy_path, "r") as f:
    policy_context = f.read()

eval_json_path = os.path.join(os.path.dirname(__file__), "evaluation.json")
with open(eval_json_path, "r") as f:
    eval_json = json.load(f)

test_cases = eval_json["test_cases"]
print(f"Loaded {len(test_cases)} test cases from evaluation.json")

# 4. Generate responses from cymbal_travel_policy_agent
async def get_agent_response(query: str) -> str:
    session_service = InMemorySessionService()
    runner = Runner(
        agent=root_agent,
        session_service=session_service,
        auto_create_session=True,
        app_name="cymbal_policy_concierge"
    )
    message = types.Content(role="user", parts=[types.Part(text=query)])
    response_text = ""
    async for event in runner.run_async(
        new_message=message,
        user_id="eval_user",
        session_id=f"eval_session_{abs(hash(query))}",
        run_config=RunConfig(streaming_mode=StreamingMode.NONE)
    ):
        if event.content and event.content.parts and event.author != "user":
            for part in event.content.parts:
                if part.text:
                    response_text += part.text
    return response_text

print("\nExecuting agent queries...")
prompts = []
responses = []
references = []
contexts = []
instructions = []

for tc in test_cases:
    q = tc["query"]
    gt = tc["ground_truth"]
    inst = tc.get("evaluation_instructions", "")
    print(f"- Query: {q}")
    resp = asyncio.run(get_agent_response(q))
    print(f"  Agent Answer: {resp[:120]}...\n")
    prompts.append(q)
    responses.append(resp)
    references.append(gt)
    contexts.append(policy_context)
    instructions.append(inst)

eval_df = pd.DataFrame({
    "prompt": prompts,
    "response": responses,
    "reference": references,
    "context": contexts,
    "instruction": instructions
})

# 5. Define Evaluation Metrics
groundedness_metric = PointwiseMetric(
    metric="groundedness",
    metric_prompt_template=MetricPromptTemplateExamples.Pointwise.GROUNDEDNESS
)

safety_metric = PointwiseMetric(
    metric="safety",
    metric_prompt_template=MetricPromptTemplateExamples.Pointwise.SAFETY
)

fulfillment_prompt = """
Evaluate whether the model response fulfills the user instruction and query based on the reference ground truth.

Instruction: {instruction}
Query: {prompt}
Response: {response}
Reference: {reference}

Assign a fulfillment score from 1 to 5, where 5 means completely fulfilled and 1 means unfulfilled.

Return format:
Explanation: <explanation>
Score: <score>
"""

fulfillment_metric = PointwiseMetric(
    metric="fulfillment",
    metric_prompt_template=fulfillment_prompt
)

# 6. Create and run EvalTask under experiment cymbal-travel-policy-eval
EXPERIMENT_NAME = "cymbal-travel-policy-eval"
RUN_NAME = f"cymbal-travel-policy-run-{int(time.time())}"

print(f"Creating EvalTask under experiment '{EXPERIMENT_NAME}'...")
eval_task = EvalTask(
    dataset=eval_df,
    metrics=[groundedness_metric, safety_metric, fulfillment_metric],
    experiment=EXPERIMENT_NAME
)

print(f"Running EvalTask.evaluate for run '{RUN_NAME}'...")
eval_result = eval_task.evaluate(
    experiment_run_name=RUN_NAME
)

# Ensure run state is finalized as COMPLETE
exp_run = aiplatform.ExperimentRun(RUN_NAME, experiment=EXPERIMENT_NAME)
exp_run.end_run(state=aiplatform.gapic.Execution.State.COMPLETE)

# 7. Print and verify evaluation summary and MetadataStore status
print("\n=== Evaluation Completed Successfully ===")
print("Summary Metrics:", eval_result.summary_metrics)

final_run = aiplatform.ExperimentRun(RUN_NAME, experiment=EXPERIMENT_NAME)
final_state_name = gca_execution_compat.Execution.State(final_run.state).name
print(f"MetadataStore Experiment Context Run '{RUN_NAME}' State: {final_state_name}")
assert final_state_name == "COMPLETE", f"Expected COMPLETE state, got {final_state_name}"
print("Verification complete: Experiment context registered in Vertex AI MetadataStore and reached COMPLETE state.")
