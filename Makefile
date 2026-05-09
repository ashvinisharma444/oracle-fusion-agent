.PHONY: setup dev build test docker-up docker-down migrate ingest-knowledge clean

# Setup development environment
setup:
	@echo "Setting up Oracle Fusion AI Diagnostic Agent..."
	cp .env.example .env
	cd backend && pip install -r requirements.txt
	cd backend && playwright install chromium --with-deps
	cd frontend && npm install
	@echo "✓ Setup complete. Edit .env with your credentials."

# Start development servers
dev:
	@echo "Starting development servers..."
	cd infrastructure && docker compose up postgres redis chromadb -d
	cd backend && uvicorn app.main:app --reload --port 8000 &
	cd frontend && npm run dev &
	@echo "✓ Backend: http://localhost:8000/docs | Frontend: http://localhost:3000"

# Docker full stack
docker-up:
	cd infrastructure && docker compose up --build -d
	@echo "✓ Stack running. Frontend: http://localhost:3000 | API: http://localhost:8000"

docker-down:
	cd infrastructure && docker compose down

docker-logs:
	cd infrastructure && docker compose logs -f backend

# Database migrations
migrate:
	psql $(DATABASE_URL) -f backend/app/infrastructure/database/migrations/001_initial.sql
	@echo "✓ Database schema applied"

# Ingest sample Oracle knowledge base
ingest-knowledge:
	cd scripts && python ingest_knowledge.py
	@echo "✓ Knowledge base seeded"

# Run tests
test:
	cd backend && pytest tests/ -v --tb=short

# Build production images
build:
	docker build -t oracle-fusion-agent-backend:latest backend/
	docker build -t oracle-fusion-agent-frontend:latest frontend/

# Deploy to Kubernetes
k8s-deploy:
	kubectl apply -f infrastructure/kubernetes/namespace.yaml
	kubectl apply -f infrastructure/kubernetes/configmap.yaml
	kubectl apply -f infrastructure/kubernetes/backend-deployment.yaml
	kubectl apply -f infrastructure/kubernetes/ingress.yaml
	@echo "✓ Deployed to Kubernetes"

clean:
	cd infrastructure && docker compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .next -exec rm -rf {} + 2>/dev/null || true
