run:
	uvicorn workout_api.main:app --reload

create-migrations:
	alembic revision --autogenerate -m d="init db"

run-migrations:
	alembic upgrade head