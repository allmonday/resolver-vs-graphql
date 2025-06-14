import asyncio
import datetime
from typing import List, Dict
import strawberry
from strawberry.dataloader import DataLoader
from strawberry.fastapi import GraphQLRouter, BaseContext

# Mock database for tasks
TASKS_DB = [
    {"id": 1, "name": "Task 1", "owner": 201, "done": False, "story_id": 1},
    {"id": 2, "name": "Task 2", "owner": 202, "done": True, "story_id": 2},
    {"id": 3, "name": "Task 3", "owner": 203, "done": False, "story_id": 1},
]

# Mock database for stories
STORIES_DB = [
    {"id": 1, "name": "Story 1", "owner": 101, "point": 5, "sprint_id": 1},
    {"id": 2, "name": "Story 2", "owner": 102, "point": 8, "sprint_id": 1},
    {"id": 3, "name": "Story 3", "owner": 103, "point": 3, "sprint_id": 2},
]

async def batch_load_tasks(story_ids: List[int]) -> List[List["Task"]]:
    await asyncio.sleep(0.01)  # Simulate async DB call
    story_id_to_tasks: Dict[int, List[Task]] = {sid: [] for sid in story_ids}
    for t in TASKS_DB:
        if t["story_id"] in story_id_to_tasks:
            story_id_to_tasks[t["story_id"]].append(Task(id=t["id"], name=t["name"], owner=t["owner"], done=t["done"]))
    return [story_id_to_tasks[sid] for sid in story_ids]

async def batch_load_stories(sprint_ids: List[int]) -> List[List["Story"]]:
    await asyncio.sleep(0.01)  # Simulate async DB call
    sprint_id_to_stories: Dict[int, List[Story]] = {sid: [] for sid in sprint_ids}
    for s in STORIES_DB:
        if s["sprint_id"] in sprint_id_to_stories:
            sprint_id_to_stories[s["sprint_id"]].append(Story(id=s["id"], name=s["name"], owner=s["owner"], point=s["point"]))
    return [sprint_id_to_stories[sid] for sid in sprint_ids]

# Custom context class inheriting from BaseContext
class CustomContext(BaseContext):
    def __init__(self):
        self.task_loader = DataLoader(load_fn=batch_load_tasks)
        self.story_loader = DataLoader(load_fn=batch_load_stories)
        self.name = "tangkikodo"

# Dependency that returns the custom context
async def get_context_dependency() -> CustomContext:
    return CustomContext()


@strawberry.type
class Task:
    id: int
    name: str
    owner: int
    done: bool

@strawberry.type
class Story:
    id: int
    name: str
    owner: int
    point: int
    @strawberry.field
    async def tasks(self, info: strawberry.Info) -> List["Task"]:
        tasks = await info.context.task_loader.load(self.id)
        return tasks

@strawberry.type
class Sprint:
    id: int
    name: str
    start: datetime.datetime
    task_count: int = 0
    @strawberry.field
    async def stories(self, info: strawberry.Info, ids: list[int]) -> List["Story"]:
        stories = await info.context.story_loader.load(self.id)
        return [s for s in stories if s.id in ids]


@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "hello world"

    @strawberry.field
    async def sprints(self) -> List[Sprint]:
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
        return [sprint1, sprint2] * 10

schema = strawberry.Schema(query=Query)

graphql_app = GraphQLRouter(
    schema,
    context_getter=get_context_dependency
)
