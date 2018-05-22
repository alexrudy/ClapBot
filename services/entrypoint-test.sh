#!/usr/bin/env bash

set -e

pipenv lock -r > requirements.txt
pipenv lock --dev -r > requirements.dev.txt

exec "$@"