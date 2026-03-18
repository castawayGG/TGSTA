FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir -e "."

COPY . .

# Create data directory
RUN mkdir -p /app/data

# Run migrations then start the bot
CMD ["sh", "-c", "alembic upgrade head && python -m app.bot"]
