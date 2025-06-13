# REST + Resolver vs. GraphQL

This project is a minimal demonstration of REST + resolver mode compares to GraphQL (Strawberry) based on FastAPI.

More comparison scenarios will be added gradually. Currently, only data construction is compared.

## Features

Compare two data access modes: REST + resolver and GraphQL
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


## Benchmark

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


### rest + resolver

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