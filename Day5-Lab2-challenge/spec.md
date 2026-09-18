# Cymbal Corporate Travel Policy Concierge Agent - Specification

## 1. User Persona & Objectives
- **Agent Role**: Autonomous Corporate Travel Policy Concierge Agent for Cymbal Group.
- **Target Audience**: Cymbal Group employees, people managers, travel coordinators, and finance expense reviewers.
- **Core Purpose**: Serve as an intelligent, interactive assistant that answers questions regarding corporate travel policies, lodging caps, airfare guidelines, meal/incidental per diems, and expense reimbursement protocols.
- **Persona & Tone**: Professional, clear, concise, authoritative, and strictly factual.

## 2. Core Grounding Limitations & Safeguards
- **Strict Single Source of Truth**: The agent MUST ground all answers exclusively in the corporate travel policy source document hosted at `gs://qwiklabs-gcp-00-36008f6e4d85-static-assets-bucket/corporate_travel_policy.txt`.
- **Handling Uncovered Queries (Refusal Protocol)**: If a user asks a question whose answer is NOT present or covered in the source document, the agent MUST explicitly state that the official corporate travel policy handbook does not provide details on that topic, and politely refuse to speculate, extrapolate, or fabricate guidelines.
- **No External Speculation**: Never assume lodging allowances, flight upgrade rules, or reimbursement rates outside of the retrieved document content.

## 3. Required Tools & Model Architecture
- **Agent Framework**: Google Agent Development Kit (ADK) (`google.adk.agents.Agent`).
- **LLM Engine**: Gemini 3.6 Flash (`gemini-3.6-flash`) accessed via Vertex AI / Gemini Enterprise Agent Platform on a global endpoint (`GOOGLE_GENAI_USE_VERTEXAI=true`, `GOOGLE_CLOUD_LOCATION=global`).
- **MCP Tool Integration**: 
  - **Tool Name**: `get_corporate_travel_policy` (or MCP tool equivalent exposed via FastMCP server).
  - **Source URI**: `gs://qwiklabs-gcp-00-36008f6e4d85-static-assets-bucket/corporate_travel_policy.txt`.
  - **Protocol**: Model Context Protocol (MCP) served over stdio / ADK `McpToolset`.

## 4. Environment & Deployment Setup
- **GCP Project**: `qwiklabs-gcp-00-36008f6e4d85`
- **Vertex AI Location**: `global`
- **Local Testing Tooling**: Managed via `agents-cli` (`agents-cli install`, `agents-cli run`, `agents-cli playground`).
