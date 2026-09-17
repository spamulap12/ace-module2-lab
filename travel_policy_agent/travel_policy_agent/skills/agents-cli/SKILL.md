---
name: agents-cli
description: "Deploy, register, and manage AI agents on Google Cloud and Gemini Enterprise using agents-cli. Use this skill when deploying agents to Agent Engine (Agent Runtime), registering them in the Agent Registry, or exposing them to Gemini Enterprise (GE) Apps."
---

# Agents CLI (`agents-cli`) Skill

`agents-cli` is Google's official command-line interface designed to streamline the **Agent Development Lifecycle (ADLC)** on Google Cloud. It enables developer automation (and agentic automation) for scaffolding, testing, evaluating, deploying, and publishing AI agents built with the **Agent Development Kit (ADK)**.

## 🔗 Official Documentation & Code References
*   **Official GitHub Repository (CLI Download):** [https://github.com/google/agents-cli](https://github.com/google/agents-cli)
*   **Official Deployment Guide & Command Reference:** [https://google.github.io/agents-cli/guide/deployment/](https://google.github.io/agents-cli/guide/deployment/)

---

## 1. Concepts & Architecture

*   **Agent Engine (Agent Runtime):** A fully managed, stateful/stateless runtime hosted on Google Cloud for running AI agents without container management (under the hood, this uses Google Cloud Vertex AI's `ReasoningEngine`).
*   **Agent Registry:** A centralized catalog on the Gemini Enterprise platform that acts as the single source of truth for discovered, governed, and managed enterprise agents.
*   **GE App (Gemini Enterprise Application):** The end-user interface or system of workflows that consumes agents from the Agent Registry, exposing them directly to enterprise employees.
*   **ADK Core Components:**
    *   **Tools:** Standard Python functions that agents can run (e.g. `get_weather`, `get_current_time`).
    *   **Model:** Powered by Gemini 3.6 Flash.
    *   **App / root_agent:** The main entry point `App` wrapping a `root_agent` that exposes the agent capabilities.

---

## 2. Configuration Files

An `agents-cli` project relies on these primary configuration files:

### 2.1 `pyproject.toml`
Manages the Python environment, packages, metadata, and dependencies (including `google-adk`).

```toml
[project]
name = "travel-policy-agent"
version = "1.0.0"
description = "Cymbal Group Travel Policy Concierge"
dependencies = [
    "google-adk>=1.0.0",
    "fastapi>=0.100.0",
    "uvicorn>=0.20.0",
]
```

### 2.2 `agents-cli-manifest.yaml`
Manages deployment, environment, and orchestration metadata separately from Python dependencies.

```yaml
name: travel-policy-agent
agent_directory: travel_policy_agent/
deployment_target: agent_runtime   # Targets Agent Engine / Agent Runtime
session_type: in_memory
create_params:
  deployment_target: agent_runtime
  runtime_version: python311
```

### 2.3 `deployment_metadata.json`
Generated during deployment to keep track of the cloud resource IDs, particularly `remote_agent_runtime_id`.

---

## 3. Step-by-Step Lifecycle & Deployment Workflow

### Step 1: Install and Initialize `agents-cli`
Install the global CLI tool and the context-aware skills.

```bash
# Install global skills and agents-cli using uvx
uvx google-agents-cli setup

# Alternatively, for manual command line control
uv tool install google-agents-cli

# Verify installation
agents-cli --version
```

### Step 2: Authenticate and Set Up Environment
Configure local credentials and select your active Google Cloud project.

```bash
# Authenticate with Google Cloud
gcloud auth login
gcloud auth application-default login

# Enable required Google Cloud APIs
gcloud services enable aiplatform.googleapis.com \
  run.googleapis.com \
  cloudtrace.googleapis.com \
  cloudbuild.googleapis.com

# Set Environment Variables
export GOOGLE_CLOUD_PROJECT="YOUR_PROJECT_ID"
export GOOGLE_CLOUD_LOCATION="us-central1"
```

### Step 2.5: Provision Cloud Infrastructure with `infra`

Before deploying the agent code, you must provision the underlying Google Cloud infrastructure (IAM service accounts, API configurations, and telemetry buckets). `agents-cli` automates this process.

```bash
# Provision core cloud infrastructure resources (optional)
agents-cli infra single-project --project YOUR_PROJECT_ID --apply
```

> [!NOTE]
> `agents-cli infra` deploys a secure, enterprise-grade foundation (including least-privilege IAM service accounts) so your agent can execute securely in production.

### Step 3: Scaffold or Enhance the Agent Project
Create a new project from a prototype template, or enhance an existing project to target Agent Runtime.

```bash
# Option A: Scaffold a new prototype project instantly
agents-cli scaffold create travel-policy-agent --prototype --yes
cd travel-policy-agent

# Option B: Enhance an existing project to target Agent Engine / Agent Runtime
agents-cli scaffold enhance --deployment-target agent_runtime --yes
```

### Step 4: Install Dependencies and Test Locally
Resolve local environment requirements and start testing.

```bash
# Install dependencies into local .venv using uv sync
agents-cli install

# Start the interactive local playground (runs on http://127.0.0.1:8080/dev-ui/?app=app)
# This includes hot reload: changes to app/agent.py are picked up instantly
agents-cli playground

# Test directly from the command line
agents-cli run "What is the meal allowance cap in Switzerland?"

# Stop the background API server
agents-cli run --stop-server
```

### Step 5: Run Automated Quality Evaluations
Evaluate the agent on two distinct dimensions: **Tool Trajectory** (deterministic exact matches) and **Response Quality** (LLM-as-a-judge score).

1.  **Define evaluation cases** in `tests/eval/evalsets/basic.evalset.json`:
    ```json
    {
      "eval_set_id": "basic_eval",
      "name": "Basic Agent Evaluation",
      "eval_cases": [
        {
          "eval_id": "swiss_meal_cap",
          "conversation": [
            {
              "user_content": { "parts": [{"text": "What is the meal cap for Switzerland?"}], "role": "user" },
              "intermediate_data": {
                "tool_uses": [{"name": "cymbal_policy_retriever", "args": {"query": "Switzerland meal cap"}}]
              }
            }
          ]
        }
      ]
    }
    ```
2.  **Define evaluation criteria** in `tests/eval/eval_config.json`:
    ```json
    {
      "criteria": {
        "tool_trajectory_avg_score": 1.0,
        "rubric_based_final_response_quality_v1": {
          "threshold": 0.8,
          "judgeModelOptions": {"judgeModel": "gemini-3.6-flash"},
          "rubrics": [
            {"rubricId": "relevance", "rubricContent": {"textProperty": "The response directly addresses the user's query."}},
            {"rubricId": "tool_grounded", "rubricContent": {"textProperty": "The response is grounded in values returned by tools."}}
          ]
        }
      }
    }
    ```
3.  **Run evaluations:**
    ```bash
    agents-cli eval run --all
    ```

### Step 6: Deploy to Agent Runtime / Agent Engine
Upload and host your agent on Google Cloud's fully-managed Serverless Agent Runtime.

```bash
# Update and lock dependencies
uv lock

# Deploy the agent (Note: if using private packages, pass credentials as build argument)
TOKEN=$(gcloud auth application-default print-access-token)
agents-cli deploy --project YOUR_PROJECT_ID --region us-central1 --build-args UV_HTTP_BASIC_US_PYTHON_PKG_DEV="oauth2accesstoken:$TOKEN"

# (Optional) Verify status of deployment
agents-cli deploy --status
```
*This packages the agent, provisions managed infrastructure (4 CPU, 8Gi memory, auto-scaling 1-10 instances), and registers the agent on Google Cloud.*

> [!WARNING]
> **Authenticating Private Repositories during Cloud Container Build**:
> If your project depends on private registries (e.g. `artifact-foundry-prod`), ensure your `Dockerfile` includes `ARG UV_HTTP_BASIC_US_PYTHON_PKG_DEV` before the `RUN uv sync --frozen` line, and pass the token as a build argument (`--build-args UV_HTTP_BASIC_US_PYTHON_PKG_DEV="oauth2accesstoken:$TOKEN"`) in your deploy command.


### Step 7: Test the Deployed Agent
You can interact with your deployed agent in three ways:

*   **Console Playground (Interactive UI):**
    Open the link provided in the deploy output:
    `https://console.cloud.google.com/vertex-ai/agents/agent-engines/locations/<REGION>/agent-engines/<RUNTIME_ID>/playground?project=<PROJECT_ID>`
*   **CLI command:**
    ```bash
    RUNTIME_ID=$(jq -r .remote_agent_runtime_id deployment_metadata.json)
    agents-cli run \
      --url "https://us-central1-aiplatform.googleapis.com/v1/${RUNTIME_ID}" \
      --mode adk \
      "What is the meal allowance cap in Switzerland?"
    ```
*   **Python SDK (Programmatic):**
    ```python
    import vertexai
    from vertexai import agent_engines

    vertexai.init(project="YOUR_PROJECT_ID", location="us-central1")
    remote_agent = agent_engines.get("projects/YOUR_PROJECT_ID/locations/us-central1/reasoningEngines/YOUR_RUNTIME_ID")
    session = remote_agent.create_session(user_id="user-1")
    for event in remote_agent.stream_query(user_id="user-1", session_id=session["id"], message="What's the weather?"):
        print(event)
    ```

### Step 8: Monitor Deployed Agent
Observability is automatically provisioned and enabled:
*   **Cloud Trace:** Open *Trace Explorer* in the Cloud Console and filter by attribute `service.name = your-agent-name` to drill into end-to-end latency, model inference, and tool calls.
*   **Cloud Logging:** Open *Logs Explorer* and use the query:
    `resource.type="aiplatform.googleapis.com/ReasoningEngine" AND resource.labels.reasoning_engine_id="YOUR_RUNTIME_ID"`
*   **Cloud Monitoring:** Go to *Metrics Explorer* and monitor `request_count`, `request_latencies`, and `instance_count`.

### Step 9: Register the Agent in the Agent Registry (Publish to Gemini Enterprise)
Publish the deployed agent to make it discoverable in the Gemini Enterprise Agent Marketplace and expose it to the GE App.

```bash
# List Gemini Enterprise apps in your project to identify targets
agents-cli publish gemini-enterprise --list

# Register the deployed agent (auto-reads the Runtime ID)
agents-cli publish gemini-enterprise \
  --gemini-enterprise-app-id "projects/PROJECT_NUMBER/locations/global/collections/default_collection/engines/YOUR_APP_ID" \
  --display-name "Cymbal HR Policy Concierge" \
  --description "Cymbal Group corporate travel and expense policy concierge" \
  --tool-description "Use this tool to ask the travel policy concierge." \
  --interactive
```
*This command binds the backend runtime URL to the Gemini Enterprise orchestration layer, authorizing and making it visible in GE Apps.*

---

## 4. Cleaning Up Resources

To avoid recurring charges on Google Cloud when testing is complete, delete the deployed agent:

Using the **gcloud CLI** (Recommended):
```bash
# Extract the runtime ID and trigger deletion
RUNTIME_ID=$(jq -r .remote_agent_runtime_id deployment_metadata.json)
gcloud ai reasoning-engines delete "${RUNTIME_ID}" --region="us-central1"
```

Using the **direct REST API** (Alternative):
```bash
# Extract the runtime ID and trigger deletion via curl/REST API
RUNTIME_ID=$(jq -r .remote_agent_runtime_id deployment_metadata.json)
curl -X DELETE \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  "https://us-central1-aiplatform.googleapis.com/v1beta1/${RUNTIME_ID}?force=true"
```
*Note: Specifying `force=true` ensures any child active conversation sessions are also cleaned up.*
