import os
from dotenv import load_dotenv
load_dotenv()

WEBHOOK_URL = os.environ.get('WEBHOOK_URL', '')
TOKEN = os.environ.get('BOT_TOKEN')
PORT = int(os.environ.get('PORT', '8443'))
MAX_INC = int(os.environ.get('MAX_INC'))
MAX_DEC = int(os.environ.get('MAX_DEC'))
PENALTY = int(os.environ.get('PENALTY'))
DATABASE_URL = os.environ.get('DATABASE_URL')
PER_PERSON_TIME_LIMIT = int(os.environ.get('PER_PERSON_TIME_LIMIT'))
ENV = os.environ.get('ENV')
