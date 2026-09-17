# Lab Guide: Deploying Cymbal Travel Policy Agent to Agent Engine & Gemini Enterprise

This lab guide walks you through the step-by-step process of downloading, refactoring, deploying, and registering the **Cymbal Group Travel Policy Concierge** agent to the Google Cloud Agent Engine (GEAP) and exposing it through the **Gemini Enterprise Application** chat interface.

---

## 📋 Scenario Overview

> [!NOTE]
> **Context**: In the previous lab (**Lab 3.1**), we created and configured the travel policy agent using `spec.md`. In this lab (**Lab 3.2**), we are going to deploy that exact agent onto the **Gemini Enterprise Agent Platform's Agent Engine** using Antigravity.

In this lab, you will:
1.  Set up an Antigravity project folder and prepare the starting package (`travel_policy_agent`) created during Lab 3.1.
2.  Leverage the pre-packaged `agents-cli` deployment skill.
3.  Package, dockerize, and deploy the agent onto the cloud-managed **Agent Engine** runtime.
4.  Test the live deployed cloud API.
5.  Create a **Gemini Enterprise App** named `Cymbal HR Policy Concierge` and register your Agent Engine backend to it.
6.  Perform end-to-end user verification within the enterprise portal interface.

---

## 🗺️ Lab Steps

### Step 1: Navigate to the Provided Starting Directory

In this lab, you are provided with the `travel_policy_agent` directory as your starting point (created during Lab 3.1). You will use this folder directly to run and deploy the agent.

1.  **Navigate to your starting folder** inside your workspace:
    ```bash
    cd ~/travel_policy_agent
    ```
2.  **Verify workspace contents**: Make sure the following files are present in the folder:
    *   `main.py` — FastAPI application serving the agent API
    *   `__init__.py` — Package initialization file containing the `root_agent` logic
    *   `corporate_travel_policy.txt` — The official corporate travel guidelines grounding context
    *   `pyproject.toml` — Python package dependencies

---

### Step 2: Leverage the Pre-packaged `agents-cli` Skill

The custom **`agents-cli` deployment skill** is already pre-packaged directly inside your starting project folder under `skills/agents-cli/`. 

Because it is already in your workspace, you do not need to perform any manual copy operations. Antigravity running in your environment automatically discovers and uses local skills located inside your project folder to execute target platform tasks.

---

### Step 3: Deploy the Agent to Agent Engine

With the `agents-cli` skill ready, trigger the cloud packaging and deployment.

*   **Prompt to Antigravity:**
    ```text
    /goal Scaffold and deploy our local Travel Policy Agent on Agent Engine using the agents-cli skill.
    Use PyPi packages to install agents-cli and google-adk.

    - Context: The application entrypoint is main.py, which imports the core agent from the travel_policy_agent/ subdirectory.
    - Target: Deploy to Vertex AI Agent Engine (agent_runtime) in us-central1.
    - Setup Steps: 
      1. Authenticate with Google Cloud using 'gcloud auth login' and 'gcloud auth application-default login'.
      2. Compile 'pyproject.toml' into a standard 'requirements.txt' via 'uv pip compile'. Bootstrap the workspace with 'agents-cli-manifest.yaml' and configure a lightweight Dockerfile that copies and installs requirements.txt cleanly via standard pip.
      3. Deploy the package using 'agents-cli deploy'. 

    *Note: If you need my GCP Project ID, stop and ask me directly.*
    ```

> [!NOTE]
> **What Antigravity is doing under the hood:**
> During the execution of this `/goal` prompt, the Antigravity coding agent autonomously performs the following optimized dependency compilation and containerization steps on your behalf:
> 
> 1. **Dependency Compilation**: It compiles your `pyproject.toml` configuration into a flat, production-ready `requirements.txt` via `uv pip compile`.
> 2. **Standard Dockerfile Structuring**: It generates or adjusts the project's `Dockerfile` to copy and install this compiled `requirements.txt` cleanly with standard `pip`:
>    ```dockerfile
>    FROM python:3.12-slim
>    WORKDIR /code
>    COPY requirements.txt ./
>    COPY ./app ./app
>    RUN pip install --no-cache-dir -r requirements.txt
>    EXPOSE 8080
>    CMD ["uvicorn", "app.fast_api_app:app", "--host", "0.0.0.0", "--port", "8080"]
>    ```
> 3. **Friction-Free Public Builds**: Because our dependencies reside on public PyPI, Vertex AI Cloud Build can retrieve and compile packages natively with zero authentication issues, eliminating the need for private keys or registry credentials!

---

### Step 4: Test Agent Engine Deployment

Verify that your deployed backend is running, accessible, and properly grounded.

*   **Prompt to Antigravity:**
    ```text
    /goal Test our live deployed Travel Policy Agent using these three compliance scenarios:

    1. Swiss Meal Allowance: Ask "What is the meal cap for Switzerland?" ➜ Expect the agent to retrieve Section 3.1 and return "120 CHF".
    2. Flight Policy: Ask "Can I book a first-class flight from Dublin to Zurich?" ➜ Expect the agent to retrieve Section 2.1 to deny it (no First-Class for flights under 6 hours).
    3. Hotel Entertainment: Ask "Can I buy a movie on the hotel TV?" ➜ Expect the agent to retrieve Section 4 and mark it as non-reimbursable.

    Output a clean Pass/Fail markdown table showing the agent's live response for each query.
    ```

---

### Step 5: Create the Gemini Enterprise App

Set up the parent Enterprise Application layer inside Google Cloud Console.

*   **Prompt to Antigravity:**
    ```text
    /goal Create a new Gemini Enterprise App named 'Cymbal HR Policy Concierge' in my active GCP project.
    ```

---

### Step 6: Register the Policy Agent to the App

Map your newly deployed reasoning engine directly into the Gemini Enterprise Application.

*   **Prompt to Antigravity:**
    ```text
    /goal Register our Travel Policy Agent (deployed on Agent Engine) to the 'Cymbal HR Policy Concierge' Gemini Enterprise App using the local agents-cli skill.
    ```

---

### Step 7: End-to-End Enterprise UI Testing

Examine the end-user experience from the cloud interface.

*   **Prompt to Antigravity:**
    ```text
    /goal Query our live 'Cymbal HR Policy Concierge' Gemini Enterprise App API to verify it is routing queries to our backend agent correctly.

    1. Generate an OAuth token with 'gcloud auth print-access-token'.
    2. Programmatically test the same three queries (Switzerland meal cap, Dublin flight restriction, hotel movie) through the live Enterprise App API.
    3. Output the raw JSON responses to confirm routing and grounding are functional.
    ```

---

### 🖥️ Manual Gemini Enterprise UI Testing

Once you complete registration, verify the user experience manually:
1.  **Open the App UI**: Go to Google Cloud Console ➜ **Gemini Enterprise** ➜ click on **Cymbal HR Policy Concierge**.
2.  **Enable Web Access**: Ensure the Web App toggle switch is flipped **On** within the engine overview layout.
3.  **Launch Chat Portal**: Copy and click the shared workspace link. This brings up the managed enterprise chat interface.
4.  **Invoke and Validate**: Locate **Cymbal HR Policy Concierge** under the left-side *Agents* sidebar menu. Test the following prompts directly in the chat window:
    - 🧪 `"What is the meal cap for Switzerland?"` ➜ Confirm it extracts the **120 CHF** constraint.
    - 🧪 `"Can I buy a movie on the hotel TV?"` ➜ Confirm it flags it as **non-reimbursable**.

---

### ⚠️ Troubleshooting: Quota & Subscription Tier Limitations
If you run `agents-cli publish gemini-enterprise` and encounter the following error:
```json
Error: Error during ADK registration: 400 Client Error: Bad Request...
Invalid subscription tier for build agents quota: SUBSCRIPTION_TIER_UNSPECIFIED
```
This is a standard platform guardrail. Google Cloud's **Gemini Enterprise** requires a paid subscription tier in your active billing account to provision the automated web hooks that link custom backend agents to the console UI. 

If you encounter this:
1. Confirm your deployed Reasoning Engine endpoint is healthy by querying it directly via `agents-cli run --url ...` (as documented in **Step 4**).
2. Report the success of the backend deployment and direct query validation to your lab instructor, as the backend logic has been fully deployed and verified.
