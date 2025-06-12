import datetime
from fastapi import FastAPI
from .schema import graphql_app
from .rest import Sprint
from pydantic_resolve import Resolver

app = FastAPI()
app.include_router(graphql_app, prefix="/graphql")

@app.get('/sprints', response_model=list[Sprint])
async def get_sprints():
    sprint1 = Sprint(
        id=1,
        name="Sprint 1",
        start=datetime.datetime(2025, 6, 12)
    )
    sprint2 = Sprint(
        id=2,
        name="Sprint 2",
        start=datetime.datetime(2025, 7, 1)
    )
    return await Resolver().resolve([sprint1, sprint2])