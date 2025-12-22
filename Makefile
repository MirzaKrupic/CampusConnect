.PHONY: help build up down logs clean test seed health docs

help:
	@echo "CampusConnect - Polyglot Persistence Demo"
	@echo ""
	@echo "Available commands:"
	@echo "  make build     - Build all Docker containers"
	@echo "  make up        - Start all services (databases + backend)"
	@echo "  make down      - Stop all services"
	@echo "  make logs      - Tail logs from all services"
	@echo "  make clean     - Stop services and remove volumes (DELETE ALL DATA)"
	@echo "  make test      - Run unit tests"
	@echo "  make seed      - Re-run seed script (populate demo data)"
	@echo "  make health    - Check health of all services"
	@echo "  make docs      - Open API documentation in browser"
	@echo ""

build:
	docker-compose build

up:
	@echo "Starting all services..."
	docker-compose up -d
	@echo ""
	@echo "Services are starting up. Wait 30-60 seconds for health checks."
	@echo "Check status with: make health"
	@echo "View logs with: make logs"
	@echo ""
	@echo "Once ready, access:"
	@echo "  - API: http://localhost:8000"
	@echo "  - API Docs: http://localhost:8000/docs"
	@echo "  - Neo4j Browser: http://localhost:7474 (neo4j/campus_pass_123)"

down:
	docker-compose down

logs:
	docker-compose logs -f

clean:
	@echo "WARNING: This will delete all data in volumes!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v; \
		echo "All services stopped and volumes removed."; \
	fi

test:
	docker exec -it campusconnect-backend pytest backend/tests/test_services.py -v

seed:
	docker exec -it campusconnect-backend python /app/docker/init/seed.py

health:
	@curl -s http://localhost:8000/health | python -m json.tool

docs:
	@echo "Opening API docs..."
	@command -v open >/dev/null 2>&1 && open http://localhost:8000/docs || \
	 command -v xdg-open >/dev/null 2>&1 && xdg-open http://localhost:8000/docs || \
	 echo "Please open http://localhost:8000/docs in your browser"
