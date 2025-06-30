import asyncio
from pydantic.dataclasses import dataclass
from dataclasses import field
from typing import List
import datetime
from aiodataloader import DataLoader
from typing import List
from pydantic_resolve import LoaderDepend, ensure_subset
from fastapi import APIRouter
from pydantic_resolve import Resolver
import strawberry
from .graphql import batch_load_tasks, batch_load_stories, StoryBase, TaskBase, SprintBase


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

# ---- business model ------
@dataclass
class Story(StoryBase):
    tasks: list[TaskBase] = field(default_factory=list)
    
    def resolve_tasks(self, loader=LoaderDepend(batch_load_tasks)):
        return loader.load(self.id)
    

@ensure_subset(StoryBase)
@dataclass
class SimpleStory():  # how to pick fields..
    id: int

    name: str
    def resolve_name(self, ancestor_context):
        return f'{ancestor_context["sprint_name"]} - {self.name}'

    point: int

    tasks: list[TaskBase] = field(default_factory=list)
    
    def resolve_tasks(self, loader=LoaderDepend(batch_load_tasks)):
        return loader.load(self.id)

@dataclass
class Sprint(SprintBase):
    __pydantic_resolve_expose__ = {'name': 'sprint_name'}
    stories: list[SimpleStory] = field(default_factory=list)
    
    def resolve_stories(self, loader=LoaderDepend(batch_load_stories)):
        return loader.load(self.id)


# yet another way, you can even mimic the GraphQL response structure (data, error)
@dataclass
class Query:
    sprints: list[Sprint] = field(default_factory=list)
    
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
    
router = APIRouter()

@router.get('/plain-sprints', response_model=list[SprintBase])
async def get_plain_sprints():
    sprint1 = SprintBase(
        id=1,
        name="Sprint 1",
        start=datetime.datetime(2025, 6, 12)
    )
    sprint2 = SprintBase(
        id=2,
        name="Sprint 2",
        start=datetime.datetime(2025, 7, 1)
    )
    return [sprint1, sprint2]

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
