import os
from dotenv import load_dotenv
load_dotenv()

env_vars = {
    "WEBHOOK_URL": os.environ.get('WEBHOOK_URL', ''),
    "TOKEN": os.environ.get('BOT_TOKEN'),
    "PORT": int(os.environ.get('PORT', '8443')),
    "MAX_INC": int(os.environ.get('MAX_INC')),
    "MAX_DEC": int(os.environ.get('MAX_DEC')),
    "PENALTY": int(os.environ.get('PENALTY')),
    "DATABASE_URL": os.environ.get('DATABASE_URL'),
    "PER_PERSON_TIME_LIMIT": int(os.environ.get('PER_PERSON_TIME_LIMIT')),
    "TIME_WINDOW_LIMIT_COUNT": int(os.environ.get('TIME_WINDOW_LIMIT_COUNT')),
    "TIME_WINDOW": int(os.environ.get('TIME_WINDOW')),
    "RETALIATION_TIME": int(os.environ.get('RETALIATION_TIME')),
    "ENV": os.environ.get('ENV'),
    "DB_USERNAME": os.environ.get('DB_USERNAME'),
    "DB_PASSWORD": os.environ.get('DB_PASSWORD'),
    "SENTRY_DSN": os.environ.get('SENTRY_TOKEN'),
}

