from fastapi import FastAPI
from .graphql import graphql_app
from .rest import router as rest_router
from .rest_dataclass import router as rest_dc_router

app = FastAPI()
app.include_router(graphql_app, prefix="/graphql")
app.include_router(rest_router)
app.include_router(rest_dc_router, prefix='/dc')

app.get('/base-test')
async def get_base():
    return {"message": "Welcome to the FastAPI application!"}