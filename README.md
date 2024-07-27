# surfgate.app

The `surfgate.app` API offers you to perform actions such as evaluating `potential content violation rates` (PCVR) and 
retrieving already evaluated rates. You can connect to using your `API` license key.

## Run project using local setup

To set up the project within `python environment`, you can use one of the listed options:

- `venv`
  - The [venv](https://docs.python.org/3/library/venv.html) module provides support for creating lightweight "virtual environments" with their own site directories, optionally isolated from system site directories.
- `pyenv`
  - The [pyenv](https://github.com/pyenv/pyenv) is a tool for managing multiple Python versions. 

We prefer to use `pyenv`. Please be sure you have installed it before running

```shell
make setup
```

### Bootstrap database

Setups `data` into database and start analysing process of `true-rate` resources.

```shell
make init
```

### Train

Trains model against `true-rate` resources with a status  

```shell
make train
```

# Start the webservice

```shell
python3 app.py
```


## Run project using docker compose

This command runs the application and the `postgres` database in containers.

```shell
make start-app
```
