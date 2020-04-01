from dotenv import load_dotenv
load_dotenv()
from settings import env_vars
from collections import OrderedDict

SWAT_UPDATE_STRING = "%s's swat count has now %s to %d." # name, "increased" or "decreased," count

RULES = "Rules? For a bot? Well, this is a spanking bot after all. And you know what that means if you disobey!" \
        "\n\n1. You can't subtract your own swats." \
        "\n2. You can only add %s swats at a time." \
        "\n3. You can only subtract %s swats at a time." \
        "\n4. You must wait %s minutes between sending swats to any particular person." \
        "\n5. You can only send %s swat adjustments in a %s minute window."\
        "\n\nEach infraction will swiftly earn you 5 additional swats. These rules " \
        "are neither comprehensive nor invariable. If I need to add more, I certainly " \
        "will. If you need a refresher, just type /rules anytime to see this list." % \
        (env_vars["MAX_INC"], env_vars["MAX_DEC"], env_vars["PER_PERSON_TIME_LIMIT"], env_vars["TIME_WINDOW_LIMIT_COUNT"], env_vars["TIME_WINDOW"])

PENALTY_SCOLDS = {
    "SWATTING_BOT": "Lol.", # if someone tries to swat the bot
    "OWN_SWAT": "Trying to subtract your own swats? Nice try.",
    "SWAT_INC": "Remember, the rules say you can only add %s swats at a time." % env_vars["MAX_INC"],
    "SWAT_DEC": "Remember, the rules say you can only decrease %s swats at time." % env_vars["MAX_DEC"],
    "LIMIT_PER_PERSON": "Whoa there... you just adjusted the swat count for %s! Remember, there's "
                        "a %s minute cool-down period before you can swat them again." %
                        ('%s', env_vars["PER_PERSON_TIME_LIMIT"]),
    "LIMIT_PER_TIME_WINDOW": "Let's not get carried away... you can only send %s "
                             "swat adjustments within a %s minute window." %
                             (env_vars["TIME_WINDOW_LIMIT_COUNT"], env_vars["TIME_WINDOW"])
}

ERROR_MSG = "Oops! Something went wrong, and I'm now broken." # catch-all if swatbot starts malfunctioning

messages = OrderedDict()
messages[50] = "Over 50, ouch! I do not envy you right now."
messages[100] = "Oh boy, over 100 swats! Looks like you have a big spanking coming..."
MILESTONES = messages
