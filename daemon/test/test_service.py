import unittest
import unittest.mock

import os
import json

import service


class MockRedis(object):

    def __init__(self, host, port):

        self.host = host
        self.port = port
        self.channel = None
        self.messages = []

    def pubsub(self):

        return self

    def subscribe(self, channel):

        self.channel = channel

    def get_message(self):

        return self.messages.pop(0)


class TestService(unittest.TestCase):

    @unittest.mock.patch.dict(os.environ, {
        "REDIS_HOST": "most.com",
        "REDIS_PORT": "667",
        "REDIS_CHANNEL": "stuff",
        "SLEEP": "0.7"
    })
    @unittest.mock.patch("redis.StrictRedis", MockRedis)
    def setUp(self):

        self.daemon = service.Daemon()

    @unittest.mock.patch.dict(os.environ, {
        "REDIS_HOST": "most.com",
        "REDIS_PORT": "667",
        "REDIS_CHANNEL": "stuff",
        "SLEEP": "0.7"
    })
    @unittest.mock.patch("redis.StrictRedis", MockRedis)
    def test___init___(self):

        daemon = service.Daemon()

        self.assertEqual(daemon.redis.host, "most.com")
        self.assertEqual(daemon.redis.port, 667)
        self.assertEqual(daemon.channel, "stuff")
        self.assertEqual(daemon.sleep, 0.7)

    def test_subscribe(self):

        self.daemon.subscribe()

        self.assertEqual(self.daemon.redis, self.daemon.pubsub)
        self.assertEqual(self.daemon.redis.channel, "stuff")

    def test_text(self):

        self.assertEqual("hey", self.daemon.text({
            "name": "hey",
            "data": {}
        }))

        self.assertEqual("ya", self.daemon.text({
            "name": "hey",
            "data": {
                "text": "ya"
            }
        }))

    def test_reference(self):

        self.assertIsNone(self.daemon.reference({}))

        self.assertEqual("hey", self.daemon.reference({
            "name": "hey",
            "data": {}
        }))

        self.assertEqual("<@ya>", self.daemon.reference({
            "name": "hey",
            "chore-slack.nandy.io": {
                "slack_id": "ya"
            }
        }))

    @unittest.mock.patch("service.time.time", unittest.mock.MagicMock(return_value=7))
    @unittest.mock.patch("builtins.open", create=True)
    @unittest.mock.patch("requests.post")
    def test_say(self, mock_post, mock_open):

        person = {}

        mock_open.side_effect = [
            unittest.mock.mock_open(read_data='webhook_url: http://peeps').return_value
        ]

        self.daemon.say("hey", person)

        mock_post.assert_has_calls([
            unittest.mock.call("http://peeps", json={
                "text": "hey"
            }),
            unittest.mock.call().raise_for_status()
        ])

        mock_open.assert_called_once_with("/opt/service/config/settings.yaml", "r")

        mock_open.side_effect = [
            unittest.mock.mock_open(read_data='webhook_url: http://peeps').return_value
        ]

        mock_post.reset_mock()

        self.daemon.say(
            "hey",
            {
                "name": "dude"
            }
        )

        mock_post.assert_has_calls([
            unittest.mock.call("http://peeps", json={
                "text": "dude, hey"
            }),
            unittest.mock.call().raise_for_status()
        ])

    @unittest.mock.patch("service.time.time", unittest.mock.MagicMock(return_value=7))
    @unittest.mock.patch("builtins.open", create=True)
    @unittest.mock.patch("requests.post")
    def test_process(self, mock_post, mock_open):

        mock_open.side_effect = [
            unittest.mock.mock_open(read_data='webhook_url: http://peeps').return_value,
            unittest.mock.mock_open(read_data='webhook_url: http://peeps').return_value
        ]

        self.daemon.subscribe()

        self.daemon.redis.messages = [
            None,
            {"data": 1},
            {
                "data": json.dumps({
                    "kind": "area",
                    "action": "create",
                    "area": {
                        "name": "ya",
                        "data": {
                            "text": "the living room"
                        }
                    },
                    "person": {
                        "name": "dude",
                        "data": {}
                    }
                })
            },
            {
                "data": json.dumps({
                    "kind": "act",
                    "action": "create",
                    "act": {
                        "name": "ya",
                        "status": "positive",
                        "data": {
                            "text": "put away your towel"
                        }
                    },
                    "person": {
                        "name": "dude",
                        "data": {}
                    }
                })
            },
            {
                "data": json.dumps({
                    "kind": "todo",
                    "action": "create",
                    "todo": {
                        "name": "ya",
                        "data": {
                            "text": "mow the lawn"
                        }
                    },
                    "person": {
                        "name": "dude",
                        "data": {}
                    }
                })
            },
            {
                "data": json.dumps({
                    "kind": "todos",
                    "speech": {
                        "node": "bump",
                        "language": "cursing"
                    },
                    "todos": [
                        {
                            "name": "hey",
                            "data": {
                                "text": "guys"
                            }
                        }
                    ],
                    "person": {
                        "name": "dude",
                        "data": {}
                    }
                })
            },
            {
                "data": json.dumps({
                    "kind": "routine",
                    "action": "create",
                    "routine": {
                        "name": "ya",
                        "data": {
                            "text": "hey"
                        }
                    },
                    "person": {
                        "name": "dude",
                        "data": {}
                    }
                })
            },
            {
                "data": json.dumps({
                    "kind": "task",
                    "action": "create",
                    "routine": {
                        "data": {}
                    },
                    "task": {
                        "text": "you"
                    },
                    "person": {
                        "name": "dude",
                        "data": {}
                    }
                })
            }
        ]

        self.daemon.process()
        self.daemon.process()

        mock_open.side_effect = [
            unittest.mock.mock_open(read_data='webhook_url: http://peeps').return_value
        ]

        mock_post.reset_mock()
        self.daemon.process()
        mock_post.assert_has_calls([
            unittest.mock.call("http://peeps", json={
                "text": "dude, you are now responsibile for the living room."
            }),
            unittest.mock.call().raise_for_status()
        ])

        mock_open.side_effect = [
            unittest.mock.mock_open(read_data='webhook_url: http://peeps').return_value
        ]

        mock_post.reset_mock()
        self.daemon.process()
        mock_post.assert_has_calls([
            unittest.mock.call("http://peeps", json={
                "text": "dude, it is good you put away your towel."
            }),
            unittest.mock.call().raise_for_status()
        ])

        mock_open.side_effect = [
            unittest.mock.mock_open(read_data='webhook_url: http://peeps').return_value
        ]

        mock_post.reset_mock()
        self.daemon.process()
        mock_post.assert_has_calls([
            unittest.mock.call("http://peeps", json={
                "text": "dude, 'mow the lawn' has been added to your ToDo list."
            }),
            unittest.mock.call().raise_for_status()
        ])

        mock_open.side_effect = [
            unittest.mock.mock_open(read_data='webhook_url: http://peeps').return_value
        ]

        mock_post.reset_mock()
        self.daemon.process()
        mock_post.assert_has_calls([
            unittest.mock.call("http://peeps", json={
                "text": "dude, these are your current todos:\nguys"
            }),
            unittest.mock.call().raise_for_status()
        ])

        mock_open.side_effect = [
            unittest.mock.mock_open(read_data='webhook_url: http://peeps').return_value
        ]

        mock_post.reset_mock()
        self.daemon.process()
        mock_post.assert_has_calls([
            unittest.mock.call("http://peeps", json={
                "text": "dude, time to hey."
            }),
            unittest.mock.call().raise_for_status()
        ])

        mock_open.side_effect = [
            unittest.mock.mock_open(read_data='webhook_url: http://peeps').return_value
        ]

        mock_post.reset_mock()
        self.daemon.process()
        mock_post.assert_has_calls([
            unittest.mock.call("http://peeps", json={
                "text": "dude, time to you."
            }),
            unittest.mock.call().raise_for_status()
        ])

    @unittest.mock.patch("service.time.time", unittest.mock.MagicMock(return_value=7))
    @unittest.mock.patch("builtins.open", create=True)
    @unittest.mock.patch("requests.post")
    @unittest.mock.patch("service.time.sleep")
    @unittest.mock.patch("traceback.format_exc")
    @unittest.mock.patch('builtins.print')
    def test_run(self, mock_print, mock_traceback, mock_sleep, mock_post, mock_open):

        mock_open.side_effect = [
            unittest.mock.mock_open(read_data='webhook_url: http://peeps').return_value
        ]

        self.daemon.redis.messages = [
            {
                "data": json.dumps({
                    "kind": "routine",
                    "action": "create",
                    "routine": {
                        "name": "ya",
                        "data": {
                            "text": "hey"
                        }
                    },
                    "person": {
                        "name": "dude",
                        "data": {}
                    }
                })
            },
            None
        ]

        mock_sleep.side_effect = [Exception("whoops"), Exception("adaisy")]
        mock_traceback.side_effect = ["spirograph", Exception("doh")]

        self.assertRaisesRegex(Exception, "doh", self.daemon.run)

        self.assertEqual(self.daemon.redis, self.daemon.pubsub)
        self.assertEqual(self.daemon.redis.channel, "stuff")

        mock_post.assert_has_calls([
            unittest.mock.call("http://peeps", json={
                "text": "dude, time to hey."
            }),
            unittest.mock.call().raise_for_status()
        ])

        mock_sleep.assert_called_with(0.7)

        mock_print.assert_has_calls([
            unittest.mock.call("whoops"),
            unittest.mock.call("spirograph"),
            unittest.mock.call("adaisy")
        ])