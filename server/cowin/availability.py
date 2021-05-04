from datetime import datetime, timedelta

import requests

from server import config


def district_by_calendar(district_id, weeks=config.TRACK_WEEKS_DEFAULT):
    today = datetime.now(config.TZ)
    available = []

    for i in range(weeks):
        date = (today + timedelta(days=i)).strftime(r"%d-%m-%Y")
        response = requests.get(
            "https://cdn-api.co-vin.in/api/v2/appointment/"
            "sessions/public/calendarByDistrict",
            params=dict(district_id=district_id, date=date),
        ).json()

        # If there are no centers, can stop here itself
        if not response["centers"]:
            break

        for center in response["centers"]:
            available_sessions = [
                session
                for session in center["sessions"]
                if session["available_capacity"] and session["slots"]
            ]
            if available_sessions:
                available.append({**center, "sessions": available_sessions})

    return available
