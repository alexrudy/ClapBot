# ClapBot
Craigslist Apartment Bot

## Architecture
Clapbot has several components:

- A web front-end (web/flask.debug) powered by Flask
- A task worker (celery.worker), powered by Celery
- A task management and monitoring tool (celery.flower)
- A task scheduler (celery.beat)
- A database (db) powered by postgresql for recording entries.
- A key-value store (redis) for managing tasks.

The web front-end is the primary interaction route. You will also need the task backend running to do any of the scraping, scoring and downloading of crigslist data. These are all managed through docker-compose, set up in the `docker-compose.yml` file. The `scripts/dc` script will help you call docker compose with the right arguments and the right overrides.

## Configuration

Configuration setups go in a `./config/{NAME}/` folder in the application root. To select a specific config, use the `CLAPBOT_ENVIRON` variable, and set it to `{NAME}` as appropriate to find your configuration. When working locally, you should instead use the `dev` environment and the `dev` config, to ensure that the application is appropriately discoverable.

## Installation

You should install `docker-compose` on your computer. On a Mac, you can run:
```
$ brew install docker-compose
```

You will also need to create a docker network, `reverse-proxy`, which you can do like this:
```
$ docker network create reverse-proxy
```

## Starting ClapBot

In local mode, clapbot servse to several domains which end in `clapbot.local`. Add the following line to your `/etc/hosts` file:
```
127.0.0.1 clapbot.local dev.clapbot.local flower.clapbot.local
```

To start clapbot, you should first start a reverse proxy to ensure that clapbots multiple web services are available on your host. To do this, run `docker-compose -f proxy/docker-compose.yml up -d` and notice that the nginx-proxy container should have started.

Then you can use `./scripts/dc up -d` to start all of the clapbot services. You should then be able to visit <http://dev.clapbot.local> and see the local clapbot instance running, and visit <http://flower.clapbot.local> to see the task manager running. Visiting <http://clapbot.local> will show you the website served via nginx. Note that <http://clapbot.local> is not running a debug server, so it won't reload when you change something in the code directory, however, <http://dev.clapbot.local> will. It is best to work from <http://dev.clapbot.local> until you are ready to check and deploy your changes.

## Deploy

When deploying clapbot, you should be sure not to deploy the `flask.debug` container or the `celery.flower` container unless you have suitable restricted access to both of those hosts.

## Setup Bounding Boxes

In the settings pane (<https://clapbot.example.com/settings/>), you should import bounding boxes for where you'd like to look for listings. You can include as many bounding boxes as you like, in CSV format, with a name for each bbox. Make bboxes at <https://boundingbox.klokantech.com>