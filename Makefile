PYTHON = 3.12.3
PIP = pip3
SORT = isort
VIRTNAME = surfgate.app
PYENV = pyenv

setup:
	$(PYENV) virtualenv $(PYTHON) $(VIRTNAME) || true
	$(PYENV) activate $(VIRTNAME) || true
	$(PIP) install setuptools
	$(PIP) install wheel
	$(PIP) install PyYAML
	$(PIP) install -e .[dev]

activate:
	pyenv activate $(VIRTNAME)

deactivate:
	pyenv deactivate

unused:
	autoflake --recursive --in-place --remove-unused-variables --remove-all-unused-imports --recursive src/**/**/*.py

sort:
	$(SORT) src/*.py
	$(SORT) src/**/*.py
	$(SORT) src/**/**/*.py

check: unused sort
	pylama -o pylama.ini **/**/*.py

app-start:
	docker-compose -f ./scripts/development/docker-compose.yml up -d

app-stop:
	docker-compose -f ./scripts/development/docker-compose.yml down

tasks-check:
	python3 ./src/run_tasks_check.py

tasks-predicts:
	python3 ./src/run_tasks_predicts.py

tasks-notifications:
	python3 ./src/run_tasks_notifications.py

tasks-delete:
	python3 ./src/run_tasks_delete.py
