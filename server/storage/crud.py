from sqlalchemy.orm import Session

from server.storage import models


def get_regions(db: Session):
    return db.query(models.TrackingRegion).all()


def add_region(db: Session, state: str, district: str):
    region = models.TrackingRegion(state=state, district=district)

    db.add(region)
    db.commit()
    db.refresh(region)

    return region


def add_subscription(db: Session, slack_id: str, state: str, district: str):
    region = (
        db.query(models.TrackingRegion)
        .filter_by(state=state, district=district)
        .one_or_none()
    )
    if region is None:
        region = add_region(db, state, district)

    # Check if user is already subscribed to this region
    for subscriber in region.subscribers:
        if subscriber.slack_id == slack_id:
            return subscriber

    subscription = models.SlackUserSubscription(slack_id=slack_id, region_id=region.id)

    db.add(subscription)
    db.commit()
    db.refresh(subscription)

    return subscription
