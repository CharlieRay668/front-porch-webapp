APP_NAME=volunteer-app
PORT?=8000

.PHONY: help build run stop logs shell clean db-reset

help:
	@echo "Targets:"
	@echo "  build        Build Docker image"
	@echo "  run          Run container (port $(PORT))"
	@echo "  stop         Stop container"
	@echo "  logs         Tail logs"
	@echo "  shell        Shell into running container"
	@echo "  clean        Remove image and container"
	@echo "  db-reset     Drop and recreate local SQLite DB (host)"

build:
	docker build -t $(APP_NAME) .

run:
	docker run --name $(APP_NAME) -p $(PORT):8000 -v "$(shell pwd)/app:/app/app" -d $(APP_NAME) uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

stop:
	- docker stop $(APP_NAME) 2>/dev/null || true
	- docker rm $(APP_NAME) 2>/dev/null || true

logs:
	docker logs -f $(APP_NAME)

shell:
	docker exec -it $(APP_NAME) /bin/sh

clean: stop
	- docker rmi $(APP_NAME) 2>/dev/null || true

# Local DB reset (host machine)
db-reset:
	rm -f app/volunteers.db
	.venv/bin/python -c "from sqlmodel import SQLModel, create_engine; import os; p='app/volunteers.db'; os.makedirs('app', exist_ok=True); e=create_engine(f'sqlite:///{p}', connect_args={'check_same_thread': False}); SQLModel.metadata.create_all(e)"
	@echo "Database reset at app/volunteers.db"

run-no-docker:
	venv/bin/python -m uvicorn app.main:app --reload
