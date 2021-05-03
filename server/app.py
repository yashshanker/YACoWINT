from fastapi import Depends, FastAPI, Request
from sqlalchemy.orm import Session

from server.storage import crud, models, session

models.Base.metadata.create_all(bind=session.engine)

app = FastAPI()


@app.post("/notify")
def notify(db: Session = Depends(session.get_db)):
    regions = crud.get_regions(db)
    return [{"state": region.state, "district": region.district} for region in regions]


@app.post("/subscribe")
async def subscribe(request: Request, db: Session = Depends(session.get_db)):
    data = await request.form()
    return data
