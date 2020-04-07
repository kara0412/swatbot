from db_helpers import get_user_count_from_db, get_leaderboard_from_db
from mention_helpers import message_contains_mentions, get_mention_properties
from settings import env_vars
from strings import HELP, RULES, MY_SWATS, LEADERBOARD, CONVERSION, \
    SWAT_COUNT_NO_MENTION, SWAT_COUNT


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
    context.bot.send_message(chat_id=update.effective_chat.id, text=CONVERSION)
