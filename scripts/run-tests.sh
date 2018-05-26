#!/usr/bin/env bash
set -eo pipefail

if (dc run --rm "flask.test" tox "$@"); then
    RESULT=$?
else
    RESULT=$?
    echo "FAILED"
fi

if (type pushover > /dev/null); then
    pushover -s$RESULT "Clapbot ${SERVICE} tests finished"
fi
