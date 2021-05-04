import json

from fastapi import Depends, FastAPI, Request, Response, status
from sqlalchemy.orm import Session

from server import config
from server.cowin.availability import district_by_calendar
from server.cowin.metadata import district_options, state_options
from server.slack import client, modals, signature_verifier
from server.storage import crud, models, session
from server.utils import format_centers_markdown

models.Base.metadata.create_all(bind=session.engine)

app = FastAPI()


@app.get("/health")
def health():
    return Response(status_code=status.HTTP_200_OK)


@app.post("/subscribe")
async def subscribe(request: Request, db: Session = Depends(session.get_db)):
    if not signature_verifier.is_valid_request(await request.body(), request.headers):
        return Response(status_code=status.HTTP_403_FORBIDDEN)

    data = await request.form()
    if data.get("text", "").lower().strip() == "unsub":
        crud.remove_subscriptions(db, data["user_id"])
        return Response("Unsubscribed!", status_code=status.HTTP_200_OK)

    client.views_open(trigger_id=data["trigger_id"], view=modals.subscription_modal())
    return Response(status_code=status.HTTP_200_OK)


@app.post("/interact")
async def interact(request: Request, db: Session = Depends(session.get_db)):
    if not signature_verifier.is_valid_request(await request.body(), request.headers):
        return Response(status_code=status.HTTP_403_FORBIDDEN)

    data = await request.form()
    payload = json.loads(data["payload"])
    view = payload["view"]

    if payload["type"] == "view_submission":
        metadata = json.loads(view["private_metadata"])

        # Attempt to add a subscription
        subscription = crud.add_subscription(
            db,
            payload["user"]["id"],
            metadata["state_option"]["value"],
            metadata["district_option"]["value"],
        )

        return {
            "response_action": "update",
            "view": modals.successful_subscription_modal(subscription),
        }

    for action in payload["actions"]:
        if action["action_id"] == "state_select":
            client.views_update(
                view_id=view["id"],
                hash=view["hash"],
                view=modals.subscription_modal(state_option=action["selected_option"]),
            )

        if action["action_id"] == "district_select":
            state_option = json.loads(view["private_metadata"]).get("state_option")
            client.views_update(
                view_id=view["id"],
                hash=view["hash"],
                view=modals.subscription_modal(
                    state_option=state_option,
                    district_option=action["selected_option"],
                ),
            )

    return Response(status_code=status.HTTP_200_OK)


@app.post("/options")
async def options(request: Request):
    if not signature_verifier.is_valid_request(await request.body(), request.headers):
        return Response(status_code=status.HTTP_403_FORBIDDEN)

    data = await request.form()
    payload = json.loads(data["payload"])
    action_id = payload["action_id"]
    entered_value = payload["value"].lower()
    options = []

    if action_id == "state_select":
        options = state_options()

    elif action_id == "district_select":
        metadata = json.loads(payload["view"]["private_metadata"])
        state_option = metadata["state_option"]
        options = district_options(state_option["value"])

    return dict(
        options=[
            option
            for option in options
            if option["text"]["text"].lower().startswith(entered_value)
        ]
    )


@app.post("/notify")
def notify(db: Session = Depends(session.get_db)):
    regions = crud.get_regions(db)

    for region in regions:
        if not len(region.subscriptions):
            continue

        available_centers = district_by_calendar(region.district_id)
        if not available_centers:
            continue

        centers_markdown = format_centers_markdown(available_centers)
        for subscription in region.subscriptions:
            intro = (
                f"<@{subscription.slack_id}>, found a few slots "
                f"over the next {config.TRACK_WEEKS_DEFAULT} week(s):\n"
            )
            response = client.conversations_open(users=[subscription.slack_id])
            channel_id = response["channel"]["id"]
            client.chat_postMessage(channel=channel_id, text=intro + centers_markdown)
