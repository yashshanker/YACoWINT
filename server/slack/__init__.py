from slack_sdk import WebClient

from server.config import SLACK_OAUTH_TOKEN

client = WebClient(token=SLACK_OAUTH_TOKEN)
