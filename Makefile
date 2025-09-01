.PHONY: run dev test lint type initdb
run:
	cd backend && ./run.sh
dev:
	uvicorn backend.app:app --reload
initdb:
	python backend/app.py --initdb
test:
	pytest -q
