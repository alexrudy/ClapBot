#!/usr/bin/env bash
export FLASK_DEBUG="${FLASK_DEBUG:-True}"
flask $@
