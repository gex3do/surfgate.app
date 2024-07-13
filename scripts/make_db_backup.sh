#!/usr/bin/env bash

pg_dump -h localhost -U postgres --column-inserts --data-only surfgateapp > ../src/backup/surfgate.app.bak
