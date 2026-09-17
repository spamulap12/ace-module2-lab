FROM python:3.12-slim

WORKDIR /code

# Copy requirements and install via standard pip
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY main.py ./
COPY travel_policy_agent/ ./travel_policy_agent/

# Expose port
EXPOSE 8080

# Run FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
