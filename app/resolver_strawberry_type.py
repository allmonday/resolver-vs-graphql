from pydantic.dataclasses import dataclass
from dataclasses import field
import datetime
from pydantic_resolve import LoaderDepend, ensure_subset
from fastapi import APIRouter
from pydantic_resolve import Resolver
from .graphql import batch_load_tasks, batch_load_stories, StoryBase, TaskBase, SprintBase
import strawberry

@strawberry.type
class Story(StoryBase):
    tasks: list[TaskBase] = field(default_factory=list)
    
    def resolve_tasks(self, loader=LoaderDepend(batch_load_tasks)):
        return loader.load(self.id)
    

@ensure_subset(StoryBase)
@strawberry.type
class SimpleStory():  # how to pick fields..
    id: int
    name: str
    point: int

    tasks: list[TaskBase] = field(default_factory=list)
    
    def resolve_tasks(self, loader=LoaderDepend(batch_load_tasks)):
        return loader.load(self.id)

@strawberry.type
class Sprint(SprintBase):
    stories: list[SimpleStory] = field(default_factory=list)
    
    def resolve_stories(self, loader=LoaderDepend(batch_load_stories)):
        return loader.load(self.id)

    
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
