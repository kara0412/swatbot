import unittest
import uuid

from main import mention_response, reset_dict
from telegram import Message, Update, User, Chat, MessageEntity
from datetime import datetime


class TestMentionHandler(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.chat = Chat(1, "group")
        cls.user_mention = User(1, "Kara", False, username="kara_username")
        cls.user_text_mention = User(2, "Joe", False)
        cls.user_text_mention_Jen = User(3, "Jen", False)
        cls.from_user = User(3, "Jill", False)

    def setUp(self):
        class MockBot():
            def __init__(self):
                self.called = False
                self.called_with = []

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


    def call_handler_with_message(self, text, entities=None, from_user=None):
        m =  Message(uuid.uuid4(), from_user or self.from_user, datetime.now(), self.chat,
                     text=text, entities=entities)
        update = Update(uuid.uuid4(), message=m)
        mention_response(update, self.context)

    def test_increase_limit(self):
        mention_Jen = MessageEntity(MessageEntity.TEXT_MENTION, 0, 4,
                                    user=self.user_text_mention_Jen)
        self.call_handler_with_message("@Jen +11", entities=[mention_Jen])
        self.assertTrue("You can only increase swats 10 at a time." in self.mock_bot.called_with)
        self.call_handler_with_message("@Jen +10", entities=[mention_Jen])
        self.assertTrue("Jen's swat count is now 10!" in self.mock_bot.called_with)

    def test_permission(self):
        mention_Jill = MessageEntity(MessageEntity.TEXT_MENTION, 0, 5,
                                     user = self.from_user)
        self.call_handler_with_message("@Jill -5", entities=[mention_Jill])
        self.assertTrue("Nice try... here's 10 more swats." in self.mock_bot.called_with)
        self.assertTrue("Jill's swat count is now 10!" in self.mock_bot.called_with)
        mention_Kara = MessageEntity(MessageEntity.MENTION, 0, 14,
                                     user=self.user_mention)
        self.call_handler_with_message("@kara_username -5", entities=[mention_Kara],
                                       from_user=self.user_mention)
        self.assertTrue("kara_username's swat count is now 10!" in self.mock_bot.called_with)

    def test_no_mention_response(self):
        self.call_handler_with_message("No mention here!")
        assert not self.mock_bot.called

    def test_mention_but_no_swat(self):
        mention_Jill = MessageEntity(MessageEntity.TEXT_MENTION, 0, 5,
                                     user=self.from_user)
        self.call_handler_with_message("@Jill", entities=[mention_Jill])
        assert not self.mock_bot.called

    def test_text_mention(self):
        mention_Joe = MessageEntity(MessageEntity.TEXT_MENTION, 0, 4,
                                    user=self.user_text_mention)
        self.call_handler_with_message("@Joe +3", entities=[mention_Joe])
        self.assertTrue("Joe's swat count is now 3!" in self.mock_bot.called_with)
        self.call_handler_with_message("@Joe -3", [mention_Joe])
        self.assertTrue("Joe's swat count is now 0!" in self.mock_bot.called_with)



    def test_mention(self):
        mention_Kara = MessageEntity(MessageEntity.MENTION, 0, 5) # no user
        self.call_handler_with_message("@Kara +4", entities=[mention_Kara])
        self.assertTrue("Kara's swat count is now 4!" in self.mock_bot.called_with)
        self.call_handler_with_message("@Kara -4", entities=[mention_Kara])
        self.assertTrue("Kara's swat count is now 0!" in self.mock_bot.called_with)

