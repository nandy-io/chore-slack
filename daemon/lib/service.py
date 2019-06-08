"""
Main module for daemon
"""

import os
import time
import json
import redis
import requests
import traceback

class Daemon(object):
    """
    Main class for daemon
    """

    AREA_STATEMENTS = {
        "create": "you are now responsibile for %s.",
        "wrong": "I'm sorry but %s is not up to snuff.",
        "right": "thank you for %s is now up to snuff."
    }

    ACT_STATEMENTS = {
        "negative": "I'm sorry but you did not %s.",
        "positive": "thank you for you did %s."
    }

    ACTION_STATEMENTS = {
        "pause": "you do not have to %s yet.",
        "unpause": "you do have to %s now.",
        "skip": "you do not have to %s.",
        "unskip": "you do have to %s.",
        "complete": "thank you. You did %s",
        "uncomplete": "I'm sorry but you did not %s yet.",
        "expire": "your time to %s has expired.",
        "unexpire": "your time to %s has not expired."
    }

    TODO_STATEMENTS = {
        "create": "at some point, %s."
    }

    TODO_STATEMENTS.update(ACTION_STATEMENTS)

    ROUTINE_STATEMENTS = {
        "create": "time to %s."
    }

    ROUTINE_STATEMENTS.update(ACTION_STATEMENTS)

    def __init__(self):

        self.sleep = float(os.environ['SLEEP'])

        self.redis = redis.StrictRedis(host=os.environ['REDIS_HOST'], port=int(os.environ['REDIS_PORT']))
        self.channel = os.environ['REDIS_CHANNEL']

        with open("/opt/service/secret/slack.json", "r") as slack_file:
            self.slack_api = json.load(slack_file)["url"]

        self.pubsub = None

    def subscribe(self):
        """
        Subscribes to the channel on Redis
        """

        self.pubsub = self.redis.pubsub()
        self.pubsub.subscribe(self.channel) 

    @staticmethod
    def text(model):
        return model["data"].get("text", model["name"])

    def say(self, text, name=None):

        message = {
            "text": f"{name}, {text}" if name else text
        }

        requests.post(self.slack_api, json=message).raise_for_status()

    def process(self):
        """
        Processes a message from the channel if later than the daemons start time
        """

        message = self.pubsub.get_message()

        if not message or not isinstance(message["data"], str):
            return

        data = json.loads(message['data'])

        if data["kind"] == "area":

            self.say(
                self.AREA_STATEMENTS[data["action"]] % self.text(data["area"]),
                data["person"]["name"]
            )

        elif data["kind"] == "act":

            self.say(
                self.ACT_STATEMENTS[data["act"]["status"]] % self.text(data["act"]),
                data["person"]["name"]
            )

        elif data["kind"] == "todo":

            self.say(
                self.TODO_STATEMENTS[data["action"]] % self.text(data["todo"]),
                data["person"]["name"]
            )

        elif data["kind"] == "todos":

            text = ["these are your current todos:"]

            for todo in data["todos"]:
                text.append(self.text(todo))

            self.say(
                "\n".join(text),
                data["person"]["name"]
            )

        elif data["kind"] == "routine":

            if data["action"] != "remind":
                self.say(
                    self.ROUTINE_STATEMENTS[data["action"]] % self.text(data["routine"]),
                    data["person"]["name"]
                )

        elif data["kind"] == "task":

            if data["action"] != "remind":
                self.say(
                    self.ROUTINE_STATEMENTS[data["action"]] % data["task"]["text"],
                    data["person"]["name"]
                )

    def run(self):
        """
        Runs the daemon
        """

        self.subscribe()

        while True:
            try:
                self.process()
                time.sleep(self.sleep)
            except Exception as exception:
                print(str(exception))
                print(traceback.format_exc())
