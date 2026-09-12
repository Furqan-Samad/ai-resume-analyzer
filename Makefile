.PHONY: install-backend install-frontend run-backend run-frontend test docker-up docker-down

install-backend:
	pip install -r backend/requirements.txt -r requirements-dev.txt

install-frontend:
	pip install -r frontend/requirements.txt

run-backend:
	uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

run-frontend:
	streamlit run frontend/app.py

test:
	pytest tests/ -v

docker-up:
	docker compose up --build

docker-down:
	docker compose down
