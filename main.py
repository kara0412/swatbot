#!/usr/bin/env python

from telegram.ext import Updater, CommandHandler, MessageHandler, BaseFilter
from telegram import MessageEntity
import logging
import os
import re
from collections import defaultdict
from dotenv import load_dotenv
load_dotenv()
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)
TOKEN = os.environ.get('BOT_TOKEN')
PORT = int(os.environ.get('PORT', '8443'))
MAX_INC = int(os.environ.get('MAX_INC'))
MAX_DEC = int(os.environ.get('MAX_DEC'))
PENALTY = int(os.environ.get('PENALTY'))

updater = Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher

swat_count_dict = defaultdict(int)
swat_regex = re.compile('^[\s]+[+-][0-9]+(?:\s|$)')
swat_update_string = "%s's swat count has now %s to %d."

def reset_dict():
    swat_count_dict.clear()

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

def add_penalty(id, name, context, update):
    swat_count_dict[id] += PENALTY
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Nice try... here's %d more swats." % PENALTY)
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=swat_update_string %
                                  (name, "increased", swat_count_dict[id]))

def mention_response(update, context):
    entities = message_contains_mentions(update.message)
    text = update.message.text
    from_user = update.message.from_user
    if entities != False:
        for entity in entities:
            count = get_count_after_mention(entity, text)
            if isinstance(count, int):
                if entity.type == MessageEntity.TEXT_MENTION:
                    (id, name) = (entity.user.id, entity.user.first_name)
                    if from_user.id == entity.user.id and count < 0:
                        add_penalty(id, name, context, update)
                        return
                else:
                    (id, name) = (entities[entity][1:], entities[entity][1:])
                    if from_user.username == entities[entity][1:] and count < 0:
                        add_penalty(id, name, context, update)
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
                    swat_count_dict[id] += count
                    context.bot.send_message(chat_id=update.effective_chat.id,
                                             text=swat_update_string %
                                                  (name,
                                                   "increased" if count >= 0
                                                   else "decreased",
                                                   swat_count_dict[id]))

def main():
    """Start the bot."""

    start_handler = CommandHandler('start', start)
    mention_handler = MessageHandler(swatExistsFilter, mention_response)
    add_handlers_to_dispatcher([start_handler, mention_handler])
    updater.start_webhook(listen='0.0.0.0', port=PORT, url_path=TOKEN)
    updater.bot.set_webhook('https://telegram-swat-bot.herokuapp.com/' + TOKEN)

    updater.idle()

if __name__ == '__main__':
    main()
