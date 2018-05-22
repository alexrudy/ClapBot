#!/usr/bin/env bash
set -eo pipefail
SERVICE=${1:-flask}
shift

if (dc run --rm "${SERVICE}.test" tox $@); then
    RESULT=$?
else
    RESULT=$?
    echo "FAILED"
fi

if (type pushover > /dev/null); then
    pushover -s$RESULT "Clapbot ${SERVICE} tests finished"
fi
