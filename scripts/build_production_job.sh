#!/usr/bin/env bash

sudo docker build --no-cache -t surfgate.app:"$@" --build-arg param_mode=production .