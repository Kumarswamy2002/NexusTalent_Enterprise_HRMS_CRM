ifeq ($(OS),Windows_NT)
	VENV_PY := $(wildcard .venv/Scripts/python.exe)
else
	VENV_PY := $(wildcard .venv/bin/python)
endif
PYTHON := $(if $(VENV_PY),$(VENV_PY),python)

.PHONY: install build run test clean lint docker-build docker-run

install:
	$(PYTHON) -m pip install -r requirements.txt
	npm install

build:
	$(PYTHON) -m compileall backend/

run:
	$(PYTHON) -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload

test:
	$(PYTHON) -m pytest tests/ -v

lint:
	python -m flake8 backend/ --max-line-length=120 || true

docker-build:
	docker build -t nexustalent:latest .

docker-run:
	docker run -p 8000:8000 nexustalent:latest

clean:
	rm -rf __pycache__ .pytest_cache
