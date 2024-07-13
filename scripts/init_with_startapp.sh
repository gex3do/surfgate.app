#!/usr/bin/env bash

param_mode=$1

# run cron
/usr/sbin/cron

echo "Starting $param_mode environment"

python3 init.py --settings "$param_mode"

python3 synch_true_rates.py --settings "$param_mode"

python3 update_domainsearchqueries.py --settings "$param_mode"

python3 train.py --settings "$param_mode"

python3 app.py --settings "$param_mode"
