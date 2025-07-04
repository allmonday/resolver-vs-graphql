from fastapi import FastAPI
from .graphql import graphql_app
from .resolver import router as rest_router
from .resolver_dataclass import router as rest_router_dataclass
from .resolver_strawberry_type import router as rest_router_strawberry

app = FastAPI()
app.include_router(graphql_app, prefix="/graphql")
app.include_router(rest_router)
app.include_router(rest_router_dataclass, prefix="/dc")
app.include_router(rest_router_strawberry, prefix="/sb")

app.get('/base-test')
async def get_base():
    return {"message": "Welcome to the FastAPI application!"}