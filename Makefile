PYTHON = 3.12.3
PIP = pip3
SORT = isort
VIRTNAME = surfgate.app
PYENV = pyenv
AUTOFLAKE = autoflake
PYLAMA = pylama

PYLIST = src/*.py src/**/*.py src/**/**/*.py

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
	for i in $(PYLIST); do \
	  $(AUTOFLAKE) --recursive --in-place --remove-unused-variables --remove-all-unused-imports --recursive $$i; \
	done

sort:
	for i in $(PYLIST); do \
	  $(SORT) $$i; \
	done

check: unused sort
	for i in $(PYLIST); do \
	  $(PYLAMA) -o pylama.ini $$i; \
	done

start-app:
	# starts postgres + webserver (currently only postgres)
	docker-compose -f ./scripts/development/docker-compose.yml up -d

stop-app:
	docker-compose -f ./scripts/development/docker-compose.yml down

init:
	python3 ./src/init.py

train:
	python3 ./src/train.py

app:
	python3 ./src/app.py

tasks-check:
	python3 ./src/run_tasks_check.py

tasks-predicts:
	python3 ./src/run_tasks_predicts.py

tasks-notifications:
	python3 ./src/run_tasks_notifications.py

tasks-delete:
	python3 ./src/run_tasks_delete.py

sync:
	python3 ./src/sync_true_rates.py
