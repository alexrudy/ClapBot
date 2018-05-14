HOSTNAME=$(hostname)

mkdir -p "./var/$HOSTNAME/"

celery -A "${FLASK_APP:clapbot}:celery" beat -linfo \
    --schedule="./var/$HOSTNAME/celery-beat-schedule"