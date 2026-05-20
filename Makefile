.PHONY: install run test generate deploy setup-cloudflare tunnel

PYTHON ?= python3
VENV := .venv
BIN := $(VENV)/bin

install:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install -r requirements.txt

run:
	$(BIN)/python -m bot

test:
	./scripts/test-webhook.sh

generate:
	$(BIN)/python scripts/generate_worker_config.py

deploy:
	cd worker && npm install && npx wrangler deploy

setup-cloudflare:
	./scripts/setup-cloudflare.sh

tunnel:
	cloudflared tunnel --url http://localhost:8080
