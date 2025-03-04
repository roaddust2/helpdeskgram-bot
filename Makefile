ENV=poetry run

# Util commands

lint:
	$(ENV) flake8

test:
	$(ENV) pytest

test-coverage:
	$(ENV) coverage run -m pytest tests
	$(ENV) coverage report --omit=*/tests/*
	$(ENV) coverage xml --omit=*/tests/*

requirements.txt: 
	poetry export --without-hashes --no-cache --output=requirements.txt

i18n-update:
	$(ENV) pybabel extract --input-dirs=. -o locales/messages.pot
	$(ENV) pybabel update -i locales/messages.pot -d locales -D messages

i18n-compile:
	$(ENV) pybabel compile -d locales -D messages


# Main commands (Poetry)

setup:
	poetry install

start:
	$(ENV) python3 -m app.main