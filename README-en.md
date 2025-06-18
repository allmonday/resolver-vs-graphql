# Resolver Pattern: A Better Choice than GraphQL in BFF Scenarios

[中文](./README.md)

This is a comparison project between Resolver pattern and GraphQL (strawberry) pattern based on FastAPI.

Focuses on the best development pattern for **internal frontend-backend API communication** scenarios

> Also applicable to BFF (Backend for Frontend) scenarios

> Assumes readers are familiar with GraphQL and RESTful, basic concepts will not be elaborated.

Comparison scenarios include:

- [x] Associated data fetching and construction
- [x] Query parameter passing
- [x] Frontend query method comparison
- [x] Post-processing data at each node, minimal cost view data construction (key focus)
- [x] Architecture and refactoring differences

## Introduction

GraphQL is an excellent API query tool, widely used in various scenarios. However, it's not a universal solution and encounters various problems in different scenarios.

This article specifically targets the common scenario of "internal frontend-backend API integration", analyzes the problems with GraphQL, and attempts to solve them one by one using the Resolver pattern based on `pydantic-resolve`.

Let me briefly introduce what the Resolver pattern is: It's a pattern that extends existing RESTful interfaces by introducing resolver and post-processing concepts, transforming originally "generic" RESTful interfaces into RPC-like interfaces that are customized for frontend pages.

In the Resolver pattern, we extend and combine data based on Pydantic classes (dataclass can also be used).

Here's a code example that demonstrates the ability to fetch associated data and generate view data after post-processing. The article will gradually explain all features and design intentions later.

```python
class Story(BaseStory):
    tasks: list[BaseTask] = []
    def resolve_tasks(self, loader=LoaderDepend(TaskLoader)):
        return loader.load(self.id)

@ensure_subset(BaseStory)
class SimpleStory(BaseModel):
    id: int
    point: int

    name: str
    def resolve_name(self, ancestor_context):
        return f'{ancestor_context["sprint_name"]} - {self.name}'

    tasks: list[BaseTask] = []
    def resolve_tasks(self, loader=LoaderDepend(TaskLoader)):
        return loader.load(self.id)

    done_perc: float = 0.0
    def post_done_perc(self):
        if self.tasks:
            done_count = sum(1 for task in self.tasks if task.done)
            return done_count / len(self.tasks) * 100
        else:
            return 0

class Sprint(BaseSprint):
    __pydantic_resolve_expose__ = {'name': 'sprint_name'}

    simple_stories: list[SimpleStory] = []
    def resolve_simple_stories(self, loader=LoaderDepend(StoryLoader)):
        return loader.load(self.id)


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
```

It can act as a BFF layer. Compared to traditional BFF tools, each layer introduces "post-processing" methods, making many aggregation calculations that originally required traversal expansion as easy as pie.

For more features of pydantic-resolve, please see [https://github.com/allmonday/pydantic-resolve](https://github.com/allmonday/pydantic-resolve)

## Getting Started

1. Install dependencies:
   ```sh
   python -m venv venv
   source venv/bin/activate  # Windows users please replace accordingly
   pip install -r requirements.txt
   ```
2. Start the service:
   ```sh
   uvicorn app.main:app --reload
   ```
3. Open [http://localhost:8000/graphql](http://localhost:8000/graphql) to access GraphQL playground.
4. Open [http://localhost:8000/docs](http://localhost:8000/docs) to view Resolver pattern

## 1. Data Fetching and Composition

```sh
uvicorn app.main:app --reload
```

Resolver itself is one of the two core features of GraphQL (the other being Query functionality). Through Resolver and dataloader, GraphQL can freely compose data.

In GraphQL, data definition can be graph-based, but in practice, for each specific query, the Query structure is tree-like. This is why queries cannot just write object names without providing specific fields.

This is a valid query:

```graphql
query MyQuery {
  sprints {
    id
    name
    start
    stories {
      id
      name
      owner
    }
  }
}
```

This is an invalid query:

```graphql
query MyQuery {
  sprints {
    id
    name
    start
    stories # playground will show red error
  }
}
```

Because if the stories field has object types, GraphQL doesn't know whether to continue expanding. Therefore, essentially, Query serves as the driving basis (configuration) for resolvers.

In the Resolver pattern, **Query statements are hardcoded into the code**, describing the desired combined data through inheritance and extension of pydantic classes.

> This approach loses query flexibility but becomes more suitable for RPC usage scenarios, namely the internal API integration scenarios mentioned at the beginning of the article, allowing data consumers to not bear the additional burden of query statements.
> How to determine if you're in this scenario? The simplest example is if your Query uses all fields of objects in specific entry points, then you probably belong to this scenario.

If you directly inherit BaseStory, all fields of BaseStory will be returned. You can also define a new class and declare the required fields in it. The `@ensure_subset` decorator is provided to additionally ensure that field names actually exist in BaseStory.

```python
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
```

Another difference from GraphQL concepts is that GraphQL's input is user query statements, while Resolver's input data is root node data. This might be a bit abstract to say directly, so a code comparison would be more illustrative:

In GraphQL, when users query sprints, the root data fetching happens within the sprints method.

```python
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
```

In Resolver, you need to provide root data and pass it to the `Resolver().resolve` method for parsing.

```python
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
```

This approach is very friendly to traditional RESTful interfaces. For example, an interface that originally returns flat BaseSprint objects can be seamlessly extended by simply modifying the response_model definition type.

```python
@router.get('/base-sprints', response_model=list[BaseSprint])
async def get_base_sprints():
    sprint1 = BaseSprint(
        id=1,
        name="Sprint 1",
        start=datetime.datetime(2025, 6, 12)
    )
    sprint2 = BaseSprint(
        id=2,
        name="Sprint 2",
        start=datetime.datetime(2025, 7, 1)
    )
    return [sprint1, sprint2] * 10
```

Of course, if you want to mimic GraphQL's style, it's also easy:

```python
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

# resolve
await Resolver().resolve(Query())
```

That's it.

Another capability of Resolver is handling self-referential type data. Because it doesn't need to provide Query statements like GraphQL, the construction logic for self-referential types (like Tree) can be completely managed by the backend.

For comparison, in GraphQL, queriers need to write very deep query statements like this because they don't know the actual depth:

```graphql
query MyQuery {
  tree {
    id
    children {
      id
      children {
        id
        children {
          id
          children {
            id
          }
        }
      }
    }
  }
}
```

There's also the possibility of insufficient depth description requiring further query adjustments.

In contrast, in Resolver or traditional RESTful mode, you just need to define the type and return value:

```python
@router.get('/tree', response_model=list[Tree])
async def get_tree():
    return [Tree(id=1, children=[
        Tree(id=2, children=[Tree(id=3)])
    ])]
```

Then a simple `curl http://localhost:8000/tree` gets it done. The depth problem is solved by backend-specific logic.

## Query Parameter Passing

```sh
uvicorn app_filter.main:app --reload
```

GraphQL can receive parameters at each node, with each resolver able to accept a set of params:

```python
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
```

However, in practice, for convenience of dynamic setting, they are generally managed centrally at the top:

```graphql
// query
query MyQuery($ids: [Int!]!) {
  sprints {
    start
    name
    id
    stories(ids: $ids) {
      id
      name
      owner
      point
      tasks {
        done
        id
        name
        owner
      }
    }
  }
}

// variables
{
  "ids": [1]
}
```

This implies a centralized parameter management design philosophy. Although parameter consumers are at various nodes, centralized access can be achieved through agreed variable aliases.

In Resolver mode, since queries are already "hardcoded" through code in advance, all parameters can be provided through global variables like context:

```python
class Sprint(BaseSprint):
    simple_stories: list[SimpleStory] = []
    async def resolve_simple_stories(self, context, loader=LoaderDepend(StoryLoader)):
        stories = await loader.load(self.id)
        stories = [s for s in stories if s.id in context['story_ids']]
        return stories

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
    return await Resolver(
        context={'story_ids': [1, 2, 3]},
    ).resolve([sprint1, sprint2] * 10)
```

This is formally equivalent to GraphQL's approach.

You might notice that filtering stories after fetching them in the provided ids usage is a very inefficient approach. A better way would obviously be to pass it to the Dataloader and let it complete the filtering during data fetching.

In GraphQL scenarios, Dataloader can only be configured through the params in the `loader.load(params)` method, so achieving this functionality requires some awkward writing, such as passing both id and ids together through params to the dataloader:

```python
  @strawberry.field
  async def stories2(self, info: strawberry.Info, ids: list[int]) -> List["Story"]:
      stories = await info.context.story_loader.load((self.id, ids))
      return stories
```

Then extract them inside the Dataloader, where the second parameter in the Tuple is actually quite redundant.

```python
async def batch_load_stories_with_filter(input: List[Tuple[int, List[int]]]) -> List[List["Story"]]:
    await asyncio.sleep(0.01)  # Simulate async DB call
    sprint_ids = [item[0] for item in input]
    story_ids = input[0][1] # need extra code to check the length of input
    sprint_id_to_stories: Dict[int, List[Story]] = {sid: [] for sid in sprint_ids}

    for s in STORIES_DB:
        if s["sprint_id"] in sprint_id_to_stories:
            if not story_ids or s["id"] in story_ids:
              sprint_id_to_stories[s["sprint_id"]].append(Story(id=s["id"], name=s["name"], owner=s["owner"], point=s["point"]))
    return [sprint_id_to_stories[sid] for sid in sprint_ids]
```

In the Resolver's multi-entry mode, this problem is very simple to solve. Just add the story_ids field directly to the Dataloader class:

```python
class StoryLoader(DataLoader):
    story_ids: List[int]
    async def batch_load_fn(self, sprint_ids: List[int]) -> List[List[BaseStory]]:
        await asyncio.sleep(0.01)  # Simulate async DB call
        sprint_id_to_stories = {sid: [] for sid in sprint_ids}
        for s in STORIES_DB:
            if s["sprint_id"] in sprint_id_to_stories:
                if not self.story_ids or s["id"] in self.story_ids:
                    sprint_id_to_stories[s["sprint_id"]].append(s)
        return [sprint_id_to_stories[sid] for sid in sprint_ids]
```

Then pass parameters directly in the Resolver() method:

```python
return await Resolver(
  loader_params={
      StoryLoader: {
          'story_ids': [1, 2, 3]
      },
  }
).resolve([sprint1, sprint2] * 10)
```

Additionally, `pydantic-resolve` provides parent to access parent node objects and `ancestor_context` to access specific fields from ancestor nodes. These are features that most current GraphQL frameworks don't support. For specific usage, please refer to [ancestor_context](https://allmonday.github.io/pydantic-resolve/api/#ancestor_context), [parent](https://allmonday.github.io/pydantic-resolve/api/#parent).

Summary:

| Parameter Type | Resolver | GraphQL |
| -------------- | -------- | ------- |
| Node           | Support  | Support |
| Global context | Support  | Support |
| Parent node    | Support  | Limited |
| Ancestor node  | Support  | None    |
| Dataloader     | Support  | None    |

## Frontend Query Method Differences

Using GraphQL, the frontend needs to maintain query statements. Although some people have hardcoded queries into RPC, these all require additional technical complexity.

Generally, no one would directly use fetch to build GraphQL queries; tools like Apollo client are typically used for querying.

Also, in the current TypeScript era, to generate frontend type definitions, tools like GraphQL code generator and GraphQL Typescript Generator are needed.

In Resolver mode, with FastAPI and pydantic, RESTful APIs can be directly generated into SDKs through OpenAPI 3.x, allowing frontends to directly call RPC methods and type definitions, such as openapi-ts.

OpenAPI 3.x is a very mature standard with high stability of various tools. There's also Swagger for viewing API definitions and return types.

Additionally, writing in Resolver mode is not complex, and it's even feasible for frontends to assemble data themselves (similar to BFF mode), though full-stack mode would be more convenient.

| API                     | Resolver | GraphQL           |
| ----------------------- | -------- | ----------------- |
| Provide Query Statement | No       | Yes               |
| Provide Types           | Support  | Support (complex) |
| Generate SDK            | Support  | Support (complex) |
| Frontend Awareness      | Strong   | Relatively weak   |

## Post-processing Data at Each Node, Easy View Data Construction

```sh
uvicorn app_post_process.main:app --reload
```

If the previous comparisons were minor skirmishes, then post-processing capability is the biggest difference between Resolver and GraphQL patterns.

Let me first demonstrate what post-processing is. The following method does several things:

- Modify story.name, adding sprint.name as prefix
- Calculate story.done_perc based on story.tasks

```python
def post_process(sprints: List[Sprint]) -> List[Sprint]:
    for sprint in sprints:
        sprint_name = sprint.name

        for story in sprint.simple_stories:
            story.name = f"{sprint_name} - {story.name}"
            if story.tasks:
                done_count = sum(1 for task in story.tasks if task.done)
                done_perc = done_count / len(story.tasks) * 100
            else:
                done_perc = 0
            story.done_perc = done_perc

            for task in story.tasks:
                ...

    return sprints
```

You can see that if this code had more post-processing requirements or more node layers, readability would decline rapidly.

In Resolver mode, this can be expressed as:

```python
@ensure_subset(BaseStory)
class SimpleStory(BaseModel):
    ...

    name: str
    def resolve_name(self, ancestor_context):
        # Because name already has data, it can be operated even in resolver.
        # ancestor_context represents variables defined in direct ancestor nodes. Here it refers to sprint.name
        return f'{ancestor_context["sprint_name"]} - {self.name}'

    done_perc: float = 0.0
    def post_done_perc(self):
        if self.tasks:
            done_count = sum(1 for task in self.tasks if task.done)
            return done_count / len(self.tasks) * 100
        else:
            return 0

class Sprint(BaseSprint):
    __pydantic_resolve_expose__ = {'name': 'sprint_name'}

    simple_stories: list[SimpleStory] = []
    def resolve_simple_stories(self, loader=LoaderDepend(StoryLoader)):
        return loader.load(self.id)
```

Ancestor node fields are passed through specific ancestor_context without polluting locals.

And done_perc relies on local calculation at the node level.

Maintainability improves significantly.

---

In GraphQL, limited by its Query functionality, post-processing capability can be said to be basically impossible to implement.

Many GraphQL frameworks at most support a post-processing middleware at the root node, where developers can do some processing after all data is fetched.

In Resolver mode, each node can provide post hooks for additional processing after descendant data processing is completed.

This is the resolve process, expanding data layer by layer from the ROOT node:

![](./images/resolve.png)

This is the post-processing process. When all data obtained through resolvers is complete, there's a layer-by-layer return triggering process:

![](./images/post-process.png)

Here's the significance of post-processing methods:

- Can modify fields at each layer node after its descendant fields are all processed, or read descendant node data to implement various statistics or aggregation operations
  - For example, calculate Story completion rate based on Task.done status
- Can move node data across layers, such as moving Task nodes under Sprint nodes
- Can perform cross-layer statistical aggregation, such as counting how many Tasks there are in Sprint by skipping the Story layer transfer

Unfortunately, in GraphQL's design, the concept of post-processing doesn't exist.

Using GraphQL can only experience a top-down data fetching process. There's no way to implement post-processing at each layer. For example, I cannot know the content of tasks in advance at the story node.

And the Query-driven resolver approach constrains the possibility of adding new fields in post-processing methods.

For example, in Resolver mode, you can use the post_done_perc method to get `self.tasks` information and then calculate the done ratio:

```python
@ensure_subset(BaseStory)
class SimpleStory(BaseModel):  # how to pick fields..
    id: int
    name: str
    point: int

    tasks: list[BaseTask] = []
    def resolve_tasks(self, loader=LoaderDepend(TaskLoader)):
        return loader.load(self.id)

    done_perc: float = 0.0
    def post_done_perc(self):
        if self.tasks:
            done_count = sum(1 for task in self.tasks if task.done)
            return done_count / len(self.tasks) * 100
        else:
            return 0.0
```

In GraphQL, even if node-level post-processing were somehow supported, for data like done_perc that depends on tasks, if the Query only declares `done_perc` but not `tasks`, then done_perc would error due to lack of tasks data when Query drives the query. If forced to support this, some static analysis process would be needed to analyze the dependency of done_perc on tasks in advance.

It's precisely the post-processing capability that gives Resolver the ability to easily build view data, making secondary construction and modification based on data possible.

Here are some post-processing features supported by Resolver mode:

| Post-processing Capability                                                                             | Resolver           | GraphQL |
| ------------------------------------------------------------------------------------------------------ | ------------------ | ------- |
| Modify current field data [post](https://allmonday.github.io/pydantic-resolve/api/#post)               | Support            | None    |
| Read current node's descendant data                                                                    | Support            | None    |
| Send data to descendant nodes [collector](https://allmonday.github.io/pydantic-resolve/api/#collector) | Support            | None    |
| Hide fields in serialization                                                                           | Support (pydantic) | None    |

You can also check the code in `app_post_process/rest.py` for more examples.

## Architecture Design Differences

This section discusses the experience of using GraphQL in project iterations.

The biggest obstacle when refactoring GraphQL is not daring to modify existing schemas because you don't know which fields in the schema have been queried and which haven't.

This means that as long as fields have been provided, the basic structure is constrained and can't be easily adjusted, otherwise you'd have to audit all queries to confirm the situation.

Due to GraphQL's flexibility, different teams use it in different ways. Some people build backend-friendly schemas based on ER models, like in our demo, while others build frontend-friendly schemas based on frontend view models, incorporating many post-processing processes. But these two approaches can't be combined because GraphQL lacks powerful post-processing capabilities.

**Summary**: Because GraphQL lacks good post-processing methods, it leads to schema design falling into the dilemma of ER model priority vs view model priority.

Generally, GraphQL schemas provided by platforms follow the former, designed close to ER models, delegating the process of converting to frontend view data to the queriers.

In Resolver mode, because the view model consumed by the frontend is actually maintained on the backend, developers have a clear understanding of field usage.

Thanks to RESTful's multi-entry points and good inheritance and extension mechanisms, adjustments to each interface won't affect other interfaces.

Architecturally, Resolver mode matches the objective situation where structural stability gradually decreases in the ER model -> view model process.

Base types in ER models are very stable. Business objects are assembled through inheritance and associated data as needed, then adjusted into view objects through post-processing.

Thus, Resolver mode can smoothly build various specific view data required by business while conforming to ER models.

**Summary**: Resolver mode assembles data through specific business based on ER models, then uses post-processing to fine-tune data into expected view data, providing good readability and maintainability.

## Bonus

How to add post-processing methods to GraphQL?

Here's an interesting approach: remove all resolve methods, remove all Dataloaders, and directly use GraphQL query results as input data.

Then keep all post methods to convert data into expected view objects.

> Because pydantic itself has the ability to load nested data

```python
@ensure_subset(BaseStory)
class SimpleStory(BaseModel):  # how to pick fields..
    __pydantic_resolve_collect__ = {'tasks': ('task_count', 'task_count2')}  # send tasks to collectors

    id: int
    name: str
    point: int
    tasks: list[BaseTask]

    done_perc: float = 0.0
    def post_done_perc(self):
        if self.tasks:
            done_count = sum(1 for task in self.tasks if task.done)
            return done_count / len(self.tasks) * 100
        else:
            return 0

class Sprint(BaseSprint):
    simple_stories: list[SimpleStory]
    task_count: int = 0
    def post_task_count(self, collector=Collector(alias='task_count', flat=True)):
        return len(collector.values())  # this can be optimized further


@router.get('/sprints', response_model=list[Sprint])
async def get_sprints():
    sprints = await graphql_api_provider.query_sprints() # read from graphql res.data
    sprints = [Sprint.model_validate(s) for s in sprints]
    return await Resolver().resolve(sprints)
```

## Discussion on Resolver Pattern Design Philosophy

The core of Resolver pattern is designing data structures based on business requirements.

When we remove all resolver and post methods, what remains is the business objects we want to define.

These methods are just instructions on how to obtain/calculate this data.

**Data structure is the most important asset**, acquisition methods can be freely replaced/optimized.

```python
class SimpleStory(BaseModel):  # how to pick fields..
    id: int
    name: str
    point: int

    tasks: list[BaseTask]
    done_perc: float

class Sprint(BaseSprint):

    simple_stories: list[SimpleStory]
    task_count: int
```

Let's recap the design process from the beginning:

Through ER models, we can define relationships between data, which are the "constraints" for all data combinations. For example, Sprint -> Story follows a 1:N relationship.

Therefore, we can add stories field to Sprint.

By adding default values, we allow this object to ignore missing values during initialization because data will be set in subsequent processing. This processing might happen in resolver or post.

> In other words, if your initialization data already contains tasks data, then `tasks: list[BaseTask]` doesn't need to set `[]` default value. Remember pydantic supports loading nested data.

```python
class SimpleStory(BaseModel):  # how to pick fields..
    id: int
    name: str
    point: int

    tasks: list[BaseTask] = []
    done_perc: float = 0

class Sprint(BaseSprint):
    simple_stories: list[SimpleStory] = []
```

Then set resolver methods for these values to be queried:

```python
class SimpleStory(BaseModel):  # how to pick fields..
    id: int
    name: str
    point: int

    tasks: list[BaseTask] = []
    def resolve_tasks(self, loader=LoaderDepend(TaskLoader)):
        return loader.load(self.id)

    done_perc: float = 0

class Sprint(BaseSprint):
    simple_stories: list[SimpleStory] = []
    def resolve_simple_stories(self, loader=LoaderDepend(StoryLoader)):
        return loader.load(self.id)
```

Some values need to wait for all tasks data to be fetched before being calculated, so they need to be set through post methods:

```python
@ensure_subset(BaseStory)
class SimpleStory(BaseModel):  # how to pick fields..
    __pydantic_resolve_collect__ = {'tasks': ('task_count', 'task_count2')}  # send tasks to collectors

    id: int
    name: str
    point: int
    tasks: list[BaseTask]

    done_perc: float = 0.0
    def post_done_perc(self):
        # self.tasks is filled with real values
        if self.tasks:
            done_count = sum(1 for task in self.tasks if task.done)
            return done_count / len(self.tasks) * 100
        else:
            return 0

class Sprint(BaseSprint):
    simple_stories: list[SimpleStory]
    task_count: int = 0
    def post_task_count(self, collector=Collector(alias='task_count', flat=True)):
        return len(collector.values())  # this can be optimized further
```

> If there are values that need to be calculated based on post calculation outputs, pydantic-resolve provides `post_default_handler` to handle this.

**Therefore, pydantic objects define the expected data structure (interface design), while resolver and post methods just provide specific implementation methods.**

> The reason for recommending Dataloader is that it balances query complexity and runtime efficiency best. But as mentioned earlier, when there are better/faster ways to obtain associated data (like optimized ORM queries), we can immediately complete code refactoring by just removing resolver and Dataloader.
> Pydantic can load nested objects, so there's no need to limit yourself to returning flat object data in resolvers. (Nested dicts are ok too)

## Resolver vs GraphQL Pattern Comparison

| Feature               | Resolver Pattern                                       | GraphQL Pattern                                                 |
| --------------------- | ------------------------------------------------------ | --------------------------------------------------------------- |
| Interface Design      | Based on URL paths and HTTP methods                    | Based on single endpoint and typed Schema                       |
| Data Fetching         | Separate interfaces, internal code static construction | Single request can fetch multiple resources, on-demand querying |
| Flexibility           | Fixed return structure, can flexibly define fields     | Frontend can customize query fields, higher flexibility         |
| Documentation & Types | Swagger/OpenAPI3.0, supports SDK generation            | Auto-generated Playground, strong type validation               |

This project implements both Resolver and GraphQL interfaces for comparison and learning the usage and pros/cons of both.

### GraphQL

Flexible, queryable, suitable for scenarios requiring flexible data querying

![image](https://github.com/user-attachments/assets/cf80c282-b3bc-472d-a584-bbb73a213d4d)

### Resolver

Uses [pydantic-resolve](https://github.com/allmonday/pydantic-resolve)

Uses fewer technology stacks to build equivalent data structures, suitable for internal API integration scenarios

Can use tools like https://github.com/hey-api/openapi-ts to generate frontend SDKs

![image](https://github.com/user-attachments/assets/bb922804-5ed8-429c-b907-a92bf3c4b3ed)

## Benchmark

Finally, using Resolver pattern doesn't affect interface performance and can actually become faster.

You can easily refactor GraphQL code using Resolver, and this process won't have too much mental burden but will actually streamline various codes.

Therefore, for **internal frontend-backend API integration** scenarios, Resolver pattern is a reliable choice.

`ab -c 50 -n 1000`

### graphql

```shell
Server Software:        uvicorn
Server Hostname:        localhost
Server Port:            8000

Document Path:          /graphql
Document Length:        5303 bytes

Concurrency Level:      50
Time taken for tests:   3.630 seconds
Complete requests:      1000
Failed requests:        0
Total transferred:      5430000 bytes
Total body sent:        395000
HTML transferred:       5303000 bytes
Requests per second:    275.49 [#/sec] (mean)
Time per request:       181.498 [ms] (mean)
Time per request:       3.630 [ms] (mean, across all concurrent requests)
Transfer rate:          1460.82 [Kbytes/sec] received
                        106.27 kb/s sent
                        1567.09 kb/s total

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0    0   0.2      0       1
Processing:    31  178  14.3    178     272
Waiting:       30  176  14.3    176     270
Total:         31  178  14.4    179     273
```

### Resolver

```shell
Server Software:        uvicorn
Server Hostname:        localhost
Server Port:            8000

Document Path:          /sprints
Document Length:        4621 bytes

Concurrency Level:      50
Time taken for tests:   2.194 seconds
Complete requests:      1000
Failed requests:        0
Total transferred:      4748000 bytes
HTML transferred:       4621000 bytes
Requests per second:    455.79 [#/sec] (mean)
Time per request:       109.700 [ms] (mean)
Time per request:       2.194 [ms] (mean, across all concurrent requests)
Transfer rate:          2113.36 [Kbytes/sec] received

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0    0   0.3      0       1
Processing:    30  107  10.9    106     138
Waiting:       28  105  10.7    104     138
Total:         30  107  11.0    106     140
```
