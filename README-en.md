# Resolver Pattern: A Better Alternative to GraphQL in BFF.

[中文](./README.md)

This is a comparative project between the Resolver pattern and the GraphQL (strawberry) pattern based on FastAPI.

It focuses on the optimal development pattern for **internal frontend to backend API calls within a project** (also applicable to the BFF - backend for frontend scenario).

> It is assumed that the reader is familiar with GraphQL and RESTful, so the basic concepts will not be repeated here.

The comparison scenarios include:

- [x] Retrieval and construction of associated data
- [x] Passing of query parameters
- [x] Comparison of frontend query methods
- [x] Post - processing of data at each node to construct view data at minimum cost
- [x] Differences in architecture and refactoring

## Introduction

GraphQL is an excellent API query tool widely used in various scenarios. However, it is not a one - size - fits - all solution and may encounter various problems in different scenarios. This article specifically analyzes the problems of GraphQL in the common scenario of "internal frontend to backend API docking within a project" and attempts to solve them one by one using the Resolver pattern based on `pydantic-resolve`.

Let's first briefly introduce what the Resolver pattern is: It is a pattern that, based on existing RESTful interfaces, extends the originally "generic" RESTful interfaces into RPC - like interfaces customized for frontend pages by introducing the concept of resolvers.

In the Resolver pattern, we extend and combine data based on Pydantic classes.

For example, a `Story` can directly inherit all fields from `BaseStory`, or it can use the `@ensure_subset(BaseStory)` decorator and add custom fields to achieve a function similar to field selection in GraphQL.

Data can also be assembled layer by layer through resolve methods and DataLoader.

Put simply, by defining Pydantic classes and providing a root data entry, the interface can precisely meet the frontend's requirements for view data.

It can act as a BFF layer, and compared with traditional BFF tools, it is more innovative in the process of constructing view data - it introduces a "post - processing" method for each layer of nodes, making many summary calculations that originally required traversal and expansion much easier.

The specific details will be explained in the subsequent comparison.

For more features of `pydantic-resolve`, please refer to [https://github.com/allmonday/pydantic-resolve](https://github.com/allmonday/pydantic-resolve).

## Starting the Project

1. Install dependencies:
   ```sh
   python -m venv venv
   source venv/bin/activate  # Replace this for Windows users
   pip install -r requirement.txt
   ```
2. Start the service:
   ```sh
   uvicorn app.main:app --reload
   ```
3. Open [http://localhost:8000/graphql](http://localhost:8000/graphql) to access the GraphQL playground.
4. Open [http://localhost:8000/docs](http://localhost:8000/docs) to view the Resolver pattern.

## 1. Data Retrieval and Combination

```sh
uvicorn app.main:app --reload
```

Resolver is one of the two core features of GraphQL (the other is the Query function). Through Resolver and DataLoader, GraphQL can freely combine data.

In GraphQL, data can be defined in a graph structure, but in fact, for each specific query, the structure of the Query is tree - like. This is why it is not allowed to only write the object name in the query without providing specific fields.

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
    stories  // The playground will show a red error
  }
}
```

Because if the `stories` field contains object - type fields, GraphQL does not know whether to continue expanding. Therefore, in essence, the Query is the basis (configuration) for driving the Resolvers' queries.

In the Resolver pattern, **the Query statement is hard - coded in the code**. The desired combined data is described through the inheritance and extension of Pydantic classes.

> This approach sacrifices the flexibility of queries and is more suitable for RPC - like scenarios, i.e., the internal API docking scenario mentioned at the beginning of the article, which relieves data users from the burden of an additional query statement. So how do you determine if you are in this scenario? The simplest example is if your Query uses all the fields of an object in a specific entry, then you are probably in this scenario.

If you directly inherit from `BaseStory`, all fields of `BaseStory` will be returned. You can also define a new class and declare the required fields in it. At the same time, the `@ensure_subset` decorator is provided to additionally ensure that the field names actually exist in `BaseStory`.

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

Another difference from the GraphQL concept is that the input of GraphQL is the user's query statement, while the input data of Resolver is the root - node data. This may sound a bit abstract, but it will be clearer through a code comparison.

In GraphQL, when the user queries `sprints`, the retrieval of the root data occurs within the `sprints` method.

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

In the Resolver pattern, you need to provide root data and pass it to the `Resolver().resolve` method for parsing.

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

This approach is very friendly to traditional RESTful interfaces. For example, for an interface that originally returned flat `BaseSprint` objects, you can seamlessly expand it by simply modifying the definition of the `response_model` type.

```python
@router.get('/base - sprints', response_model=list[BaseSprint])
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

Of course, if you want to mimic the GraphQL style, it's also easy:

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

That's all.

Another ability of Resolver is to handle self - referencing type data. Since there is no need to provide a Query statement like in GraphQL, the construction logic of self - referencing type data (such as a `Tree`) can be completely managed by the backend.

In contrast, in GraphQL, because the querier doesn't know the actual depth, they need to write a very deep query statement like this:

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

There is also a possibility that the described depth is insufficient and the query needs to be adjusted.

In contrast, in the Resolver or traditional RESTful pattern, you only need to define the type and return value:

```python
@router.get('/tree', response_model=list[Tree])
async def get_tree():
    return [Tree(id=1, children=[
        Tree(id=2, children=[Tree(id=3)])
    ])]
```

Then simply run `curl http://localhost:8000/tree` and you're done. The depth issue is left to the specific backend logic to handle.

## Passing of Query Parameters

```sh
uvicorn app_filter.main:app --reload
```

GraphQL can receive parameters at each node, and each resolver can accept a set of params.

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

However, in actual use, for the convenience of dynamic setting, parameters are generally managed centrally at the top:

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

This implies a design idea of centralized parameter management. Although the consumers of the parameters are at various nodes, they can be obtained centrally by agreeing on variable aliases.

In the Resolver pattern, since the query is "hard - coded" in the code in advance, all parameters can be provided through a global variable like `context`:

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

This is equivalent to the GraphQL approach in form.

By now, you may have noticed that in the usage of providing `ids`, filtering the `stories` after retrieval through code is a very inefficient method. A better way is obviously to pass the parameters to the DataLoader and let it complete the filtering during the data retrieval process.

In the GraphQL scenario, the DataLoader can only set parameters through the `loader.load(params)` method. So, to achieve this function, there are only some rather awkward ways of writing, such as passing both the `id` and `ids` to the DataLoader through `params`.

```python
  @strawberry.field
  async def stories2(self, info: strawberry.Info, ids: list[int]) -> List["Story"]:
      stories = await info.context.story_loader.load((self.id, ids))
      return stories
```

Then, inside the DataLoader, the parameters need to be split. At this time, the second parameter in the Tuple is actually redundant.

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

In the multi - entry Resolver pattern, this problem is very easy to solve. Simply add a field `story_ids` to the DataLoader class.

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

Then, directly pass the parameters in the `Resolver()` method.

```python
return await Resolver(
  loader_params={
      StoryLoader: {
          'story_ids': [1, 2, 3]
      },
  }
).resolve([sprint1, sprint2] * 10)
```

In addition, `pydantic-resolve` also provides `parent` to obtain the parent - node object and `ancestor_context` to obtain specific fields of ancestor nodes. These are functions generally not supported by current GraphQL frameworks. For specific usage methods, please refer to [ancestor_context](https://allmonday.github.io/pydantic-resolve/api/#ancestor_context) and [parent](https://allmonday.github.io/pydantic-resolve/api/#parent).

To summarize:

| Parameter Type | Resolver  | GraphQL         |
| -------------- | --------- | --------------- |
| Node           | Supported | Supported       |
| Global context | Supported | Supported       |
| Parent node    | Supported | Limited support |
| Ancestor node  | Supported | Not supported   |
| Dataloader     | Supported | Not supported   |

## Differences in frontend Query Methods

When using GraphQL, the frontend needs to maintain query statements. Although some people have hard - coded queries into RPC, these methods require additional technical complexity.

Generally, no one directly uses `fetch` to construct GraphQL queries. Usually, tools like Apollo Client are used for queries.

In the current era of popular TypeScript, to generate frontend type definitions, code - generation tools such as GraphQL Code Generator and GraphQL TypeScript Generator are also needed.

In the Resolver pattern, with the help of FastAPI and Pydantic, the RESTful API can be directly converted into an SDK through OpenAPI 3.x. The frontend can directly call RPC methods and use type definitions. For example, `openapi - ts`.

The OpenAPI 3.x standard is a very mature standard, and the stability of various tools is also high. There is also Swagger to view API definitions and return types.

In addition, the writing of the Resolver pattern is not complicated. It is even feasible for the frontend to assemble data itself (similar to the BFF pattern). Of course, it will be more convenient in a full - stack scenario.

| API                                   | Resolver     | GraphQL                           |
| ------------------------------------- | ------------ | --------------------------------- |
| Provide Query statement               | Not required | Required                          |
| Provide types                         | Supported    | Supported (relatively cumbersome) |
| Generate SDK                          | Supported    | Supported (relatively complex)    |
| Frontend awareness after modification | Strong       | Relatively weak                   |

## Post - Processing of Data at Each Node, Easily Constructing View Data

If the previous comparisons were just minor differences, then the post - processing ability is the most significant difference between the Resolver pattern and the GraphQL pattern.

In GraphQL, limited by its Query function, the post - processing ability is basically non - existent.

Most GraphQL frameworks only support a post - processing middleware at the root node, that is, after all data is retrieved, developers can perform some processing.

In the Resolver pattern, each node can provide a post - hook for additional processing after the processing of its descendant data is completed.

Here, let's first explain the significance of the post - processing method:

- On each layer of nodes, after the processing of its descendant fields is completed, fields can be modified, or data from descendant nodes can be read to implement various statistical or aggregation operations. For example, calculate the completion rate of a `Story` based on the `done` status of `Task`.
- Data can be moved across layers. For example, move the `Task` node under the `Sprint` node.
- Cross - layer statistical aggregation can be performed on nodes. For example, in a `Sprint`, the number of `Task` can be counted without going through the `Story` layer.

Unfortunately, the concept of post - processing does not exist in the design of GraphQL.

When using GraphQL, there is only a top - down data retrieval process, and it is impossible to implement post - processing at each layer. For example, in a `story` node, it is impossible to know the content of `tasks` in advance.

Moreover, the way Query drives resolvers restricts the possibility of adding new fields in the post - processing method.

For example, in the Resolver pattern, the `post_done_perc` method can be used to obtain information from `self.tasks` and then calculate the `done` percentage.

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

In GraphQL, even if node - level post - processing is supported, for data like `done_perc` that depends on `tasks`, if only `done_perc` is declared in the Query but `tasks` is not, then when the Query drives the query, `done_perc` will report an error due to the lack of `tasks` data. If you want to support it, a static analysis process is needed to analyze the dependency of `done_perc` on `tasks` in advance.

It is precisely the post - processing ability that enables the Resolver to easily construct view data and makes secondary construction and modification of data possible.

Here are some post - processing functions supported by the Resolver pattern:

| Post - Processing Ability                                                                                   | Resolver             | GraphQL |
| ----------------------------------------------------------------------------------------------------------- | -------------------- | ------- |
| Modify current field data [post](https://allmonday.github.io/pydantic-resolve/api/#post)                    | Supported            | None    |
| Read descendant data of the current node                                                                    | Supported            | None    |
| Transfer data to a descendant node [collector](https://allmonday.github.io/pydantic-resolve/api/#collector) | Supported            | None    |
| Hide fields during serialization                                                                            | Supported (pydantic) | None    |

You can also view more examples in the code `app_post_process/rest.py`.

## Differences in Architecture Design

In this section, let's talk about the experience of using GraphQL in project iteration.

When refactoring with GraphQL, the biggest obstacle is the reluctance to modify existing schemas because it is unknown which fields in the schema are being queried and which are not.

This means that once a field is provided, its basic structure is restricted and cannot be easily adjusted. Otherwise, all queries need to be audited to confirm the situation.

Due to the flexibility of GraphQL, different teams use it in different ways. Some people construct backend - friendly schemas based on the ER model, as in our demo. Others construct frontend - friendly schemas by integrating many post - processing processes based on the frontend view model. However, because GraphQL lacks a powerful post - processing ability, these two approaches cannot be combined.

**Summary**: Due to the lack of a good post - processing method, GraphQL schema design is caught in a dilemma between prioritizing the ER model and the view model.

Generally, the GraphQL schemas provided by platforms follow the former approach, i.e., they are designed in a way that is close to the ER model. The process of converting to frontend view data is left to the querying party.

In the Resolver pattern, since the view model consumed by the frontend is actually maintained on the backend, developers clearly know how the fields are being used.

Thanks to the multiple entry points of RESTful and the good inheritance and extension mechanisms, adjustments to each interface will not affect other interfaces.

In terms of architecture, the Resolver pattern matches the objective situation where the structural stability gradually decreases during the process of transforming from the ER model to the view model.

The Base types of the ER model are very stable. Business objects are assembled as needed through inheritance and associated data, and then view objects are adjusted through the post - processing process.

Therefore, the Resolver approach can smoothly construct various specific view data required by the business on the basis of conforming to the ER model.

**Summary**: The Resolver pattern assembles data based on specific business requirements on the basis of the ER model and then fine - tunes the data into the desired view data through post - processing. It provides good readability and maintainability.

## Easter Egg

So, how can we add post - processing methods to GraphQL?

Here is an interesting idea: Delete all resolve methods and all DataLoaders, and directly use the GraphQL query results as input data.

Then, keep all post methods and let them convert the data into the desired view objects.

> Since Pydantic itself has the ability to load nested data.

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

## Comparison between Resolver and GraphQL Patterns

| Feature                 | Resolver Pattern                                          | GraphQL Pattern                                                          |
| ----------------------- | --------------------------------------------------------- | ------------------------------------------------------------------------ |
| Interface Design        | Based on URL paths and HTTP methods                       | Based on a single endpoint and typed Schema                              |
| Data Retrieval          | Separate interfaces, static construction in internal code | Multiple resources can be retrieved in a single request, query on demand |
| Flexibility             | Fixed return structure, can also flexibly define fields   | frontend can customize query fields, higher flexibility                  |
| Documentation and Types | Swagger/OpenAPI 3.0, supports SDK generation              | Automatically generates Playground, strong type validation               |

This project implements both Resolver and GraphQL interfaces to facilitate the comparison and learning of the usage methods, advantages, and disadvantages of the two.

### GraphQL

Flexible, can perform queries, suitable for scenarios where flexible data queries are required.

![image](https://github.com/user-attachments/assets/cf80c282-b3bc-472d-a584-bbb73a213d4d)

### Resolver

Uses [pydantic-resolve](https://github.com/allmonday/pydantic-resolve).

Uses fewer technology stacks to construct equivalent data structures, suitable for internal API docking scenarios within a project.

Tools like [https://github.com/hey-api/openapi-ts](https://github.com/hey-api/openapi-ts) can be used to generate frontend SDKs.

![image](https://github.com/user-attachments/assets/bb922804-5ed8-429c-b907-a92bf3c4b3ed)

## Benchmark

Finally, using the Resolver pattern does not affect the performance of the interface; instead, it can make it faster.

You can easily refactor GraphQL code using the Resolver pattern. This process does not require much mental effort and will even streamline various codes.

Therefore, for the scenario of **internal frontend to backend API docking within a project**, the Resolver pattern is a reliable choice.

`ab -c 50 -n 1000`

### GraphQL

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
