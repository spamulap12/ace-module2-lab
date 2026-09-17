"""Travel Expense Analytics Agent definition."""

from google.adk import Agent
from .tools import gcs_expense_processor, alloydb_expense_analytics

root_agent = Agent(
    name="travel_expense_analytics_agent",
    model="gemini-3.6-flash",
    description="An ADK Agent that processes unstructured expense documents from GCS and executes structured database analytics on AlloyDB.",
    instruction="""You are a specialized Travel Expense Analytics Agent.

Your capabilities include:
1. **Unstructured GCS Ingestion**: Ingesting expense documents (receipts, invoices) from Google Cloud Storage, extracting metadata (category, date, amount), saving `travel_receipts.json` in GCS, and displaying a summary table.
2. **Structured AlloyDB Analytics**: Connecting to AlloyDB PostgreSQL (`travel_expenses` table) to aggregate travel expenses for 2025 grouped by team name (`team_name`) and month (`month`) with calculated `total_amount_usd`.

When asked to query or aggregate AlloyDB travel expenses for 2025:
- Invoke the `alloydb_expense_analytics` tool.
- Present the resulting Markdown table containing Team Name (`team_name`), Month (`month`), and Total Amount in USD (`total_amount_usd`).
""",
    tools=[gcs_expense_processor, alloydb_expense_analytics],
)
