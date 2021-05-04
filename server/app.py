import json

import requests
from fastapi import Depends, FastAPI, Request, Response, status
from sqlalchemy.orm import Session

from server.logger import log
from server.slack import client, modals
from server.storage import crud, models, session

models.Base.metadata.create_all(bind=session.engine)

app = FastAPI()


def state_options():
    response = requests.get(
        "https://cdn-api.co-vin.in/api/v2/admin/location/states"
    ).json()
    options = [
        {
            "text": {"type": "plain_text", "text": state["state_name"]},
            "value": f"state-{state['state_id']}",
        }
        for state in response.get("states")
    ]

    return options


def district_options(state_id):
    response = requests.get(
        f"https://cdn-api.co-vin.in/api/v2/admin/location/districts/{state_id}"
    ).json()
    options = [
        {
            "text": {"type": "plain_text", "text": district["district_name"]},
            "value": f"district-{district['district_id']}",
        }
        for district in response.get("districts")
    ]

    return options


@app.post("/interact")
async def interact(request: Request, db: Session = Depends(session.get_db)):
    data = await request.form()
    payload = json.loads(data["payload"])
    view = payload["view"]
    log.info("Interact payload: %s", json.dumps(payload))

    if payload["type"] == "view_submission":
        metadata = json.loads(view["private_metadata"])
        state = metadata["state_option"]["text"]["text"]
        district = metadata["district_option"]["text"]["text"]

        # Attempt to add a subscription
        subscription = crud.add_subscription(db, payload["user"]["id"], state, district)

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
        prefix_offset = len("state-")
        options = district_options(state_option["value"][prefix_offset:])

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
    return [
        {
            "state": region.state,
            "district": region.district,
            "subscribers": [s.slack_id for s in region.subscribers],
        }
        for region in regions
    ]


@app.post("/subscribe")
async def subscribe(request: Request, db: Session = Depends(session.get_db)):
    data = await request.form()
    client.views_open(trigger_id=data["trigger_id"], view=modals.subscription_modal())
    return Response(status_code=status.HTTP_200_OK)
