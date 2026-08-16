FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ensure data directory exists for the SQLite database
RUN mkdir -p /app/data

# The specific startup command is provided in docker-compose.yml
CMD ["bash"]
