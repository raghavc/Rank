.PHONY: up down logs migrate revision worker-shell api-shell ios test

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f api worker beat

migrate:
	docker compose exec api alembic upgrade head

revision:
	docker compose exec api alembic revision --autogenerate -m "$(m)"

api-shell:
	docker compose exec api bash

worker-shell:
	docker compose exec worker bash

test:
	docker compose exec api pytest -q

ios:
	open RichRank.xcodeproj
