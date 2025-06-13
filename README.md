# REST + resolver vs. GraphQL

[EN](./README-en.md)

本项目是一个基于 FastAPI 的 REST + resolver 模式和 GraphQL (trawberry) 模式的比较项目

后续会逐步添加更多的比较场景， 当前只比较了数据构建相关的部分。

## Features

- Strawberry GraphQL 端点：`/graphql`
- 比较 REST + resolver 和 GraphQL（Schema）两种数据访问模式

在 rest.py 中， 我们使用扩展 Pydantic 类的方式来组合数据

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

## Getting Started

1. 安装依赖：
   ```sh
   pip install -r requirement.txt
   ```
2. 启动服务：
   ```sh
   uvicorn app.main:app --reload
   ```
3. 打开 [http://localhost:8000/graphql](http://localhost:8000/graphql) 访问 GraphQL playground。
4. 打开 [http://localhost:8000/docs#/default/get_sprints_sprints_get](http://localhost:8000/docs#/default/get_sprints_sprints_get) 查看 REST + resolver 模式

## 项目结构

- `app/schema.py`：Strawberry GraphQL schema
- `app/main.py`：FastAPI 应用入口

## REST + resolver 与 GraphQL 模式对比

| 特性       | REST 模式                        | GraphQL（Schema）模式            |
| ---------- | -------------------------------- | -------------------------------- |
| 接口设计   | 基于 URL 路径和 HTTP 方法        | 基于单一端点和类型化 Schema      |
| 数据获取   | 单独接口，内部组合               | 单次请求可获取多资源，按需查询   |
| 灵活性     | 固定返回结构，也能灵活定义字段   | 前端可自定义查询字段，灵活性更高 |
| 文档与类型 | Swagger/OpenAPI3.0, 支持生成 SDK | 自动生成 Playground，类型强校验  |

本项目同时实现了 REST + resolver 和 GraphQL 两种接口，便于对比和学习两者的使用方式及优缺点。

### GraphQL

灵活， 可以查询，适合需要对数据做灵活查询的场景

![image](https://github.com/user-attachments/assets/cf80c282-b3bc-472d-a584-bbb73a213d4d)

### REST + resolver

使用 [pydantic-resolve](https://github.com/allmonday/pydantic-resolve)

使用更少的技术栈， 来构建等价的数据结构， 适合项目内部 api 对接的场景

可以使用 https://github.com/hey-api/openapi-ts 之类的工具生成前端 sdk

![image](https://github.com/user-attachments/assets/bb922804-5ed8-429c-b907-a92bf3c4b3ed)


