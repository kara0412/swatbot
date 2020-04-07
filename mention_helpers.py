from telegram import MessageEntity


def message_contains_mentions(message):
    """ Returns a list of MessageEntity mentions/text_mentions if they
        exist, and False if not.
    """
    return message.parse_entities(types=[MessageEntity.TEXT_MENTION,
                                         MessageEntity.MENTION])

def get_mention_properties(entity, entities):
    username_present = entity.type != MessageEntity.TEXT_MENTION
    mention_text = entities[entity][1:]
    receiver_id = entity.user.id if not username_present else mention_text.lower()
    name = entity.user.first_name if not username_present else mention_text
    return (username_present, mention_text, receiver_id, name)