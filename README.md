# RESTful + resolver vs. GraphQL

[EN](./README-en.md)

这是一个基于 FastAPI 的 RESTful + resolver 模式和 GraphQL (strawberry) 模式的比较项目

关注的是**项目内部前后端之间 API 调用**的最佳开发模式。

> 这里不会去过多介绍 GraphQL (strawberry) 的概念和使用方式，

比较的场景有这些：

- [x] 关联数据的获取和构建
- [ ] 数据在每一个节点的后处理, 最小成本构建试图数据
- [ ] 前端查询方式的简化
- [ ] 重构上的区别

## 介绍

GraphQL 是一个优秀的 API 查询工具， 被人广泛在各个场景中使用。 但他也不是银弹， 根据具体使用的场景不同， 也存在着各式各样的问题， 这里专门针对 `项目内部前后端 API 对接 ` 这种常见场景， 分析 GraphQL 存在的问题， 并且尝试使用基于 `pydantic-resolve` 的 RESTful + resolver 模式来逐一解决。

先简单介绍一下什么是 RESTful + Resolver 模式， 这是一种基于当前已有的 RESTful 接口， 通过引入 GraphQL resolver 的概念， 将原本 "通用" 的 RESTful 接口， 扩展构建成类似 RPC 的， 为前端页面专供数据的接口。

在 RESTful + resolver 模式中， 我们基于 Pydantic 类来扩展，组合数据

比如 Story 可以直接继承 BaseStory 所有的字段， 也可以使用 `@ensure_subset(BaseStory)` 加上自定义字段来实现类似 GraphQL 中挑选字段的功能。

并且可以通过 resolve method + DataLoader 来层层拼装数据。

用通俗的说法就是， 通过定义 pydantic 类 + 提供入口的根数据， 使得接口可以提供精确满足前端需求的视图数据。

它可以扮演类似 BFF 层的角色， 而且比其他传统的 BFF 工具， 它在构建视图数据的过程中比较有创意的，给每层节点都引入了 “后处理” 的方法， 使得许多原本需要遍历展开的汇总计算都变得一如反掌。

更多关于 pydantic-resolve 的功能请移步 [https://github.com/allmonday/pydantic-resolve](https://github.com/allmonday/pydantic-resolve)

## 启动

1. 安装依赖：
   ```sh
   pip install -r requirement.txt
   ```
2. 启动服务：
   ```sh
   uvicorn app.main:app --reload
   ```
3. 打开 [http://localhost:8000/graphql](http://localhost:8000/graphql) 访问 GraphQL playground。
4. 打开 [http://localhost:8000/docs#/default/get_sprints_sprints_get](http://localhost:8000/docs#/default/get_sprints_sprints_get) 查看 RESTful + resolver 模式

## 项目结构

- `app/graphql.py`
- `app/RESTful.py`

## RESTful + resolver 与 GraphQL 模式对比

| 特性       | RESTful + Resolver 模式          | GraphQL 模式                     |
| ---------- | -------------------------------- | -------------------------------- |
| 接口设计   | 基于 URL 路径和 HTTP 方法        | 基于单一端点和类型化 Schema      |
| 数据获取   | 单独接口，内部代码静态构建       | 单次请求可获取多资源，按需查询   |
| 灵活性     | 固定返回结构，也能灵活定义字段   | 前端可自定义查询字段，灵活性更高 |
| 文档与类型 | Swagger/OpenAPI3.0, 支持生成 SDK | 自动生成 Playground，类型强校验  |

本项目同时实现了 RESTful + resolver 和 GraphQL 两种接口，便于对比和学习两者的使用方式及优缺点。

### GraphQL

灵活， 可以查询，适合需要对数据做灵活查询的场景

![image](https://github.com/user-attachments/assets/cf80c282-b3bc-472d-a584-bbb73a213d4d)

### RESTful + resolver

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

### RESTful + resolver

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
