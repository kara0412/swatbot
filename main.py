#!/usr/bin/env python

import logging
import re
import time

from telegram.ext import Updater, CommandHandler, MessageHandler, BaseFilter
from telegram import MessageEntity

from settings import env_vars
from strings import SWAT_UPDATE_STRING, RULES, PENALTY_SCOLDS, MILESTONES, \
    ERROR_MSG, MY_SWATS, SWAT_COUNT_NO_MENTION, SWAT_COUNT, CONVERSION, \
    LEADERBOARD, HELP
from db_helpers import update_user_count_in_db, get_user_count_from_db, \
    get_nth_recent_swat_time, update_history_in_db, get_top_3_recipients
import sentry_sdk
sentry_sdk.init(env_vars["SENTRY_DSN"])
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)

updater = Updater(token=env_vars["TOKEN"], use_context=True)
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

def help(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=HELP % ())
def rules(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=RULES %
        (env_vars["MAX_INC"], env_vars["MAX_DEC"], env_vars["PER_PERSON_TIME_LIMIT"],
         env_vars["TIME_WINDOW_LIMIT_COUNT"], env_vars["TIME_WINDOW"],
         env_vars["RETALIATION_TIME"], env_vars["PENALTY"]))

def my_swats(update, context):
    from_user = update.message.from_user
    id = from_user.username or from_user.id
    count = get_user_count_from_db(str(id).lower())
    if count is None:
        count = 0
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=MY_SWATS % (from_user.first_name, count))

def swat_count(update, context):
    mentions_dict = message_contains_mentions(update.message)
    if mentions_dict != {}:
        for mention in mentions_dict:
            _, _, id, name = get_mention_properties(mention, mentions_dict)
            count = get_user_count_from_db(id)
            if count == None:
                count = 0
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=SWAT_COUNT % (name, count))
    else:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=SWAT_COUNT_NO_MENTION)

def leaderboard(update, context):
    top = get_top_3_recipients()
    construct_leaderboard = []
    for recipient in top:
        id, username_present, count = recipient[0], recipient[1], recipient[2]
        if not username_present:
            id = context.bot.get_chat_member(update.message.chat.id, id).user.first_name
        construct_leaderboard.append((id, count))

    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=LEADERBOARD % (construct_leaderboard[0][0], construct_leaderboard[0][1],
                                                 construct_leaderboard[1][0], construct_leaderboard[1][1],
                                                 construct_leaderboard[2][0], construct_leaderboard[2][1]))

def conversion(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=CONVERSION)

def crossed_milestone(old, new):
    for key, value in MILESTONES.items():
        if old < key and new >= key:
            return value
def check_for_milestones(old, new, context, update):
    if old is not None:
        milestone_message = crossed_milestone(old, new)
        if milestone_message:
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=milestone_message)

def eval_hit_time_limit(secs, limit):
    if secs == None:
        return False
    return time.time() - secs < limit

def did_retaliate(giver_id, receiver_id):
    if env_vars["RETALIATION_TIME"] == 0:
        return False
    last_time = get_nth_recent_swat_time(receiver_id, receiver=giver_id, count_must_inc=True)
    return eval_hit_time_limit(last_time, env_vars["RETALIATION_TIME"] * 60)

def should_rate_limit_per_person(giver_id, receiver_id):
    if env_vars["PER_PERSON_TIME_LIMIT"] == 0:
        return False
    last_time = get_nth_recent_swat_time(giver_id, receiver=receiver_id)
    return eval_hit_time_limit(last_time, env_vars["PER_PERSON_TIME_LIMIT"]*60)

def should_rate_limit_for_anyone(giver_id):
    if env_vars["TIME_WINDOW"] == 0:
        return False
    nth_time = get_nth_recent_swat_time(giver_id, n=env_vars["TIME_WINDOW_LIMIT_COUNT"])
    return eval_hit_time_limit(nth_time, env_vars["TIME_WINDOW"]*60)

def look_for_penalties(username_present, receiver_id, name, count, from_user, bot_username):
    from_user_id = from_user.id if not from_user.username else from_user.username.lower()
    penalty_conditions = [
        (lambda: receiver_id == bot_username, PENALTY_SCOLDS["SWATTING_BOT"]),
        (lambda: ((not username_present and from_user.id == receiver_id and count < 0)
                  or (username_present and from_user.username and from_user.username.lower() == receiver_id and count < 0)), PENALTY_SCOLDS["OWN_SWAT"]),
        (lambda: count > env_vars["MAX_INC"], PENALTY_SCOLDS["SWAT_INC"] % env_vars["MAX_INC"],),
        (lambda: count < env_vars["MAX_DEC"] * (-1), PENALTY_SCOLDS["SWAT_DEC"] % env_vars["MAX_DEC"]),
        (lambda: count > 0 and did_retaliate(from_user_id, receiver_id), PENALTY_SCOLDS["RETALIATION"] % (env_vars["RETALIATION_TIME"], count)),
        (lambda: should_rate_limit_per_person(from_user_id, receiver_id), PENALTY_SCOLDS["LIMIT_PER_PERSON"] % (env_vars["PER_PERSON_TIME_LIMIT"], name)),
        (lambda: should_rate_limit_for_anyone(from_user_id), PENALTY_SCOLDS["LIMIT_PER_TIME_WINDOW"] % (env_vars["TIME_WINDOW_LIMIT_COUNT"], env_vars["TIME_WINDOW"]))
    ]

    for condition, penalty_string in penalty_conditions:
        if condition():
            return penalty_string

def send_penalty(penalty_message, from_user, context, update, penalty=None):
    penalty_count = env_vars["PENALTY"] if penalty is None else penalty
    from_user_id, name = from_user.id, from_user.first_name
    if from_user.username: # to be consistent with the mention text issue :(
        from_user_id, name = from_user.username.lower(), from_user.username
    old_count = get_user_count_from_db(from_user_id)
    update_user_count_in_db(from_user_id, from_user.username != None, penalty_count)
    update_history_in_db(context.bot.username, from_user_id, penalty_count)
    new_count = get_user_count_from_db(from_user_id)
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=penalty_message)
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=SWAT_UPDATE_STRING % (name, "increased", new_count))
    check_for_milestones(old_count, new_count, context, update)


def get_mention_properties(entity, entities):
    username_present = entity.type != MessageEntity.TEXT_MENTION
    mention_text = entities[entity][1:]
    receiver_id = entity.user.id if not username_present else mention_text.lower()
    name = entity.user.first_name if not username_present else mention_text
    return (username_present, mention_text, receiver_id, name)


def mention_response(update, context):
    try:
        from_user = update.message.from_user
        entities = message_contains_mentions(update.message)
        if entities != {}:
            text = update.message.text
            for entity in entities:
                count = get_count_after_mention(entity, text)
                if isinstance(count, int):

                    username_present, mention_text, receiver_id, name = get_mention_properties(entity, entities)

                    # Did the sender violate any rules?
                    penalty_string = look_for_penalties(username_present, receiver_id, name,
                                                        count, from_user, context.bot.username)
                    if penalty_string:
                        if penalty_string == PENALTY_SCOLDS["RETALIATION"] % (env_vars["RETALIATION_TIME"], count):
                            send_penalty(penalty_string, from_user, context, update, penalty=count)
                        else:
                            send_penalty(penalty_string, from_user, context, update)
                        return

                    # No penalty; update receiver swat count as usual
                    old_count = get_user_count_from_db(receiver_id)
                    from_user_id = from_user.id if not from_user.username else from_user.username.lower()
                    update_user_count_in_db(receiver_id, username_present, count)
                    update_history_in_db(from_user_id, receiver_id, count)
                    new_count = get_user_count_from_db(receiver_id)
                    context.bot.send_message(chat_id=update.effective_chat.id,
                                             text=SWAT_UPDATE_STRING %
                                                  (name, "increased" if count >= 0
                                                  else "decreased", new_count))
                    check_for_milestones(old_count, new_count, context, update)
    except:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=ERROR_MSG)
        raise

def main():
    """Start the bot."""
    start_handler = CommandHandler('start', start)
    rules_handler = CommandHandler('rules', rules)
    my_swats_handler = CommandHandler('my_swats', my_swats)
    swat_count_handler = CommandHandler('swat_count', swat_count)
    conversion_handler = CommandHandler('conversions', conversion)
    leaderboard_handler = CommandHandler('leaderboard', leaderboard)
    help_handler = CommandHandler('help', help)
    mention_handler = MessageHandler(swatExistsFilter, mention_response)
    add_handlers_to_dispatcher([start_handler, rules_handler, my_swats_handler,
                                swat_count_handler, conversion_handler,
                                leaderboard_handler, help_handler,
                                mention_handler])
    updater.start_webhook(listen='0.0.0.0', port=env_vars["PORT"], url_path=env_vars["TOKEN"])
    updater.bot.set_webhook(env_vars["WEBHOOK_URL"] + env_vars["TOKEN"])
    updater.idle()

if __name__ == '__main__':
    main()
