# Resolver vs. GraphQL  （wip)

[EN](./README-en.md)

这是一个基于 FastAPI 的 Resolver 模式和 GraphQL (strawberry) 模式的比较项目

关注的是**项目内部前后端之间 API 调用**场景下的最佳开发模式。 （也适用于 BFF backend for frontend 这种场景）

> 默认读者熟悉 GraphQL 和 RESTful，这里不会过多介绍。

比较的场景有以下这些：

- [x] 关联数据的获取和构建
- [ ] 查询参数的传递
- [ ] 前端查询方式的比较
- [ ] 数据在每一个节点的后处理, 最小成本构建试图数据
- [ ] 架构和重构上的区别

## 介绍

GraphQL 是一个优秀的 API 查询工具， 广泛应用在许多场景中使用。 但它也不是银弹， 根据具体场景不同， 也存在着各式各样的问题。
这里专门针对 `项目内部前后端 API 对接 ` 这种常见场景， 分析 GraphQL 存在的问题， 并尝试使用基于 `pydantic-resolve` 的 Resolver 模式来逐一解决。

先简单介绍一下什么是 Resolver 模式， 这是一种基于当前已有的 RESTful 接口， 通过引入 resolver 的概念， 将原本 "通用" 的 RESTful 接口， 扩展构建成类似 RPC 的， 为前端页面专供数据的接口。

在 Resolver 模式中， 我们基于 Pydantic 类来扩展，组合数据

比如 Story 可以直接继承 BaseStory 所有的字段， 也可以使用 `@ensure_subset(BaseStory)` 加上自定义字段来实现类似 GraphQL 中挑选字段的功能。

并且可以通过 resolve method + DataLoader 来层层拼装数据。

用通俗的说法就是， 通过定义 pydantic 类 + 提供入口的根数据， 使得接口可以提供精确满足前端需求的视图数据。

它可以扮演类似 BFF 层的角色， 而且比其他传统的 BFF 工具， 它在构建视图数据的过程中比较有创意的，给每层节点都引入了 “后处理” 的方法， 使得许多原本需要遍历展开的汇总计算都变得易如反掌。

具体的细节会在后续的对比中说明。

更多关于 pydantic-resolve 的功能请移步 [https://github.com/allmonday/pydantic-resolve](https://github.com/allmonday/pydantic-resolve)


## 启动项目

1. 安装依赖：
   ```sh
   python -m venv venv
   source venv/bin/activate  # windows 自行替换
   pip install -r requirement.txt
   ```
2. 启动服务：
   ```sh
   uvicorn app.main:app --reload
   ```
3. 打开 [http://localhost:8000/graphql](http://localhost:8000/graphql) 访问 GraphQL playground。
4. 打开 [http://localhost:8000/docs](http://localhost:8000/docs) 查看 Resolver 模式



## 1. 数据获取和组合

```sh
uvicorn app.main:app --reload
```

Resolver 本身就是 GraphQL 的两个核心特色之一 （另一个是 Query 功能）， 通过 Resolver 和 dataloader， GraphQL 能够自由组合数据

GraphQL 中， 数据的定义可以是 Graph 的， 但事实上具体到每个查询， Query 的结构是树状的， 这也是为何不允许查询中只写对象名字但是不提供具体字段的原因

这是合法的查询

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

这是不合法的查询

```graphql
query MyQuery {
  sprints {
    id
    name
    start
    stories  // plaground 会飘红报错
  }
}
```

因为如果 stories 的字段还有对象类型的话， GraphQL 无法知道是否要继续展开。 因此本质上 Query 就是 Resolver 们的驱动查询的依据（配置）。

而在 Resolver 模式中， **Query 语句被固化到了代码中**， 通过 pdyantic class 的继承和扩展来描述自己所期望的组合数据。

> 这种做法丧失了查询的灵活， 会更贴近于 RPC 的使用场景， 即文章开头所说的项目内部 API 对接场景， 让数据使用者不需要再额外承担一份查询语句的负担。
> 那如何判断自己是不是这种场景？ 最简单的例子是如果你的 Query 把特定入口中的对象的所有字段都用到了， 那么你大概就属于这个场景了。

如果直接继承 BaseStory 那么所有 BaseStory 的字段都会被返回， 也可以自己定义一个新的类， 把所需的字段申明在里面， 同时提供了 `@ensure_subset` 装饰器来额外保证字段名是 BaseStory 中真实存在的。

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

另一个和 GraphQL 概念不同的地方是， GraphQL 的输入是用户查询语句， Resolver 的输入数据是根节点数据， 直接这么说也许有点抽象， 从代码上对比会比较形象一些：

在 GraphQL 中，当用户查询 sprints 时， 根数据的获取是发生在 sprints 方法内的。

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

在 Resolver 中， 则需要提供一个根数据, 将其提供给 `Resolver().resolve` 方法中解析。

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

这种方式对传统 RESTful 接口会很友好, 比如原本返回 flat 的 BaseSprint 对象的接口， 只要简单修改 response_model 定义类型就能无缝扩展了。

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

当然， 如果你想模仿 GraphQL 那种形式的话， 也很容易：

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

就好了。

Resolver 的另一个能力是处理自引用类型数据的能力， 
因为不用像 GraphQL 那样提供 Query 语句， 所以自引用类型（比如 Tree） 这类数据的构建逻辑可以完全交给后端来管理

作为对比， 在 GraphQL 中， 查询者因为不知道真实深度， 就需写出类似 

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

这种非常深的查询语句， 同时也可能出现描述深度不够， 要继续调整查询的可能。

作为对比在 Resolver 或者说传统 RESTful 模式下, 只要定义好类型和返回值：

```python
@router.get('/tree', response_model=list[Tree])
async def get_tree():
    return [Tree(id=1, children=[
        Tree(id=2, children=[Tree(id=3)])
    ])]
```

然后简单 `curl http://localhost:8000/tree` 就搞定了。 深度问题交给后端具体逻辑去解决。

## 查询参数的传递 (draft)

```sh
uvicorn app_filter.main:app --reload
```

graphql 可以在每个节点接收参数，每个 resolver 都能够接受一组 params

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

不过在实际使用中， 为了方便动态设置， 一般都会放到顶部集中管理：

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

这里隐含了一种参数集中化管理的设计思路，虽然参数的消费者在各个节点上，但是可以通过约定变量别名来集中获取。

Resolver 模式下， 因为查询本来就是通过代码提前“固化” 下来的， 所以可以通过 context 这种全局变量来提供所有的参数：

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

在形式上和 GraphQL 的做法是等价的。

到这里你也许注意到提供的 ids 的用法中， 获取了 stories 之后再通过代码来过滤是一种非常低效的做法， 更好的方式显然是传递给 Data






resolver 可以在 resolver 的 context 中集中管理查询参数

同时还支持 parent, ancestor 参数的获取

另外还为 dataloader 提供了参数设置

table 比较

## 前端查询方式的差别 (draft)

graphql 前端需要维护 query 语句, 也有人把 query 固化成了 rpc， 但是这些都是堆积额外技术复杂度的做法

resolver 借助 openapi3.0 可以生成 sdk， 直接提供 rpc 方法和类型定义

这里有个隐藏约定， 后端需要清晰知道前端所需的数据结构， 当然如果是全栈开发的话就没有这种问题了。

rersolver 模式的书写本身也不复杂， 甚至让前端自己过来拼装 （类似 bff）也很容易

## 数据在每个节点的后处理，轻松构建视图数据 (draft)

先说明后处理方法的意义：
- 可以在每层节点上修改字段， 或者读取子孙节点的数据， 来实现各种统计或者聚合操作
- 可以对节点数据做跨层的移动， 调整

使用 graphql 只能经历一个数据从上到下的获取过程， 想要实现每层的后处理是没有办法的， 比如我在 story 节点中是无法提前知道 tasks 中的内容的。

并且 query 驱动 resolver 的方式约束了后处理方法中， 新增字段的可能。

tip： 这里尝试使用 graphql 来曲线救国实现一些后处理字段

Resolver 借助 post_method 这个额外的 hook 方法，可以解决上述的所有问题， post hook 触发时， 节点的子孙节点都已经获取完毕

此时 story 是可以清楚知道自己 tasks 节点的所有数据的。

另外还有跨层级的 collect 设计， 比如让所有的 tasks 节点都移动到 sprint 节点之中。

## 架构和重构的区别 (draft)

graphql 重构的时候， 最大的障碍是不知道 schema 中哪些字段被查询了， 哪些没有被查询。

这就导致只要是提供过的字段， 基本结构就被约束住不能轻易调整了， 否则就要 audit 所有查询确认情况。

在 Resolver 中， 因为实际查询是维护在后端的， 所以字段的使用情况开发是清清楚楚的。

另外得益于 rest 的多入口和继承，扩展机制， 可以做到每个接口的调整， 不会影响到其他接口

在架构上， Resolver 机制匹配了 ER 模型 -> 视图模型过程中， 结构不变型逐渐递减的客观情况

Base 类型稳定， 通过继承获取， 关联数据按照需要来拼装 (resolve), 而多变的视图层需求则让 post 阶段去做各种微调。

Resolver 方式可以做到在符合 ER 模型的基础上， 流畅地构建出各种个样的业务所需的具体视图数据

GraphQL 因为缺失了良好的后处理方法， 会导致 schema 设计陷入 ER model 优先还是 view model 优先两难的境地。

tips：更多的案例

## Resolver 与 GraphQL 模式对比

| 特性       | Resolver 模式          | GraphQL 模式                     |
| ---------- | -------------------------------- | -------------------------------- |
| 接口设计   | 基于 URL 路径和 HTTP 方法        | 基于单一端点和类型化 Schema      |
| 数据获取   | 单独接口，内部代码静态构建       | 单次请求可获取多资源，按需查询   |
| 灵活性     | 固定返回结构，也能灵活定义字段   | 前端可自定义查询字段，灵活性更高 |
| 文档与类型 | Swagger/OpenAPI3.0, 支持生成 SDK | 自动生成 Playground，类型强校验  |

本项目同时实现了 Resolver 和 GraphQL 两种接口，便于对比和学习两者的使用方式及优缺点。

### GraphQL

灵活， 可以查询，适合需要对数据做灵活查询的场景

![image](https://github.com/user-attachments/assets/cf80c282-b3bc-472d-a584-bbb73a213d4d)

### Resolver

使用 [pydantic-resolve](https://github.com/allmonday/pydantic-resolve)

使用更少的技术栈， 来构建等价的数据结构， 适合项目内部 api 对接的场景

可以使用 https://github.com/hey-api/openapi-ts 之类的工具生成前端 sdk

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
