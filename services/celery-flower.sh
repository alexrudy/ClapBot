HOSTNAME=$(hostname)

mkdir -p "./run/$HOSTNAME/"
mkdir -p "./log/$HOSTNAME/"

celery -A "${FLASK_APP:clapbot}:celery" flower -linfo \
    --address='0.0.0.0'