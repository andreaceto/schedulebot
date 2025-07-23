# Makefile

# Use bash for better scripting
SHELL := /bin/bash

# Default command is 'help'
.DEFAULT_GOAL := help

## --------------------------------------
## Application Commands
## --------------------------------------

.PHONY: run
run: ## Run the Gradio application
	@echo ">> Starting the ScheduleBOT+ application..."
	@python run_app.py

## --------------------------------------
## Docker Commands
## --------------------------------------

.PHONY: build
build: ## Build or rebuild the Docker services
	@echo ">> Building services..."
	@docker-compose build

.PHONY: up
up: ## Start backend services (like Duckling) in detached mode
	@echo ">> Starting services in the background..."
	@docker-compose up -d

.PHONY: down
down: ## Stop and remove all Docker services
	@echo ">> Stopping and removing containers..."
	@docker-compose down


## --------------------------------------
## Help
## --------------------------------------

.PHONY: help
help: ## Show this help message
	@echo "Available commands:"
	@echo ""
	@echo "  build          Build or rebuild the Docker services"
	@echo "  up             Start backend services (like Duckling) in detached mode"
	@echo "  run            Run the Gradio application"
	@echo "  down           Stop and remove all Docker services"
	@echo "  help           Show this help message"
