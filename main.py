#!/usr/bin/env python
import logging
import re

from telegram.ext import Updater, CommandHandler, MessageHandler, BaseFilter
from telegram import MessageEntity

from settings import WEBHOOK_URL, TOKEN, PORT, MAX_INC, MAX_DEC, PENALTY
from strings import SWAT_UPDATE_STRING, RULES, PENALTY_SCOLDS
from db_helpers import update_user_count_in_db, get_user_count_from_db, \
    should_rate_limit_per_person, should_rate_limit_for_anyone

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)

updater = Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher

swat_regex = re.compile('^[\s]+[+-][0-9]+(?:\s|$)')

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

def rules(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=RULES)

def mention_response(update, context):

    from_user = update.message.from_user
    def send_penalty(penalty_message):
        from_user_id, name = from_user.id, from_user.first_name
        if from_user.username: # to be consistent with the mention text issue :(
            from_user_id, name = from_user.username.lower(), from_user.username
        update_user_count_in_db(context.bot.username, from_user_id,
                                from_user.username != None, PENALTY)
        new_count = get_user_count_from_db(from_user_id)
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=penalty_message)
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=SWAT_UPDATE_STRING % (name, "increased", new_count))

    entities = message_contains_mentions(update.message)
    if entities != False:
        text = update.message.text
        for entity in entities:
            count = get_count_after_mention(entity, text)
            if isinstance(count, int):
                username_present = entity.type != MessageEntity.TEXT_MENTION
                mention_text = entities[entity][1:]
                receiver_id = entity.user.id if not username_present else mention_text.lower()
                name = entity.user.first_name if not username_present else mention_text

                # Did the sender violate any rules?
                penalty_conditions = [
                    (lambda: ((not username_present and from_user.id == receiver_id and count < 0)
                             or (username_present and from_user.username and from_user.username.lower() == receiver_id
                                 and count < 0)), PENALTY_SCOLDS["OWN_SWAT"]),
                    (lambda: should_rate_limit_per_person(from_user.id, receiver_id), PENALTY_SCOLDS["LIMIT_PER_PERSON"] % name),
                    (lambda: should_rate_limit_for_anyone(from_user.id), PENALTY_SCOLDS["LIMIT_PER_TIME_WINDOW"]),
                    (lambda: count > MAX_INC, PENALTY_SCOLDS["SWAT_INC"]),
                    (lambda: count < MAX_DEC*(-1), PENALTY_SCOLDS["SWAT_DEC"])
                ]

                for condition, penalty_string in penalty_conditions:
                    if condition():
                        return send_penalty(penalty_string)

                # No penalty; update receiver swat count as usual
                update_user_count_in_db(from_user.id, receiver_id, username_present, count)
                new_count = get_user_count_from_db(receiver_id)
                context.bot.send_message(chat_id=update.effective_chat.id,
                                         text=SWAT_UPDATE_STRING %
                                              (name, "increased" if count >= 0
                                              else "decreased", new_count))

def main():
    """Start the bot."""
    start_handler = CommandHandler('start', start)
    rules_handler = CommandHandler('rules', rules)
    mention_handler = MessageHandler(swatExistsFilter, mention_response)
    add_handlers_to_dispatcher([start_handler, rules_handler, mention_handler])
    updater.start_webhook(listen='0.0.0.0', port=PORT, url_path=TOKEN)
    updater.bot.set_webhook(WEBHOOK_URL + TOKEN)
    updater.idle()

if __name__ == '__main__':
    main()
