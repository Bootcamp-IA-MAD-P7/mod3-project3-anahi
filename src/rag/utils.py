import re


def make_topic_slug(topic: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", topic.lower().strip()).strip("-")
