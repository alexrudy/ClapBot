HOSTNAME=$(hostname)

mkdir -p "./run/$HOSTNAME/"
mkdir -p "./log/$HOSTNAME/"

celery -A "${FLASK_APP:clapbot}:celery" worker -linfo --concurrency=10