.PHONY: install format test build

install:
	poetry install

format:
	poetry run black src tests

test:
	poetry run pytest

build:
	docker build -t opsguard-ai .
