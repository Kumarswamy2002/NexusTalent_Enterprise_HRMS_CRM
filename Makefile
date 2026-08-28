.PHONY: install build run test clean lint docker-build docker-run

install:
	pip install -r requirements.txt
	npm install

build:
	python -m compileall backend/

run:
	python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload

test:
	python -m pytest tests/ -v

lint:
	python -m flake8 backend/ --max-line-length=120 || true

docker-build:
	docker build -t nexustalent:latest .

docker-run:
	docker run -p 8000:8000 nexustalent:latest

clean:
	rm -rf __pycache__ .pytest_cache
