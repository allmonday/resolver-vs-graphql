# REST + Resolver vs. GraphQL

This project is a minimal demonstration of REST + resolver mode and GraphQL (Strawberry) based on FastAPI.

More comparison scenarios will be added gradually. Currently, only data construction is compared.

## Features

Compare two data access modes: REST + resolver and GraphQL (Schema)
- [x] data orchestration
- [ ] post-process / modification
- [ ] frontend client

## Getting Started

1. Install dependencies:
   ```sh
   pip install -r requirement.txt
   ```
2. Start the service:
   ```sh
   uvicorn app.main:app --reload
   ```
3. Open [http://localhost:8000/graphql](http://localhost:8000/graphql) to access the GraphQL playground.
4. Open [http://localhost:8000/docs#/default/get_sprints_sprints_get](http://localhost:8000/docs#/default/get_sprints_sprints_get) to view the REST + resolver mode.

in rest.py， we chose to directly extend the pydantic class itself.

```python

# ---- business model ------
class Story(BaseStory):
    tasks: list[BaseTask] = []
    def resolve_tasks(self, loader=LoaderDepend(TaskLoader)):
        return loader.load(self.id)


@ensure_subset(BaseStory)
class SimpleStory(BaseModel):  # how to pick fields..
    id: int
    name: str
    point: int

    tasks: list[BaseTask] = []
    def resolve_tasks(self, loader=LoaderDepend(TaskLoader)):
        return loader.load(self.id)

# or
class Sprint(BaseSprint):
    stories: list[Story] = []
    def resolve_stories(self, loader=LoaderDepend(StoryLoader)):
        return loader.load(self.id)

    simple_stories: list[SimpleStory] = []
    def resolve_simple_stories(self, loader=LoaderDepend(StoryLoader)):
        return loader.load(self.id)
```

## Project Structure

- `app/schema.py`: Strawberry GraphQL schema
- `app/main.py`: FastAPI application entry point

## Comparison: REST + Resolver vs. GraphQL Mode

| Feature       | REST Mode                                          | GraphQL (Schema) Mode                                    |
| ------------- | -------------------------------------------------- | -------------------------------------------------------- |
| API Design    | Based on URL paths and HTTP methods                | Single endpoint, typed schema                            |
| Data Fetching | Separate endpoints, internal composition           | Fetch multiple resources in one request, query as needed |
| Flexibility   | Fixed return structure, can define fields flexibly | Frontend can customize query fields, more flexible       |
| Docs & Types  | Swagger/OpenAPI3.0, SDK generation supported       | Auto-generated Playground, strong type checking          |

This project implements both REST + resolver and GraphQL interfaces for easy comparison and learning of their usage and pros/cons.

### GraphQL

Flexible, supports queries, suitable for scenarios requiring flexible data queries.

![image](https://github.com/user-attachments/assets/cf80c282-b3bc-472d-a584-bbb73a213d4d)

### REST + Resolver

boosted by [pydantic-resolve](https://github.com/allmonday/pydantic-resolve)

Uses a smaller tech stack to build equivalent data structures, suitable for internal API integration scenarios.

You can use tools like https://github.com/hey-api/openapi-ts to generate frontend SDKs.

![image](https://github.com/user-attachments/assets/bb922804-5ed8-429c-b907-a92bf3c4b3ed)
