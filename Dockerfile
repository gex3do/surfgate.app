FROM ubuntu
MAINTAINER Dmitry Sagoyan, contact@surfgate.app

ARG param_mode

ENV DEBIAN_FRONTEND noninteractive
ENV param_mode=${param_mode}

# ubuntu setup
RUN apt-get clean && apt-get update -y && apt-get upgrade -y
RUN apt-get install -y --no-install-recommends apt-utils
RUN apt-get install -y iputils-ping && apt-get install -y net-tools

RUN apt-get install -y python3-setuptools && apt-get install -y python3-wheel
RUN apt-get install -y python3 && apt-get install -y python3-pip

RUN apt-get -y install cron

# Used by selenium (see class WebDriveScrapper)
RUN apt-get -y install chromium-chromedriver
RUN apt-get -y install firefox-geckodriver

# Copy the current directory contents into the container at /app
COPY . /app
WORKDIR /app

RUN pip3 install -e .

########################################
###### CRON CONFIG
########################################

# Add crontab file in the cron directory
ADD ./envs/${param_mode}/crontab /etc/cron.d/surfgateapp-cron

# Give execution rights on the cron job
RUN chmod 755 /etc/cron.d/surfgateapp-cron

# Apply cron job
RUN crontab /etc/cron.d/surfgateapp-cron

# Create the log file to be able to run tail
RUN touch /var/log/cron.log
########################################

RUN service cron start

# Make port 443 and 5000 available to the world outside this container
EXPOSE 443:5000
EXPOSE 80:5000

WORKDIR /app/src/

CMD ./init_with_startapp.sh ${param_mode}
