SHELL = /bin/bash

.ONESHELL:

.PHONY: init
init:
	@python3 -m venv venv
	. venv/bin/activate
	pip install -r requirements.txt
	pre-commit install

format:
	@. .envrc
	. venv/bin/activate
	@isort -rc server/
	black server/

lint:
	@. .envrc
	. venv/bin/activate
	@flake8 server/

start:
	@. .envrc
	. venv/bin/activate
	@FLASK_ENV=development python -m server
