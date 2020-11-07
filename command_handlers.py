import random

from db_helpers import get_user_count_from_db, get_leaderboard_from_db, \
    update_user_count_in_db, update_history_in_db
from mention_helpers import message_contains_mentions, get_mention_properties
from settings import env_vars
from strings import HELP, RULES, MY_SWATS, LEADERBOARD, CONVERSION, \
    SWAT_COUNT_NO_MENTION, SWAT_COUNT, PRAISE_MESSAGES


def start(update, context):
    if update.effective_chat.id == env_vars["CHAT_ID"]:
        return
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Hello! I'm SwatBot.")

def help(update, context):
    if update.effective_chat.id == env_vars["CHAT_ID"]:
        return
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=HELP % ())
def rules(update, context):
    if update.effective_chat.id == env_vars["CHAT_ID"]:
        return
    context.bot.send_message(chat_id=update.effective_chat.id, text=RULES %
        (env_vars["MAX_INC"], env_vars["MAX_INC"], env_vars["MAX_DEC"],
         env_vars["MAX_INC"], env_vars["MAX_DEC"], env_vars["PER_PERSON_TIME_LIMIT"],
         env_vars["TIME_WINDOW_LIMIT_COUNT"], env_vars["TIME_WINDOW"],
         env_vars["RETALIATION_TIME"], env_vars["PENALTY"]))

def my_swats(update, context):
    if update.effective_chat.id == env_vars["CHAT_ID"]:
        return
    from_user = update.message.from_user
    id = from_user.username or from_user.id
    count = get_user_count_from_db(str(id).lower())
    if count is None:
        count = 0
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=MY_SWATS % (from_user.first_name, count))

def swat_count(update, context):
    if update.effective_chat.id == env_vars["CHAT_ID"]:
        return
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
    if update.effective_chat.id == env_vars["CHAT_ID"]:
        return
    n = env_vars["LEADERBOARD_COUNT"]
    top = get_leaderboard_from_db(n)
    leaderboard_string = LEADERBOARD
    for i, recipient in enumerate(top):
        id, username_present, count = recipient[0], recipient[1], recipient[2]
        if not username_present:
            id = context.bot.get_chat_member(update.message.chat.id, id).user.first_name
        leaderboard_string += '%d. %s with %d swats\n' % (i+1, id, count)
    context.bot.send_message(chat_id=update.effective_chat.id, text=leaderboard_string)

def conversion(update, context):
    if update.effective_chat.id == env_vars["CHAT_ID"]:
        return
    context.bot.send_message(chat_id=update.effective_chat.id, text=CONVERSION)

def resolve(update, context):
    if update.effective_chat.id == env_vars["CHAT_ID"]:
        return
    if update.message.from_user.id != env_vars["ME_ID"]:
        context.bot.send_message(chat_id=update.effective_chat.id, text='Sorry, only a moderator can do that, but nice try!')
        return
    mentions_dict = message_contains_mentions(update.message)
    if mentions_dict == {} or len(mentions_dict) > 1 or len(context.args) < 2:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='Send me a mention and a positive number of swats to resolve.')
    else:
        for mention in mentions_dict:
            username_present, _, id, name = get_mention_properties(mention, mentions_dict)
            current_count = get_user_count_from_db(id)
            current_count = 0 if current_count is None else current_count
            if current_count <= 0:
                context.bot.send_message(chat_id=update.effective_chat.id,
                                         text="%s already has %d swats, no need to resolve!" %
                                              (name, current_count))
                return
            to_resolve = int(context.args[1])
            if to_resolve <= 0:
                context.bot.send_message(chat_id=update.effective_chat.id,
                                         text='Send me a mention and a positive number of swats to resolve.')
                return
            new_count_to_set = -to_resolve if current_count > to_resolve else -current_count
            update_user_count_in_db(id, username_present, new_count_to_set)

            update_history_in_db("swat_resolver", id, -(to_resolve))
            new_count_set_in_db = get_user_count_from_db(id)
            random_index = random.randint(0, len(PRAISE_MESSAGES)-1)
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text="%s, your swat count has been resolved to %d. %s" %
                                          (name, new_count_set_in_db, PRAISE_MESSAGES[random_index]))


