import unittest
import uuid

import psycopg2
from db_helpers import get_conn
from main import mention_response, my_swats, swat_count, rules
from settings import env_vars
from strings import SWAT_UPDATE_STRING, PENALTY_SCOLDS, MILESTONES, MY_SWATS, \
    SWAT_COUNT, RULES, SWAT_COUNT_NO_MENTION
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


def setup_database():
    create_db_sql = """CREATE DATABASE test_swatbot"""
    server_conn = psycopg2.connect("user=%s password=%s" % (env_vars["DB_USERNAME"], env_vars["DB_PASSWORD"]))
    server_conn.set_isolation_level(0)
    server_cur = server_conn.cursor()
    server_cur.execute(create_db_sql)
    server_conn.commit()
    server_cur.close()


class TestMentionHandlerBaseNoUsernames(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.chat = Chat(1, "group")
        cls.mention_text, cls.mentioned_user, cls.mention_entity = get_Jen_no_username()
        cls.from_user_text, cls.from_user, cls.from_user_entity = get_Jill_no_username()

        setup_database()

    @classmethod
    def tearDownClass(cls):
        destroy_db_sql = """DROP DATABASE IF EXISTS test_swatbot;"""
        conn = psycopg2.connect("user=%s password=%s" % (env_vars["DB_USERNAME"], env_vars["DB_PASSWORD"]))
        conn.set_isolation_level(0)
        cur = conn.cursor()
        cur.execute(destroy_db_sql)
        conn.commit()
        cur.close()

    def setUp(self):
        self.previous_settings = env_vars.copy()
        class MockBot(User):
            def __init__(self):
                super(MockBot, self).__init__(25, "Bot", True, username="bot")
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

        create_users_sql = """CREATE TABLE users(
                                        user_id VARCHAR (50) UNIQUE PRIMARY KEY NOT NULL,
                                        username_present bool NOT NULL,
                                        received_swats_count INT NOT NULL
                                   );"""
        create_history_sql = """CREATE TABLE history(
                                            giver VARCHAR (50) NOT NULL,
                                            receiver VARCHAR (50) NOT NULL,
                                            count integer NOT NULL,
                                            timestamp integer NOT NULL
                                     );"""
        db_conn = get_conn()
        db_cur = db_conn.cursor()
        db_cur.execute(create_users_sql)
        db_cur.execute(create_history_sql)
        db_conn.commit()
        db_cur.close()

    def tearDown(self):
        env_vars.update(self.previous_settings)
        drop_users_sql = """DROP TABLE users;"""
        drop_history_sql = """DROP TABLE history;"""
        db_conn = get_conn()
        db_cur = db_conn.cursor()
        db_cur.execute(drop_users_sql)
        db_cur.execute(drop_history_sql)
        db_conn.commit()
        db_cur.close()


    def assert_chat_called_with(self, sent_texts):
        for text in sent_texts:
            if text not in self.mock_bot.called_with:
                raise AssertionError("\"%s\" is not in the calls %s" % (text, self.mock_bot.called_with))


    def call_handler_with_message(self, text, entities=None, from_user=None):
        if entities == None:
            entities = [self.mention_entity]
        m =  Message(uuid.uuid4(), from_user or self.from_user, datetime.now(), self.chat,
                     text=text, entities=entities)
        update = Update(uuid.uuid4(), message=m)
        mention_response(update, self.context)

    def call_my_swats(self):
        m = Message(uuid.uuid4(), self.mentioned_user, datetime.now(), self.chat,
                    text='/my_swats')
        update = Update(uuid.uuid4(), message=m)
        my_swats(update, self.context)

    def call_rules(self):
        m = Message(uuid.uuid4(), self.from_user, datetime.now(), self.chat,
                    text='/rules')
        update = Update(uuid.uuid4(), message=m)
        rules(update, self.context)

    def call_swat_count(self, users):
        command = '/swat_count '
        mention_entities = []
        for user in users:
            if user.username is not None:
                id = user.username
                mention = MessageEntity(MessageEntity.MENTION, len(command),
                                        len(id) + 1, user=user)
            else:
                id = user.first_name
                mention = MessageEntity(MessageEntity.TEXT_MENTION, len(command),
                                        len(id) + 1, user=user)
            command = command + '@' + id + ' '
            mention_entities.append(mention)

        m = Message(uuid.uuid4(), self.mentioned_user, datetime.now(),
                    self.chat, text=command, entities=mention_entities)
        update = Update(uuid.uuid4(), message=m)
        swat_count(update, self.context)

    def test_my_swats(self):
        self.call_handler_with_message('@%s +%d' % (self.mention_text, env_vars["MAX_INC"]))
        self.call_handler_with_message('@%s -%d' % (self.mention_text, 1))
        self.call_my_swats()
        expected_message = [MY_SWATS % (self.mentioned_user.first_name, env_vars["MAX_INC"] - 1)]
        self.assert_chat_called_with(expected_message)

    def test_swat_count(self):
        # zero swats
        self.call_swat_count([self.mentioned_user])
        expected_message = [SWAT_COUNT % (self.mention_text, 0)]
        self.assert_chat_called_with(expected_message)

        # one mention
        self.call_handler_with_message('@%s +%d' % (self.mention_text, 1))
        self.call_swat_count([self.mentioned_user])
        expected_messages = [SWAT_COUNT % (self.mention_text, 1)]
        self.assert_chat_called_with(expected_messages)

        # multiple mentions
        self.call_handler_with_message('@%s +%d' % (self.from_user_text, 2),
                                       entities=[self.from_user_entity])
        self.call_swat_count([self.mentioned_user, self.from_user])
        expected_messages_2 = [SWAT_COUNT % (self.mention_text, 1),
                               SWAT_COUNT % (self.from_user_text, 2)]
        self.assert_chat_called_with(expected_messages_2)


    def test_swat_count_error(self):
        self.call_swat_count([])
        expected_messages = [SWAT_COUNT_NO_MENTION]
        self.assert_chat_called_with(expected_messages)

    def test_rules(self):
        self.call_rules()
        expected_message = RULES % (env_vars["MAX_INC"], env_vars["MAX_DEC"],
                                    env_vars["PER_PERSON_TIME_LIMIT"], env_vars["TIME_WINDOW_LIMIT_COUNT"],
                                    env_vars["TIME_WINDOW"], env_vars["PENALTY"])
        self.assert_chat_called_with([expected_message])

    def test_milestones(self):
        count = 0
        messages_sent = 0
        for key, value in MILESTONES.items():
            num_messages_needed = key / env_vars["MAX_INC"] + 1 - messages_sent
            for i in range(num_messages_needed):
                self.call_handler_with_message("@%s +%d" % (self.mention_text, env_vars["MAX_INC"]))
                messages_sent += 1
                count += env_vars["MAX_INC"]
            self.assert_chat_called_with([value]) # assert milestone message sent
            self.mock_bot.called_with = []
            self.call_handler_with_message("@%s +%d" % (self.mention_text, env_vars["MAX_INC"]))
            messages_sent += 1
            count += env_vars["MAX_INC"]
            # assert milestone message just sent once
            self.assertEqual([SWAT_UPDATE_STRING % (self.mention_text, "increased", count)],
                             self.mock_bot.called_with)


    def test_penalty_swatting_bot(self):
        self.call_handler_with_message("@%s +%d" % (self.mock_bot.username, 5),
                                       entities=[MessageEntity(MessageEntity.MENTION, 0,
                                       len(self.mock_bot.username) + 1,
                                       user=self.mock_bot)])
        expected_messages = [PENALTY_SCOLDS["SWATTING_BOT"],
                             SWAT_UPDATE_STRING % (self.from_user_text, "increased", env_vars["PENALTY"])]
        self.assert_chat_called_with(expected_messages)

    def test_penalty_increase_limit(self):
        self.call_handler_with_message("@%s +%d" % (self.mention_text, env_vars["MAX_INC"]+1))
        self.call_handler_with_message("@%s +%d" % (self.mention_text, env_vars["MAX_INC"]))
        expected_messages = [PENALTY_SCOLDS["SWAT_INC"] % env_vars["MAX_INC"],
                             SWAT_UPDATE_STRING % (self.from_user_text, "increased", env_vars["PENALTY"]),
                             SWAT_UPDATE_STRING % (self.mention_text, "increased", env_vars["MAX_INC"])]
        self.assert_chat_called_with(expected_messages)

    def test_penalty_per_person_limit_string_interpolation(self):
        env_vars["PER_PERSON_TIME_LIMIT"] = 1
        self.call_handler_with_message("@%s +%d" % (self.mention_text, 2))
        self.call_handler_with_message("@%s +%d" % (self.mention_text, 2))
        expected_messages = ["%s's swat count has now increased to 2." % self.mention_text,
                             "Whoa there... remember, you have to wait 1 minutes before you "
                             "can add or subtract swats for %s again!" % self.mention_text,
                             "%s's swat count has now increased to 5." % self.from_user_text]
        self.assert_chat_called_with(expected_messages)

    def test_penalty_per_person_limit(self):
        env_vars["PER_PERSON_TIME_LIMIT"] = 1
        self.call_handler_with_message("@%s +%d" % (self.mention_text, 2))
        self.call_handler_with_message("@%s +%d" % (self.mention_text, 2))
        expected_messages = [SWAT_UPDATE_STRING % (self.mention_text, "increased", 2),
                             PENALTY_SCOLDS["LIMIT_PER_PERSON"] % (env_vars["PER_PERSON_TIME_LIMIT"], self.mention_text),
                             SWAT_UPDATE_STRING % (self.from_user_text, "increased", env_vars["PENALTY"])]
        self.assert_chat_called_with(expected_messages)


    def test_penalty_cross_receiver_limit(self):
        env_vars["TIME_WINDOW"] = 1
        for i in range(0, env_vars["TIME_WINDOW_LIMIT_COUNT"] + 1):
            self.call_handler_with_message("@%s +%d" % (self.mention_text, 2))
        expected_messages = [SWAT_UPDATE_STRING % (self.mention_text, "increased", 2),
                             PENALTY_SCOLDS["LIMIT_PER_TIME_WINDOW"] % (env_vars["TIME_WINDOW_LIMIT_COUNT"], env_vars["TIME_WINDOW"]),
                             SWAT_UPDATE_STRING % (self.from_user_text, "increased", env_vars["PENALTY"])]
        self.assert_chat_called_with(expected_messages)

    def test_penalty_decrease_limit(self):
        self.call_handler_with_message("@%s -%d" % (self.mention_text, env_vars["MAX_DEC"]+1))
        self.call_handler_with_message("@%s -%d" % (self.mention_text, env_vars["MAX_DEC"]))
        expected_messages = [PENALTY_SCOLDS["SWAT_DEC"] % env_vars["MAX_DEC"],
                             SWAT_UPDATE_STRING % (self.from_user_text, "increased", env_vars["PENALTY"]),
                             SWAT_UPDATE_STRING % (self.mention_text, "decreased", -env_vars["MAX_DEC"])]
        self.assert_chat_called_with(expected_messages)

    def test_penalty_decrease_own_swats(self):
        self.call_handler_with_message("@%s -5" % self.from_user_text, entities=[self.from_user_entity])
        expected_messages = [PENALTY_SCOLDS["OWN_SWAT"],
                             SWAT_UPDATE_STRING % (self.from_user_text, "increased", env_vars["PENALTY"])]
        self.assert_chat_called_with(expected_messages)

    def test_no_mention_response(self):
        self.call_handler_with_message("No mention here!", entities=[])
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
        expected_messages = [SWAT_UPDATE_STRING % (self.mention_text, "increased", 4),
                             SWAT_UPDATE_STRING % (other_mention_text, "increased", 2)]
        self.assert_chat_called_with(expected_messages)

    def test_mention(self):
        self.call_handler_with_message("@%s +4" % self.mention_text)
        self.call_handler_with_message("@%s -4" % self.mention_text)
        expected_messages = [SWAT_UPDATE_STRING % (self.mention_text, "increased", 4),
                             SWAT_UPDATE_STRING % (self.mention_text, "decreased", 0)]
        self.assert_chat_called_with(expected_messages)

# Both users have usernames
class TestBothHaveUsernames(TestMentionHandlerBaseNoUsernames):

    @classmethod
    def setUpClass(cls):
        setup_database()
        cls.chat = Chat(1, "group")
        cls.mention_text, cls.mentioned_user, cls.mention_entity = get_Jen_username()
        cls.from_user_text, cls.from_user, cls.from_user_entity = get_Jill_username()


# Only the mentioned user has a username
class TestOnlyMentionedHasUsername(TestMentionHandlerBaseNoUsernames):

    @classmethod
    def setUpClass(cls):
        setup_database()
        cls.chat = Chat(1, "group")
        cls.mention_text, cls.mentioned_user, cls.mention_entity = get_Jen_username()
        cls.from_user_text, cls.from_user, cls.from_user_entity = get_Jill_no_username()


# Only the from user has a username
class TestOnlyFromHasUsername(TestMentionHandlerBaseNoUsernames):

    @classmethod
    def setUpClass(cls):
        setup_database()
        cls.chat = Chat(1, "group")
        cls.mention_text, cls.mentioned_user, cls.mention_entity = get_Jen_no_username()
        cls.from_user_text, cls.from_user, cls.from_user_entity = get_Jill_username()
