import unittest
import uuid
from main import mention_response
from db_helpers import reset_dict
from settings import MAX_INC, MAX_DEC, PENALTY
from strings import SWAT_UPDATE_STRING, PENALTY_SCOLDS
from telegram import Message, Update, User, Chat, MessageEntity
from datetime import datetime


def get_Jen_no_username():
    mention_text = "Jen"
    mentioned_user = User(1, "Jen", False)
    mention_entity = MessageEntity(MessageEntity.TEXT_MENTION, 0,
                                       len(mention_text) + 1,
                                       user=mentioned_user)
    return (mention_text, mentioned_user, mention_entity)

def get_Jen_username():
    mention_text = "Jen_username"
    mentioned_user = User(1, "Jen", False, username="Jen_username")
    mention_entity = MessageEntity(MessageEntity.MENTION, 0,
                                   len(mention_text) + 1,
                                   user=mentioned_user)
    return (mention_text, mentioned_user, mention_entity)

def get_Jill_no_username():
    from_user_text = "Jill"
    from_user = User(2, "Jill", False)
    from_user_entity = MessageEntity(MessageEntity.TEXT_MENTION, 0,
                                     len(from_user_text) + 1,
                                     user=from_user)
    return (from_user_text, from_user, from_user_entity)

def get_Jill_username():
    from_user_text = "Jill_username"
    from_user = User(2, "Jill", False, username="Jill_username")
    from_user_entity = MessageEntity(MessageEntity.MENTION, 0,
                                     len(from_user_text) + 1,
                                     user=from_user)
    return (from_user_text, from_user, from_user_entity)

class TestMentionHandlerBaseNoUsernames(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.chat = Chat(1, "group")
        cls.mention_text, cls.mentioned_user, cls.mention_entity = get_Jen_no_username()
        cls.from_user_text, cls.from_user, cls.from_user_entity = get_Jill_no_username()

    def setUp(self):
        class MockBot():
            def __init__(self):
                self.called = False
                self.called_with = []
                self.username = "bot"

            def send_message(self, chat_id, text):
                self.called = True
                self.called_with.append(text)
                return text
        mock_bot = MockBot()

        class Context():
            def __init__(self):
                self.bot = mock_bot

        self.mock_bot = mock_bot
        self.context = Context()
        reset_dict()

    def assert_chat_called_with(self, text):
        for call in self.mock_bot.called_with:
            if call == text:
                return True
        raise AssertionError("\"%s\" is not in the calls %s" %(text, self.mock_bot.called_with))


    def call_handler_with_message(self, text, entities=None, from_user=None):
        if not entities:
            entities = [self.mention_entity]
        m =  Message(uuid.uuid4(), from_user or self.from_user, datetime.now(), self.chat,
                     text=text, entities=entities)
        update = Update(uuid.uuid4(), message=m)
        mention_response(update, self.context)


    def test_penalty_increase_limit(self):
        self.call_handler_with_message("@%s +%d" % (self.mention_text, MAX_INC+1))
        self.assert_chat_called_with(PENALTY_SCOLDS["SWAT_INC"])
        self.assert_chat_called_with(SWAT_UPDATE_STRING % (self.from_user_text, "increased", PENALTY))
        self.call_handler_with_message("@%s +%d" % (self.mention_text, MAX_INC))
        self.assert_chat_called_with(SWAT_UPDATE_STRING % (self.mention_text, "increased", MAX_INC))

    def test_penalty_decrease_limit(self):
        self.call_handler_with_message("@%s -%d" % (self.mention_text, MAX_DEC+1))
        self.assert_chat_called_with(PENALTY_SCOLDS["SWAT_DEC"])
        self.assert_chat_called_with(SWAT_UPDATE_STRING % (self.from_user_text, "increased", PENALTY))
        self.call_handler_with_message("@%s -%d" % (self.mention_text, MAX_DEC))
        self.assert_chat_called_with(SWAT_UPDATE_STRING % (self.mention_text, "decreased", -MAX_DEC))

    def test_penalty_decrease_own_swats(self):
        self.call_handler_with_message("@%s -5" % self.from_user_text, entities=[self.from_user_entity])
        self.assert_chat_called_with(PENALTY_SCOLDS["OWN_SWAT"])
        self.assert_chat_called_with(SWAT_UPDATE_STRING % (self.from_user_text, "increased", PENALTY))

    def test_no_mention_response(self):
        self.call_handler_with_message("No mention here!")
        assert not self.mock_bot.called

    def test_mention_but_no_swat(self):
        self.call_handler_with_message("@%s" % self.mention_text)
        assert not self.mock_bot.called

    def test_multiple_swats(self):
        other_mention_text = "Bobby"
        other_mentioned_user = User(3, "Bobby", False)
        other_mention_entity = MessageEntity(MessageEntity.TEXT_MENTION, len(self.mention_text) + 5,
                                       len(other_mention_text) + 1,
                                       user=other_mentioned_user)
        self.call_handler_with_message("@%s +4 @%s +2" % (self.mention_text, other_mention_text),
                                       entities=[self.mention_entity, other_mention_entity])
        self.assert_chat_called_with(SWAT_UPDATE_STRING % (self.mention_text, "increased", 4))
        self.assert_chat_called_with(SWAT_UPDATE_STRING % (other_mention_text, "increased", 2))

    def test_mention(self):
        self.call_handler_with_message("@%s +4" % self.mention_text)
        self.assert_chat_called_with(SWAT_UPDATE_STRING % (self.mention_text, "increased", 4))
        self.call_handler_with_message("@%s -4" % self.mention_text)
        self.assert_chat_called_with(SWAT_UPDATE_STRING % (self.mention_text, "decreased", 0))


# Both users have usernames
class TestBothHaveUsernames(TestMentionHandlerBaseNoUsernames):

    @classmethod
    def setUpClass(cls):
        cls.chat = Chat(1, "group")
        cls.mention_text, cls.mentioned_user, cls.mention_entity = get_Jen_username()
        cls.from_user_text, cls.from_user, cls.from_user_entity = get_Jill_username()


# Only the mentioned user has a username
class TestOnlyMentionedHasUsername(TestMentionHandlerBaseNoUsernames):

    @classmethod
    def setUpClass(cls):
        cls.chat = Chat(1, "group")
        cls.mention_text, cls.mentioned_user, cls.mention_entity = get_Jen_username()
        cls.from_user_text, cls.from_user, cls.from_user_entity = get_Jill_no_username()

# Only the from user has a username
class TestOnlyFromHasUsername(TestMentionHandlerBaseNoUsernames):

    @classmethod
    def setUpClass(cls):
        cls.chat = Chat(1, "group")
        cls.mention_text, cls.mentioned_user, cls.mention_entity = get_Jen_no_username()
        cls.from_user_text, cls.from_user, cls.from_user_entity = get_Jill_username()