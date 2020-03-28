import unittest

from telegram import MessageEntity

from main import get_count_after_mention


class TestMessageSwatCount(unittest.TestCase):

    def test_only_mention_and_swat(self):
        text = "@Jen +4"
        mention = MessageEntity('TEXT_MENTION', 0, 4)
        count = get_count_after_mention(mention, text)
        self.assertEqual(count, 4)

    def test_mention_in_between_text(self):
        text = "012345678 @Jen +4 here's some more text"
        mention = MessageEntity('TEXT_MENTION', 10, 4)
        count = get_count_after_mention(mention, text)
        self.assertEqual(count, 4)

    def test_mention_at_end(self):
        text = "012345678 @Jen +4"
        mention = MessageEntity('TEXT_MENTION', 10, 4)
        count = get_count_after_mention(mention, text)
        self.assertEqual(count, 4)

    def test_multiple_mentions(self):
        text = "@Kara @Jen +4"
        mention = MessageEntity('MENTION', 6, 4)
        count = get_count_after_mention(mention, text)
        self.assertEqual(count, 4)

    def test_multiple_swats(self):
        text = "@Kara +2 @Jen +4"
        kara_mention = MessageEntity('MENTION', 0, 5)
        jen_mention = MessageEntity('MENTION', 9, 4)
        kara_count = get_count_after_mention(kara_mention, text)
        self.assertEqual(kara_count, 2)
        jen_count = get_count_after_mention(jen_mention, text)
        self.assertEqual(jen_count, 4)

    def test_negative_swats(self):
        text = "@Jen -5"
        mention = MessageEntity('TEXT_MENTION', 0, 4)
        count = get_count_after_mention(mention, text)
        self.assertEqual(count, -5)

    def test_words_right_after_swat(self):
        text = "@Jen -5asf"
        mention = MessageEntity('TEXT_MENTION', 0, 4)
        count = get_count_after_mention(mention, text)
        self.assertEqual(count, None)

    def test_zero(self):
        text = "@Jen +0"
        mention = MessageEntity('MENTION', 0, 4)
        count = get_count_after_mention(mention, text)
        self.assertEqual(count, 0)