import asyncio
from pydantic import BaseModel
from typing import List
import datetime
from aiodataloader import DataLoader
from typing import List
from pydantic_resolve import LoaderDepend, ensure_subset
from fastapi import APIRouter
from pydantic_resolve import Resolver
from pydantic import Field

class BaseTask(BaseModel):
    id: int
    name: str
    owner: int
    done: bool

class BaseStory(BaseModel):
    id: int
    name: str
    owner: int
    point: int

class BaseSprint(BaseModel):
    id: int
    name: str
    start: datetime.datetime

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

class TaskLoader(DataLoader):
    async def batch_load_fn(self, story_ids: List[int]) -> List[List[BaseTask]]:
        await asyncio.sleep(0.01)  # Simulate async DB call
        story_id_to_tasks = {sid: [] for sid in story_ids}
        for t in TASKS_DB:
            if t["story_id"] in story_id_to_tasks:
                story_id_to_tasks[t["story_id"]].append(t)
        return [story_id_to_tasks[sid] for sid in story_ids]

class StoryLoader(DataLoader):
    async def batch_load_fn(self, sprint_ids: List[int]) -> List[List[BaseStory]]:
        await asyncio.sleep(0.01)  # Simulate async DB call
        sprint_id_to_stories = {sid: [] for sid in sprint_ids}
        for s in STORIES_DB:
            if s["sprint_id"] in sprint_id_to_stories:
                sprint_id_to_stories[s["sprint_id"]].append(s)
        return [sprint_id_to_stories[sid] for sid in sprint_ids]


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

class Sprint(BaseSprint):
    stories: list[Story] = []
    def resolve_stories(self, loader=LoaderDepend(StoryLoader)):
        return loader.load(self.id)

    simple_stories: list[SimpleStory] = []
    def resolve_simple_stories(self, loader=LoaderDepend(StoryLoader)):
        return loader.load(self.id)


# yet another way
class Query(BaseModel):
    sprints: list[Sprint] = []
    async def resolve_sprints(self):
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
        return [sprint1, sprint2]

class Tree(BaseModel):
    id: int
    children: list['Tree'] = Field(default_factory=list)
    
router = APIRouter()

@router.get('/sprints', response_model=list[Sprint])
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
    return await Resolver().resolve([sprint1, sprint2] * 10)

@router.get('/tree', response_model=list[Tree])
async def get_tree():
    return [Tree(id=1, children=[
        Tree(id=2, children=[Tree(id=3)])
    ])]