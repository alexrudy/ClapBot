SQLALCHEMY_DATABASE_URI = 'sqlite:////tmp/test.db'
SQLALCHEMY_TRACK_MODIFICATIONS = False
CRAIGSLIST_SITE = 'sfbay'
CRAIGSLIST_AREA = 'eby'
CRAIGSLIST_CATEGORY = 'apa'
CRAIGSLIST_FILTERS = {
    'max_price': 3100, 'min_price': 1000, 'has_image':True
}
CRAIGSLIST_CACHE_PATH = 'cldata'
CELERY_BROKER_URL = 'redis://localhost:6379/1'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/1'
MAIL_DEFAULT_SENDER = 'clapbot@alexrudy.org'