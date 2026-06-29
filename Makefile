.PHONY: install install-dev run test cov lint fmt fmt-check build up down logs tf-init tf-plan tf-fmt clean

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

run:
	FLASK_APP=app.main flask run --host=0.0.0.0 --port=5000

test:
	pytest -v

cov:
	pytest --cov=app --cov-report=term-missing --cov-fail-under=85

lint:
	flake8 app tests
	black --check app tests
	isort --check-only app tests

fmt:
	black app tests
	isort app tests

build:
	docker build -t aws-cicd-pipeline-demo:local .

up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f api

tf-init:
	cd terraform && terraform init

tf-plan:
	cd terraform && terraform plan

tf-fmt:
	cd terraform && terraform fmt -recursive

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .coverage htmlcov
