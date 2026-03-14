.PHONY: up down restart build logs shell cli

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose up -d --build

restart: down up

logs:
	docker compose logs -f

shell:
	docker exec -it kuda_assistant_app /bin/bash

cli:
	docker exec -it kuda_assistant_app python -m src.cli

ka:
	@if ! grep -q 'alias ka="docker exec -it kuda_assistant_app python -m src.cli"' ~/.bashrc; then \
		echo '\n# Kuda Assistant CLI alias\nalias ka="docker exec -it kuda_assistant_app python -m src.cli"' >> ~/.bashrc; \
		echo "Alias 'ka' has been added to ~/.bashrc. Please run 'source ~/.bashrc' or restart your terminal."; \
	else \
		echo "Alias 'ka' already exists in ~/.bashrc."; \
	fi
