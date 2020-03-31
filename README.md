# swatbot

This is a telegram bot that works similarly to a karma bot, where users can give each other "swats."

# Features
## Adding swats
Any user can add swats to another user's swat count by typing @\<mention> +5. The bot will respond "@\<mention>'s swat count has increased to \<count>."
## Subtracting swats
Any user can subtract swats from another user's swat count by typing @\<mention> -5. The bot will respond "@\<mention>'s swat count has decreased to \<count>."
## Rules (and penalties)
To see the list of bot rules, a user can type /rules. Rule infractions will result in penalty swats.
## Milestones
At various swat count milestones (such as 50 and 100) the bot will send a special message.
# Technical Details
## Tech stack
The backend is written in pure Python, using the python-telegram-bot API. It uses the webhook method instead of polling. 
