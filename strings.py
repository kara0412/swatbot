from dotenv import load_dotenv
load_dotenv()
from settings import MAX_INC, MAX_DEC, PER_PERSON_TIME_LIMIT, \
    TIME_WINDOW, TIME_WINDOW_LIMIT_COUNT
from collections import OrderedDict

SWAT_UPDATE_STRING = "%s's swat count has now %s to %d." # name, "increased" or "decreased," count

RULES = "Rules? For a bot? Well, this is a spanking bot after all. And you know what that means if you disobey!" \
        "\n\n1. You can't subtract your own swats." \
        "\n2. You can only add %s swats at a time." \
        "\n3. You can only subtract %s swats at a time." \
        "\n4. You must wait %s minutes between sending swats to any particular person." \
        "\n5. You can only send %s swat adjustments in a %s minute window."\
        "\n\nEach infraction will swiftly earn you 5 additional swats. If you " \
        "need a refresher, just type /rules anytime to see this list." % \
        (MAX_INC, MAX_DEC, PER_PERSON_TIME_LIMIT, TIME_WINDOW_LIMIT_COUNT, TIME_WINDOW)

PENALTY_SCOLDS = {
    "OWN_SWAT": "Trying to subtract your own swats? Nice try.",
    "SWAT_INC": "Remember, the rules say you can only add %s swats at a time." % MAX_INC,
    "SWAT_DEC": "Remember, the rules say you can only decrease %s swats at time." % MAX_DEC,
    "LIMIT_PER_PERSON": "Whoa there... you just adjusted the swat count for %s! Remember, there's "
                        "a %s minute cool-down period before you can swat them again." %
                        ('%s', PER_PERSON_TIME_LIMIT),
    "LIMIT_PER_TIME_WINDOW": "Let's not get carried away... you can only send %s "
                             "swat adjustments within a %s minute window." %
                             (TIME_WINDOW_LIMIT_COUNT, TIME_WINDOW)
}

messages = OrderedDict()
messages[50] = "Over 50, ouch! I do not envy you right now."
messages[100] = "Oh boy, over 100 swats! Looks like you have a big spanking coming..."
MILESTONES = messages
