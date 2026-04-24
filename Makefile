.PHONY: install run clean shell lint test

install:
	poetry install

run:
	poetry run python pipeline.py $(ARGS)


clean:
	rm -rf __pycache__
	rm -rf .pytest_cache
	find . -type f -name "*.pyc" -delete

shell:
	@echo "Starting shell in poetry environment..."
	@poetry run $$SHELL


test:
	poetry run python -m pytest
