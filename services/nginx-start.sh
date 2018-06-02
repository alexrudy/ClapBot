#!/usr/bin/env bash
flask db upgrade
flask ingest
exec /usr/bin/supervisord
