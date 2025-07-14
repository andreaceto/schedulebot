# Makefile

# Use bash for better scripting
SHELL := /bin/bash

# Default command is 'help'
.DEFAULT_GOAL := help

## --------------------------------------
## Docker Commands
## --------------------------------------

.PHONY: build
build: ## 🛠️  Build or rebuild the Docker services
	@echo ">> Building services..."
	@docker-compose build

.PHONY: up
up: ## 🚀 Start all services in detached mode
	@echo ">> Starting services in the background..."
	@docker-compose up -d

.PHONY: down
down: ## 🛑 Stop and remove all services
	@echo ">> Stopping and removing containers..."
	@docker-compose down

.PHONY: logs
logs: ## 📜 View real-time logs for all services
	@echo ">> Tailing logs (press Ctrl+C to stop)..."
	@docker-compose logs -f

.PHONY: test
test: ## 🧪 Run pytest inside the app container
	@echo ">> Running tests..."
	@docker-compose run --rm app pytest

## --------------------------------------
## Help
## --------------------------------------

.PHONY: help
help: ## 🙋 Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_-LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
