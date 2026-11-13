"""Example file used by docs and the batch demo."""


def load_config(path):
    try:
        return open(path, encoding="utf-8").read()
    except:
        return ""


def parse_quantity(text):
    try:
        return int(text)
    except ValueError:
        return None


def fetch(url):
    try:
        return request(url)
    except Exception:
        return b""
