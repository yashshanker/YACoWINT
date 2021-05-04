from slack_sdk import WebClient
from slack_sdk.signature import SignatureVerifier

from server.config import SLACK_OAUTH_TOKEN, SLACK_SIGNING_SECRET

client = WebClient(token=SLACK_OAUTH_TOKEN)
signature_verifier = SignatureVerifier(SLACK_SIGNING_SECRET)
