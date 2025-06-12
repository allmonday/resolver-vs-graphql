from fastapi import FastAPI
from .schema import graphql_app
from .rest import router as rest_router

app = FastAPI()
app.include_router(graphql_app, prefix="/graphql")
app.include_router(rest_router)