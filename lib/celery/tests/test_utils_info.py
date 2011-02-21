import unittest2 as unittest

from celery.utils import info

RANDTEXT = """\
The quick brown
fox jumps
over the
lazy dog\
"""

RANDTEXT_RES = """\
    The quick brown
    fox jumps
    over the
    lazy dog\
"""

QUEUES = {"queue1": {
            "exchange": "exchange1",
            "exchange_type": "type1",
            "binding_key": "bind1"},
         "queue2": {
            "exchange": "exchange2",
            "exchange_type": "type2",
            "binding_key": "bind2"}}


QUEUE_FORMAT = """
. queue1 -> exchange:exchange1 (type1) binding:bind1
. queue2 -> exchange:exchange2 (type2) binding:bind2
""".strip()


class TestInfo(unittest.TestCase):

    def test_humanize_seconds(self):
        t = ((4 * 60 * 60 * 24, "4 days"),
             (1 * 60 * 60 * 24, "1 day"),
             (4 * 60 * 60, "4 hours"),
             (1 * 60 * 60, "1 hour"),
             (4 * 60, "4 minutes"),
             (1 * 60, "1 minute"),
             (4, "4.00 seconds"),
             (1, "1.00 second"),
             (4.3567631221, "4.36 seconds"),
             (0, "now"))

        for seconds, human in t:
            self.assertEqual(info.humanize_seconds(seconds), human)

        self.assertEqual(info.humanize_seconds(4, prefix="about "),
                          "about 4.00 seconds")

    def test_textindent(self):
        self.assertEqual(info.textindent(RANDTEXT, 4), RANDTEXT_RES)

    def test_format_queues(self):
        self.assertEqual(info.format_queues(QUEUES), QUEUE_FORMAT)

    def test_broker_info(self):
        info.format_broker_info()
