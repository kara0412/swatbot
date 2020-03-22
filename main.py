#!/usr/bin/env python
import math

from telegram.ext import Updater, CommandHandler, MessageHandler, BaseFilter
from telegram import MessageEntity
import logging
import os
import re
import time
import psycopg2
from collections import defaultdict
from dotenv import load_dotenv
load_dotenv()
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)
WEBHOOK_URL = os.environ.get('WEBHOOK_URL', '')
TOKEN = os.environ.get('BOT_TOKEN')
PORT = int(os.environ.get('PORT', '8443'))
MAX_INC = int(os.environ.get('MAX_INC'))
MAX_DEC = int(os.environ.get('MAX_DEC'))
PENALTY = int(os.environ.get('PENALTY'))
DATABASE_URL = os.environ.get('DATABASE_URL')
PER_PERSON_TIME_LIMIT = int(os.environ.get('PER_PERSON_TIME_LIMIT'))
conn = psycopg2.connect(DATABASE_URL, sslmode='require')

updater = Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher

in_memory_swat_count_dict = defaultdict(int)
swat_regex = re.compile('^[\s]+[+-][0-9]+(?:\s|$)')
swat_update_string = "%s's swat count has now %s to %d."
cool_down_string = "Whoa there... you just gave swats to %s! Remember, there's " \
                   "a %s minute cool-down period before you can swat them again."
def reset_dict():
    in_memory_swat_count_dict.clear()

def message_contains_mentions(message):
    """ Returns a list of MessageEntity mentions/text_mentions if they
        exist, and False if not.
    """
    return message.parse_entities(types=[MessageEntity.TEXT_MENTION,
                                         MessageEntity.MENTION])

def get_count_after_mention(mention, text):
    start_index = mention.offset + mention.length
    after_mention = text[start_index:]
    m = swat_regex.match(after_mention)
    return int(m.group()) if m else None


def update_history_in_db(giver, receiver, count):
    if os.environ.get('ENV') == 'TEST':
        return
    sql = """INSERT INTO history (giver, receiver, count, timestamp)
             VALUES (%s, %s, %s, %s)"""
    cur = conn.cursor()
    cur.execute(sql, (str(giver), str(receiver), count, time.time()))
    conn.commit()
    cur.close()

def should_rate_limit(giver, receiver):
    if os.environ.get('ENV') == 'TEST':
        return False
    sql = """SELECT MAX(timestamp) FROM history
             WHERE giver = %s AND receiver = %s;"""
    cur = conn.cursor()
    cur.execute(sql, (str(giver), str(receiver)))
    result = None
    if cur.rowcount == 1:
        result = cur.fetchone()[0]
    conn.commit()
    cur.close()
    if not result:
        return False
    return time.time() - result < PER_PERSON_TIME_LIMIT

def update_user_count_in_db(giver_id, receiver_id, username_present, count):
    if os.environ.get('ENV') == 'TEST':
        in_memory_swat_count_dict[receiver_id] += count
        return
    sql = """INSERT INTO users (user_id, username_present, received_swats_count)
             VALUES (%s, %s, %s)
             ON CONFLICT (user_id) 
             DO UPDATE 
                SET received_swats_count = users.received_swats_count + %s
                RETURNING received_swats_count;"""
    cur = conn.cursor()
    cur.execute(sql, (str(receiver_id), username_present, count, count))
    conn.commit()
    cur.close()
    update_history_in_db(giver_id, receiver_id, count)

def get_user_count_from_db(user_id):
    if os.environ.get('ENV') == 'TEST':
        return in_memory_swat_count_dict[user_id]
    sql = """SELECT users.received_swats_count 
             FROM users
             WHERE users.user_id=%s"""
    cur = conn.cursor()
    cur.execute(sql, (str(user_id),))
    result = None
    if cur.rowcount == 1:
        result = cur.fetchone()[0]
    conn.commit()
    cur.close()
    return result

class SwatFilter(BaseFilter):
    def filter(self, message):
        entities = message_contains_mentions(message)
        if entities != {}:
            for entity in entities:
                count = get_count_after_mention(entity, message.text)
                return isinstance(count, int)
        return False

swatExistsFilter = SwatFilter()
def add_handlers_to_dispatcher(handlers):
    for handler in handlers:
        dispatcher.add_handler(handler)

def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Hello! I'm SwatBot.")

def add_penalty(from_id, receiver_id, username_present, name, context, update):
    update_user_count_in_db(from_id, receiver_id, username_present, PENALTY)
    new_count = get_user_count_from_db(receiver_id)
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Nice try... here's %d more swats." % PENALTY)
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=swat_update_string %
                                  (name, "increased", new_count))



def mention_response(update, context):
    entities = message_contains_mentions(update.message)
    text = update.message.text
    from_user = update.message.from_user
    if entities != False:
        for entity in entities:
            count = get_count_after_mention(entity, text)
            if isinstance(count, int):
                username_present = entity.type != MessageEntity.TEXT_MENTION
                if not username_present:
                    (receiver_id, name) = (entity.user.id, entity.user.first_name)
                    if from_user.id == entity.user.id and count < 0:
                        add_penalty(from_user.id, receiver_id, username_present, name, context, update)
                        return
                else:
                    (receiver_id, name) = (entities[entity][1:].lower(), entities[entity][1:])
                    if from_user.username == entities[entity][1:] and count < 0:
                        add_penalty(from_user.id, receiver_id, username_present, name, context, update)
                        return
                if should_rate_limit(from_user.id, receiver_id):
                    context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=cool_down_string % (name, math.floor(PER_PERSON_TIME_LIMIT / 60)))
                    return
                if count > MAX_INC:
                    context.bot.send_message(chat_id=update.effective_chat.id,
                                             text="You can only increase swats %d"
                                                  " at a time." % MAX_INC)
                elif count < MAX_DEC*(-1):
                    context.bot.send_message(chat_id=update.effective_chat.id,
                                             text="You can only decrease swats %d"
                                                  " at a time." % MAX_DEC)
                else:
                    update_user_count_in_db(from_user.id, receiver_id, username_present, count)
                    new_count = get_user_count_from_db(receiver_id)
                    context.bot.send_message(chat_id=update.effective_chat.id,
                                             text=swat_update_string %
                                                  (name,
                                                   "increased" if count >= 0
                                                   else "decreased",
                                                   new_count))

def main():
    """Start the bot."""
    start_handler = CommandHandler('start', start)
    mention_handler = MessageHandler(swatExistsFilter, mention_response)
    add_handlers_to_dispatcher([start_handler, mention_handler])
    updater.start_webhook(listen='0.0.0.0', port=PORT, url_path=TOKEN)
    updater.bot.set_webhook(WEBHOOK_URL + TOKEN)
    updater.idle()

if __name__ == '__main__':
    main()
