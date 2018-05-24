SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:postgres@db:5432/clapbot'
SQLALCHEMY_TRACK_MODIFICATIONS = False

CRAIGSLIST_SITE = 'sfbay'
CRAIGSLIST_AREA = 'eby'
CRAIGSLIST_CATEGORY = 'apa'
CRAIGSLIST_FILTERS = {
    'max_price': 3100, 'min_price': 1000, 'has_image':True
}
CRAIGSLIST_CACHE_ENABLE = False
CRAIGSLIST_CHECK_BBOX = True
CRAIGSLIST_CACHE_PATH = 'data/cl/'

CRAIGSLIST_SCORE_TRANSIT = True
CRAIGSLIST_SCORE_WORK_LAT = 37.876685
CRAIGSLIST_SCORE_WORK_LON = -122.261998
CRAIGSLIST_SCORE_WORK_CLOSE = 10.0
CRAIGSLIST_SCORE_WORK_MEDIUM = 20.0
CRAIGSLIST_SCORE_STUDIO_PENALTY = -1500

CRAIGSLIST_MAX_MAIL = 10
CRAIGSLIST_MAX_SCRAPE = 50
CRAIGSLIST_SEND_MAIL = True

CRAIGSLIST_TASK_SKEW = 120

SCORE_TARGET_DATE = '2017-07-01'
TIMEZONE = 'America/Los_Angeles'

CELERY_BROKER_URL = 'redis://redis:6379/1'
CELERY_RESULT_BACKEND = 'redis://redis:6379/1'

MAIL_DEFAULT_SENDER = 'email@example.com'
MAIL_DEFAULT_RECIPIENTS = ['me@example.com']

BCRYPT_HANDLE_LONG_PASSWORDS = True
CLAPBOT_PASSWORD = 'clapbot'
CLAPBOT_PASSWORD_TOKEN = 'open-sesame'

CRAIGSLIST_SEND_MAIL = False
SECRET_KEY = b'@7\x93\r\xc1\xaf@vB\x88\xec\\\xd7\xc9\xafL\x9a\xd1\x01y\xd3\x03\xd5v'