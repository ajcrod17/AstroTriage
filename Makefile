.PHONY: up down logs clean restart

# Starts the containers in the background and builds them
up:
	docker compose up --build -d
	@echo "🚀 AstroTriage API running at: http://localhost:8000"
	@echo "📊 Dashboard running at: http://localhost:8501"

# Stops the containers
down:
	docker compose down

# Tails the logs of both containers
logs:
	docker compose logs -f

# Stops containers and removes the database volume to start completely fresh
clean: down
	@echo "🧹 Cleaning up database state..."
	docker run --rm -v "$$(pwd)/data:/data" python:3.11-slim bash -c "rm -rf /data/*"
	@echo "✨ Database wiped. Run 'make up' to start fresh."

# Restarts the environment fresh
restart: clean up