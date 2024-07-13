#!/usr/bin/env bash

sudo docker build --no-cache -t surfgate.app:development --build-arg param_mode=development .
