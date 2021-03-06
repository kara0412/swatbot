from dotenv import load_dotenv
load_dotenv()
from collections import OrderedDict

SWAT_UPDATE_STRING = "%s's swat count has now %s to %d." # name, "increased" or "decreased," count
MY_SWATS = "%s, your swat count is %d."
VOTE = "Thanks for being a good citizen, %s! You get %d swats off, for a new swat count of %d."
ALREADY_VOTED = "You've already voted! Come back in 2024."
SWAT_COUNT_NO_MENTION = "You need to mention a user, like: /swat_count @Joe"
SWAT_COUNT = "%s's swat count is %d."
RULES = "Hi, I'm SwatBot! You can use me to give your friends swats, and I'll keep track of " \
        "how many they have coming. For example, you can type @<mention> +%s to give someone " \
        "%s swats if they misbehave. And if they do something nice, you can subtract swats by " \
        "typing @<mention> -%s! " \
        "\n\nBe careful, though... there are rules. This is a spanking " \
        "bot after all. And you know what that means if you disobey!" \
        "\n\n1. You can't subtract your own swats." \
        "\n2. You can only add %s swats at a time." \
        "\n3. You can only subtract %s swats at a time." \
        "\n4. You must wait %s minutes between adding or subtracting swats for any particular person." \
        "\n5. You can only add or subtract swats for %s people in a %s minute window."\
        "\n6. You must wait %s minutes before adding swats to someone who just added swats for you." \
        "\n\nEach infraction will swiftly earn you %s additional swats. These rules " \
        "are neither comprehensive nor invariable. More rules could be added at any " \
        "point. If you need a refresher, just type /rules anytime to see this list."
CONVERSION = "Ready to resolve some of your swats? Here are your options:" \
             "\n\n\u2022 10 swats = 1 minute of cornertime (visual proof encouraged)" \
             "\n\u2022 20 swats = 1 minute of cornertime bare (visual proof encouraged)" \
             "\n\u2022 2 swats = 1 line (ask your top or the group to assign you a line, visual proof required)" \
             "\n\u2022 50 swats = 250 word essay (ask your top or the group to assign you a topic, visual proof required)" \
             "\n\u2022 10 swats = 1 minute of service time (for tops)" \
             "\n\u2022 1 swat = 1 self-spank" \
             "\n\nOf course, the best option when possible is to just take a spanking. :-) DM me when you've " \
             "completed one (or more!) of these options, and I'll reset your swat count accordingly. You'll never be " \
             "allowed to go into negative swats via resolving, so the minimum number I'll reset your count to is 0. To build up " \
             "negative swats, you'll have to do nice things and get people to subtract for you instead." \
             "\n\nNote for tops: I know your options are sparse. Soliciting ideas for you!"

PENALTY_SCOLDS = {
    "SWATTING_BOT": "Lol.", # if someone tries to swat the bot
    "OWN_SWAT": "Trying to subtract your own swats? Nice try.",
    "SWAT_INC": "Remember, the rules say you can only add %s swats at a time.",
    "SWAT_DEC": "Remember, the rules say you can only decrease %s swats at time.",
    "LIMIT_PER_PERSON": "Whoa there... remember, you have to wait %s minutes before you can "
                        "add or subtract swats for %s again!",
    "LIMIT_PER_TIME_WINDOW": "Let's not get carried away... you can only add or "
                             "subtract swats for %s people within a %s minute window.",
    "RETALIATION": "Revenge is but a small circle. Remember, you gotta wait %s minutes "
                   "before you can retaliate. %d for you instead!"
}
PRAISE_MESSAGES = [
    "I'm proud of you.",
    "You did a good job.",
    "You're setting a wonderful example.",
    "I know you've learned your lesson.",
    "I know you'll be well-behaved from now on."
]


ERROR_MSG = "Oops! Something went wrong, and I couldn't understand that." # catch-all if swatbot starts malfunctioning
LEADERBOARD = "Our top miscreants are:\n\n"

HELP = "Here's a handy list of commands for you. " \
       "\n\n\u2022 Add swats: @<mention> +5" \
       "\n\u2022 Subtract swats: @<mention> -2" \
       "\n\u2022 View rules: /rules" \
       "\n\u2022 View conversions for resolving swats: /conversions" \
       "\n\u2022 View leaderboard: /leaderboard" \
       "\n\u2022 View your swat count: /my_swats" \
       "\n\u2022 View other people's counts: /swat_count @<mention> @<other>" \
       "\n\nHappy swatting!"
messages = OrderedDict()
messages[50] = "You reached 50, ouch! I do not envy you right now."
messages[100] = "Oh boy, over 100 swats! Looks like you have a big spanking coming..."
messages[150] = "I'd start behaving if I were you."
messages[200] = "You may never sit again..."
messages[250] = "This is getting out of hand."
messages[300] = "You're going to regret this, trust me."
messages[350] = "You were warned."
messages[400] = "SwatBot is giving you \"the look\" that tells you in no uncertain terms that you have crossed the line and earned a spanking"
messages[450] = "Just go to the bedroom and wait in the corner."
messages[500] = "This hurts me more than it hurts you."
messages[550] = "Don't test me."
messages[600] = "Your mouth is writing checks your butt can't cash."
messages[650] = "We all make choices."
messages[700] = "Does trouble find you or do you go looking for it?"
messages[750] = "You need to calm down."
messages[800] = "You poor child."
messages[900] = "I hope you'll learn a lesson from this."
messages[950] = "I don't even know what to tell you."
messages[1000] = "You'll be crying long before your punishment is over."
messages[1100] = messages[500]
messages[1200] = messages[250]
messages[1300] = messages[650]
messages[1400] = messages[400]
messages[1500] = messages[150]

MILESTONES = messages
