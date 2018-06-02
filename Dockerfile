FROM tiangolo/uwsgi-nginx:python3.6

RUN apt-get update -y
RUN pip install pipenv

ENV FLASK_APP=clapbot.app

# By default, allow unlimited file sizes, modify it to limit the file sizes
# To have a maximum of 1 MB (Nginx's default) change the line to:
# ENV NGINX_MAX_UPLOAD 1m
ENV NGINX_MAX_UPLOAD 0

# By default, Nginx listens on port 80.
# To modify this, change LISTEN_PORT environment variable.
# (in a Dockerfile or with an option for `docker run`)
ENV LISTEN_PORT 80

# Which uWSGI .ini file should be used, to make it customizable
ENV UWSGI_INI /app/uwsgi.ini

# URL under which static (not modified by Python) files will be requested
# They will be served by Nginx directly, without being handled by uWSGI
ENV STATIC_URL /static
# Absolute path in where the static files wil be
ENV STATIC_PATH /app/clapbot/static

# If STATIC_INDEX is 1, serve / with /static/index.html directly (or the static URL configured)
# ENV STATIC_INDEX 1
ENV STATIC_INDEX 0

RUN mkdir -p /app
WORKDIR /app

# Copy the entrypoint that will generate Nginx additional configs
COPY services/nginx-entrypoint.sh /app/services/nginx-entrypoint.sh
RUN chmod +x /app/services/nginx-entrypoint.sh

# Copy the entrypoint that will generate Nginx additional configs
COPY services/nginx-entrypoint.sh /app/services/entrypoint.sh
RUN chmod +x /app/services/entrypoint.sh



COPY Pipfile Pipfile
COPY Pipfile.lock Pipfile.lock

# -- Install dependencies:
RUN pipenv install --deploy --system

COPY . /app

ENTRYPOINT ["services/nginx-entrypoint.sh"]
CMD ["services/nginx-start.sh"]
