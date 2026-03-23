FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (layer cached unless requirements change)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy package and source
COPY pyproject.toml ./
COPY src/ ./src/

# Install the package itself (no deps, already installed above)
RUN pip install --no-cache-dir --no-deps -e .

EXPOSE 8000

CMD ["uvicorn", "hotel_agent.main:app", "--host", "0.0.0.0", "--port", "8000"]
