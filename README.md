#  Project surfgate.app

### Install postgres 

sudo apt-get install postgresql postgresql-contrib
sudo apt-get install postgresql-client

### Initialize project 

Setups data for database and start analysing `true_rate` resources.

```shell
python3 init.py
```

### Train model

```shell
python3 train.py
```

### Synchronize True Predictions from /data to database

```shell
python3 synch_true_rates.py
```

### Update domain search queries 

```shell
python3 update_domainsearchqueries.py
```

# Start the webservice

```shell
python3 app.py
```

### Build PRODUCTION

1. Checkout/Create candidate branch
2. Merge in candidate branch feature branches or master branch
3. Run ./build_production inside of candidate branch
    a) Creates the image tag with "name:version" should be surfgate.app:"$@"
4. After finishing check if surfgate.app:production exists using "docker image ls"

### Make DB backup

```shell
pg_dump -h 192.168.1.55 -U postgres --column-inserts --data-only surfgateapp > backup/surfgate.app.bak 
pg_dump -h 192.168.1.55 -U postgres --column-inserts --data-only --table public.users surfgateapp > backup/surfgate1.app.bak
```

### Jobs
1. python3 run_tasks_check.py
   - Collects links per page and stores them zipped under tasks
   - No features are extracted, only the links are collected

2. python3 run_tasks_predicts.py
   - Restores from zipped json -> pure json and gets through all possible pages (page include link) to predict it regarding the model

3. python3 run_tasks_notifications.py
   - When the task is predicted, it notifies using given return_url that the task is finished and can be requested by task_uuid

4. python3 run_tasks_delete.py

-----------------
Each job can be run many times parallel.

### SOME SQL HELPS
- update tasks set status = 'check' , data = '', notified = 0, maxdepth=0;
- select uuid, val, status, maxdepth, notified, notification_done from tasks;
- tail -f /var/log/cron.log

### Preparations

```shell
mkdir logs
> logs/app.log
```

### Synchronize true_rate regarding the resources from sources

The script 'synch_true_rates.py' calls resource_mgr.read_resources_from_file(sess, file_path, True)
with 'True' which means update the database resource 'true_rate' 
