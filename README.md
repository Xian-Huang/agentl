# Aegntl

Aegntl 的目标是成为一个**可运行、可测试、可扩展、可二次开发**的 ReAct Agent。它既可以直接作为命令行 Agent 使用，也可以作为一个 Python 库嵌入其他应用，并通过工具、模型提供者和运行时钩子进行扩展。

## 1. 目标与边界

`v0.1.0` 需要先达到以下目标：

- 通过统一配置连接 DeepSeek 或其他 OpenAI Chat Completions 兼容接口。
- 支持多轮对话、工具调用和多步骤 ReAct 循环。
- 通过简单装饰器注册工具，并自动生成模型可识别的参数 Schema。
- 提供可直接使用的 CLI，以及可供二次开发的 Python API。
- 对 API 超时、鉴权失败、工具异常和无限循环等情况提供可理解的处理。
- 核心逻辑具备不访问真实网络的自动化测试。
- 第三方开发者无需修改 Agent 核心，就能增加工具或替换模型提供商。

“完整架构”不等于首版一次实现所有能力，而是从第一天起为 Agent 必需的组件预留清晰边界。完整架构应覆盖：接入层、运行时、上下文、模型网关、工具执行、知识与记忆、任务编排、状态持久化、权限治理、人工介入、可观测性、评测和部署。各能力按版本逐步落地，但接口与演进路径必须提前明确。

## 2. 当前状态

项目目前是一个可离线测试的 ReAct Agent 原型，工具注册和执行链路已经接通，正在向可安装、可扩展的运行时演进。

已具备：

- `LLMChannel`：通过 HTTPX 调用 OpenAI Chat Completions 兼容接口，并在缺少 Key 时给出明确错误。
- `ReActAgent`：支持可注入模型/工具依赖的多步骤循环、最大步骤和停止原因。
- `ToolRegistry`：分离工具声明与执行，支持参数校验、未知工具错误和独立注册空间。
- `@tool`：基于 Pydantic 从函数签名生成参数 Schema，支持默认注册表和独立注册表。
- 示例工具：天气、当前时间、订单查询。
- 离线测试：注册、Schema、执行、工具错误、循环上限和缺少 API Key。
- 最小开发环境：`requirements.txt`、`requirements-dev.txt` 和 `.env.example`。

尚未完成：

- 当前目录本身是 Python 包，尚未迁移到标准 `src/aegntl` 布局，因此还没有可安装的 `pyproject.toml` 发布配置。
- 尚未实现 CLI、结构化运行结果、持久化 Trace、错误分类和 Provider 抽象。
- 模型请求仍使用通用重试，尚未区分可恢复与不可恢复错误。
- 当前测试集中在一个文件中，尚未拆分单元、契约和真实 API 集成测试。
- 尚无 Session、Memory、RAG、审批、沙箱和多 Agent 等后续能力。

## 3. 完整架构总览

完整 Agent 可以划分为六个相互独立但可组合的平面：

| 平面       | 主要职责                           | 关键组件                                                   | 目标版本                          |
| ---------- | ---------------------------------- | ---------------------------------------------------------- | --------------------------------- |
| 接入平面   | 为用户、脚本和宿主系统提供入口     | CLI、Python SDK、HTTP API、Web UI、Webhook                 | SDK/CLI `v0.1`，服务化 `v0.4` |
| 控制平面   | 驱动一次 Agent Run，决定下一步行动 | Agent Runtime、ReAct Loop、Planner、Scheduler、终止控制    | `v0.1`，高级编排 `v0.4`       |
| 能力平面   | 为 Agent 提供推理和行动能力        | Provider、Model Router、Tools、Memory、RAG、Sub Agent      | 按版本递进                        |
| 上下文平面 | 构造模型每次请求可见的信息         | Prompt Template、Context Builder、Token Budget、Compaction | `v0.1` 基础，`v0.3` 完整      |
| 状态平面   | 保存对话、任务、检查点和产物       | Session Store、Run State、Checkpoint、Artifact Store       | 内存态 `v0.1`，持久化 `v0.2`  |
| 治理平面   | 控制风险并解释系统行为             | Policy、Approval、Sandbox、Audit、Trace、Metrics、Evals    | 基础能力 `v0.2`，持续增强       |

### 3.1 总体数据流

```text
CLI / SDK / HTTP API / Web UI
              |
              v
      Input & Session Manager
              |
              v
 Context Builder <---- Memory / Knowledge / Conversation State
              |
              v
        Agent Runtime ------> Event / Trace / Metrics / Cost
          |       |
          |       +-------> Policy / Approval / Human-in-the-loop
          |       |
          |       +-------> Tool Executor ----> Built-in / Plugin / MCP / Sandbox
          |
          +---------------> Model Router ----> OpenAI-compatible Providers
              |
              v
       Planner / Step Controller
              |
              v
      Run State / Checkpoint / Artifact Store
```

一次标准运行应按以下顺序推进，并把每个关键动作记录为结构化事件：

1. 校验输入、租户、会话和运行参数。
2. 恢复会话状态，加载任务目标、约束和已有产物。
3. 构建上下文，执行 Token 预算、历史压缩和记忆检索。
4. 根据模型策略调用 Provider，必要时进行路由、回退和限流。
5. 解析文本、结构化输出或工具调用，并校验模型输出。
6. 对工具调用执行权限检查、参数校验、审批和资源限制。
7. 执行工具，处理超时、重试、幂等和并行调用，记录结果。
8. 更新运行状态、working memory、Trace 和检查点。
9. 判断是否继续规划、调用工具或结束，并检查步骤、时间、Token 和成本预算。
10. 返回结构化结果，持久化会话并触发完成、失败或取消事件。

### 3.2 推荐目录结构

```text
aegntl/
├── pyproject.toml
├── README.md
├── .env.example
├── CHANGELOG.md
├── CONTRIBUTING.md
├── src/
│   └── aegntl/
│       ├── __init__.py
│       ├── interfaces/
│       │   ├── cli.py
│       │   ├── python_api.py
│       │   └── http_api.py
│       ├── config.py
│       ├── errors.py
│       ├── types.py
│       ├── runtime/
│       │   ├── agent.py
│       │   ├── loop.py
│       │   ├── state.py
│       │   ├── scheduler.py
│       │   ├── budget.py
│       │   └── cancellation.py
│       ├── context/
│       │   ├── builder.py
│       │   ├── token_budget.py
│       │   ├── compaction.py
│       │   └── prompts/
│       ├── providers/
│       │   ├── base.py
│       │   ├── openai_compatible.py
│       │   ├── router.py
│       │   └── fake.py
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── decorators.py
│       │   ├── registry.py
│       │   ├── executor.py
│       │   ├── policy.py
│       │   ├── results.py
│       │   └── builtin.py
│       ├── memory/
│       │   ├── base.py
│       │   ├── working.py
│       │   ├── session.py
│       │   └── long_term.py
│       ├── knowledge/
│       │   ├── loaders.py
│       │   ├── chunking.py
│       │   ├── embeddings.py
│       │   └── retriever.py
│       ├── planning/
│       │   ├── base.py
│       │   ├── react.py
│       │   └── plan_execute.py
│       ├── agents/
│       │   ├── base.py
│       │   ├── supervisor.py
│       │   └── worker.py
│       ├── storage/
│       │   ├── session_store.py
│       │   ├── checkpoint_store.py
│       │   ├── artifact_store.py
│       │   └── sqlite.py
│       ├── security/
│       │   ├── policy.py
│       │   ├── approval.py
│       │   ├── redaction.py
│       │   └── sandbox.py
│       ├── observability/
│       │   ├── events.py
│       │   ├── tracing.py
│       │   ├── metrics.py
│       │   └── cost.py
│       └── plugins/
│           ├── base.py
│           └── loader.py
├── examples/
│   ├── basic_chat.py
│   ├── custom_tool.py
│   ├── custom_provider.py
│   ├── memory_rag.py
│   └── multi_agent.py
└── tests/
    ├── unit/
    ├── contract/
    ├── integration/
    └── evals/
```

目录迁移可以分步进行，不应阻塞 `v0.1.0`。第一阶段允许保留当前的根目录布局，但模块接口需要先稳定下来。

## 4. 核心组件与接口契约

核心组件必须可替换、可注入并可单独测试。建议至少定义以下边界：

| 组件                | 最小职责                                               |
| ------------------- | ------------------------------------------------------ |
| `AgentRuntime`    | 接收一次 Run，协调上下文、模型、工具、状态和终止条件   |
| `ChatProvider`    | 完成一次模型调用，支持普通文本、工具调用和结构化输出   |
| `ModelRouter`     | 按模型能力、成本、延迟和可用性选择 Provider 与回退策略 |
| `ContextBuilder`  | 构造消息、系统提示、记忆、检索结果和 Token 预算        |
| `Planner`         | 决定下一步行动，默认实现为 ReAct，可扩展为计划执行     |
| `ToolRegistry`    | 保存工具元数据、Schema 和执行函数，提供隔离的注册空间  |
| `ToolExecutor`    | 参数校验、策略检查、执行、超时、重试和结果标准化       |
| `StateStore`      | 保存 Session、Run、步骤、检查点和恢复所需状态          |
| `MemoryStore`     | 管理工作记忆、会话记忆和长期记忆                       |
| `Retriever`       | 从知识库或外部数据源检索相关内容及引用                 |
| `PolicyEngine`    | 限制模型、工具、资源、数据和运行预算                   |
| `ApprovalHandler` | 对高风险动作请求人工确认，支持暂停与恢复               |
| `EventSink`       | 接收运行事件，供 CLI、日志、Trace、Metrics 和 UI 消费  |
| `PluginHost`      | 校验、加载和隔离第三方扩展                             |

### 4.1 工具注册表

注册表必须同时解决两个不同问题，但不能把两种数据混为一谈：

1. 向模型发送工具声明，包括名称、说明和 JSON Schema。
2. 根据模型返回的函数名和参数调用真实 Python 函数。

建议提供明确接口：

```python
class ToolRegistry:
    def register(self, fn): ...
    def specs(self) -> list[dict]: ...
    def get(self, name: str): ...
    def execute(self, name: str, arguments: dict): ...
```

保留模块级默认注册表以简化普通用法，同时允许测试和宿主应用传入自己的注册表，避免全局状态妨碍隔离。

### 4.2 模型提供者

`LLMChannel` 应演进为统一的模型提供者接口。Agent 只依赖接口，不在业务逻辑中直接写 HTTP：

```python
class ChatProvider(Protocol):
    def complete(self, messages, tools=None, **options): ...
```

首个实现为 OpenAI Chat Completions 兼容协议，以便支持 DeepSeek 和类似服务。

### 4.3 Agent 运行结果

Agent 不应只返回模型消息，还需要返回本次运行的结构化结果：

- 最终文本。
- 消耗的步骤数量。
- 每一步的模型响应和工具调用记录。
- 工具执行成功或失败信息。
- 停止原因，例如完成、达到最大步骤、模型错误或工具错误。

可观测数据应可序列化，便于日志、测试和未来 UI 使用。

一次 `RunState` 至少应包含：

```text
run_id, session_id, status, goal, messages, artifacts,
current_step, max_steps, token_usage, cost_usage,
working_memory, tool_history, approvals, trace_ref, error
```

### 4.4 上下文工程

上下文不是简单拼接聊天记录。`ContextBuilder` 需要处理：

- 系统提示、开发者约束、用户目标和当前任务状态的分层。
- 工具声明、检索内容、记忆和文件内容的来源标记。
- 上下文优先级、去重、截断和摘要压缩。
- 模型上下文窗口、输出预留和安全余量。
- 不可信内容隔离，防止外部文档或工具结果中的提示词覆盖系统约束。
- 长会话的滚动摘要、关键事实提取和可恢复状态。

上下文构建结果应可解释：能够回答“本次模型调用为什么看到了这些内容”。

### 4.5 记忆与知识

记忆分为三层：

- Working Memory：当前 Run 的目标、计划、工具结果和临时状态。
- Episodic/Session Memory：跨轮次保存的对话摘要、偏好和任务进度。
- Long-term Memory：跨会话的用户事实、领域知识或经验，必须有明确写入条件。

知识检索采用可替换的 RAG 管线：

```text
Data Sources -> Loaders -> Normalizer -> Chunker -> Embedding/Index
    -> Query Rewrite -> Hybrid Retrieval -> Rerank -> Context Injection
    -> Citation / Provenance
```

长期记忆和 RAG 不能默认无限保存用户数据。需要定义写入策略、时效、删除、租户隔离和隐私边界。

### 4.6 规划与任务编排

默认使用有边界的 ReAct 循环。规划与执行应拆开，使不同任务可以使用不同策略：

- `ReActPlanner`：模型在每一步决定继续思考、调用工具或结束。
- `PlanAndExecutePlanner`：先生成可撤销计划，再逐步执行和重新规划。
- `Supervisor`：在复杂任务中分发子任务、汇总结果并控制总预算。
- `TaskScheduler`：处理并行工具、依赖关系、优先级和取消。

反思、重试和自我修正必须有次数、时间或成本上限。多 Agent 不应成为默认路径，只有任务可分解、并行收益明显或需要角色隔离时才启用。

### 4.7 状态、持久化与恢复

运行状态分为：

- Session：跨用户输入保留的会话和偏好。
- Run：一次任务执行及其预算、暂停和取消状态。
- Step：一次模型调用或工具调用。
- Checkpoint：可在进程重启或人工审批后恢复的状态快照。
- Artifact：生成的文件、表格、代码、检索结果等大对象。

Run 应采用显式状态机，例如 `created -> running -> waiting_tool -> waiting_approval -> paused -> completed/failed/cancelled`。所有状态迁移应产生事件并持久化，不能在循环中只靠局部变量隐式表达。

MVP 允许使用内存态；可部署版本建议先使用 SQLite，再根据需要切换到 PostgreSQL。存储实现必须带 Schema 版本和迁移策略，大产物不应直接塞入消息上下文。

### 4.8 权限、安全与人工介入

模型输出必须视为不可信输入，禁止直接 `eval`、动态导入或执行未授权命令。

建议将工具划分为：

- `read`：只读查询。
- `write`：修改项目、数据库或用户数据。
- `external`：发送消息、调用付费服务或产生外部副作用。
- `dangerous`：删除、部署、提权、执行任意命令。

治理链路至少包括：

- 工具白名单、租户隔离和参数 Schema 校验。
- 数据访问范围、网络域名和文件路径限制。
- 超时、并发、Token、费用和步骤预算。
- 高风险动作审批，以及暂停、恢复和中止。
- 密钥注入、日志脱敏和审计记录。
- 可选进程、容器或受限工作区隔离。
- Prompt injection 防护、输出校验和敏感数据检测。

### 4.9 可观测性与成本

每次运行应生成唯一的 `run_id` 和 `step_id`，关键事件至少包括：

```text
run.started, context.built, model.started, model.completed,
tool.requested, approval.required, tool.completed, tool.failed,
checkpoint.saved, run.completed, run.failed, run.cancelled
```

事件中应记录耗时、模型、Token、成本、工具名称、结果状态和错误分类，但必须脱敏。Trace 应支持本地开发视图，也能对接 OpenTelemetry 等外部系统。

### 4.10 扩展与插件

二次开发接口需要稳定、版本化并可独立测试。建议提供：

- Provider、Tool、Memory、Retriever、Planner、Policy、EventSink 扩展点。
- 前置/后置中间件，用于鉴权、审计、缓存、限流和结果转换。
- 装饰器注册与显式注册表注册两种方式。
- Python Entry Point、显式配置和目录加载三种插件发现方式。
- 插件清单、能力声明、依赖约束和兼容版本。
- 插件异常隔离，避免一个扩展破坏整个运行时。

### 4.11 错误与停止语义

错误必须分类，而不是统一包装成 `Exception`：

- 配置/鉴权错误。
- 输入或参数校验错误。
- Provider 限流、超时、不可用和协议错误。
- 工具未找到、权限拒绝、执行失败和超时。
- 预算耗尽、用户取消和达到最大步骤。

每次 Run 必须返回明确停止原因。可恢复错误可按策略重试；不可恢复错误应立即终止；工具错误应转换成模型可处理的结果，同时保留原始审计信息。

### 4.12 互操作与多模态

- 内部使用统一的消息和内容模型，支持文本、文件引用、图片、音频、结构化数据和工具结果。
- Provider 声明自身能力，例如流式输出、工具调用、结构化输出、视觉和 Embedding；不支持的输入必须明确降级或拒绝。
- OpenAI-compatible 消息和工具协议作为首个 Provider 协议，但 Agent 核心不依赖其具体字段。
- 通过适配器接入 MCP 等外部工具/资源协议，并把其能力纳入统一权限、Schema、超时和审计体系。
- 文件与附件通过 Artifact Store 管理，消息中只保存引用和摘要，避免大对象直接膨胀上下文。
- 外部文件、网页、图片 OCR 和 MCP 返回内容都属于不可信数据，必须与系统指令分区并执行安全过滤。

## 5. 版本能力矩阵

| 能力域        | `v0.1` 核心 Agent             | `v0.2` 可用运行        | `v0.3` 知识扩展      | `v0.4` 编排与服务  | `v1.0` 稳定平台   |
| ------------- | ------------------------------- | ------------------------ | ---------------------- | -------------------- | ------------------- |
| 对话与 ReAct  | 单/多轮对话、工具循环、最大步骤 | 流式输出、取消、并行工具 | 上下文压缩             | 任务分解             | 稳定协议            |
| Provider      | OpenAI 兼容接口                 | 重试、超时、限流         | 路由和回退             | 多 Provider 策略     | Provider 兼容规范   |
| 输入与输出    | 文本消息                        | 文件与 Artifact 引用     | 图文等多模态输入       | 流式多模态输出       | 能力协商稳定        |
| Tools         | 装饰器、Schema、执行            | 权限、审批、沙箱         | 插件发现               | 并行/异步执行        | 稳定 SDK 与兼容策略 |
| State         | 内存态会话                      | SQLite 持久化、检查点    | 记忆分层               | 分布式状态适配       | 存储接口稳定        |
| Context       | 基础消息构造                    | Token/轮数预算           | 摘要、压缩、注入来源   | 任务级上下文         | 可解释上下文        |
| Knowledge     | 不包含                          | 预留 Retriever           | RAG、引用、混合检索    | 索引服务化           | 数据治理完善        |
| Planning      | ReAct                           | 终止与恢复策略           | 计划模板               | Plan-and-Execute     | 多种规划策略        |
| Multi-Agent   | 不包含                          | 预留 Agent 接口          | 不包含                 | Supervisor/Worker    | 预算与隔离完善      |
| Safety        | 参数校验、基础脱敏              | 工具策略、审批、沙箱     | 知识权限               | 租户和外部副作用治理 | 安全审计基线        |
| Observability | 内存 Trace                      | 结构化日志、Metrics      | Citation/Context Trace | 分布式追踪           | OpenTelemetry 兼容  |
| Interfaces    | Python API、最小 CLI            | 交互式 CLI               | 插件 SDK               | HTTP API、服务部署   | 稳定公共 API        |
| Quality       | 离线单测、CI                    | 契约测试、故障注入       | 检索评测               | 多 Agent 与负载测试  | 回归评测与发布门禁  |

版本数字用于表达能力成熟度，实际开发顺序以当前代码风险为准。任何能力进入版本前，都必须先定义错误语义、预算边界和验收标准。

## 6. 分阶段实施计划

### M0：修复基础并恢复可运行状态

优先级：P0

- 实现 `get_tool_specs()`、`get_tool()` 或 `ToolRegistry` 的等价接口。
- 修正 `main.py` 中工具声明和工具执行对注册表的错误假设。
- 修正 `description` 拼写和类型标注。
- 明确导入 `tools` 模块的时机，避免注册表为空。
- 删除或迁移过时的 `schemas.py` 静态工具定义。
- 修复 `test_agent.py` 对 `register_tools` 的引用。
- 添加 `pyproject.toml`，声明 Python 版本和运行/开发依赖。
- 添加 `.env.example`。

验收标准：

- 在全新虚拟环境中安装依赖后，可以成功导入 `aegntl`。
- 不配置 API Key 时，模块本身仍可导入，并在真正调用模型时给出清晰错误。
- 三个现有工具能够出现在生成的工具声明中。
- 注册表测试和工具调用测试可以离线通过。

### M1：完成可用的命令行 MVP

优先级：P0

- 增加 `aegntl chat` 命令，支持单次输入和交互式多轮对话。
- 增加 `aegntl tools list`，显示已注册工具及其参数。
- 从环境变量和可选 `.env` 文件加载配置。
- 为 Agent 增加 `max_steps`，默认建议为 8。
- 将工具异常转换成模型可读取的错误结果，而不是直接崩溃。
- 对 401、限流、超时和网络错误提供可区分的错误信息。
- 明确多轮对话中 `messages`、`trace` 和工具上下文的管理方式。

验收标准：

- 用户可通过一条命令询问时间、天气或订单状态，并看到工具执行后的最终回答。
- 一次运行达到最大步骤时停止，并返回明确的停止原因。
- API Key 缺失、工具不存在、参数错误和网络失败均不会产生难以理解的堆栈。

### M2：建立可靠性与可用运行时

目标版本：`v0.2`

优先级：P1

- 使用 Fake Provider 和 Mock Transport 测试 Agent，不依赖真实模型。
- 单元测试覆盖：工具注册、Schema 生成、参数校验、工具执行、停止条件和错误处理。
- 将真实 API 测试标记为 integration，默认不在 CI 中运行。
- 为网络请求增加可配置超时、有限重试和退避策略。
- 区分鉴权、参数、限流、超时、网络和服务端错误，只重试可恢复错误。
- 增加 Run、Step、停止原因和结构化 Trace，并持久化到 SQLite。
- 增加 Session Store 和 Checkpoint，为多轮会话、暂停和恢复提供基础。
- 增加步骤、时间、Token 和费用预算，支持用户取消。
- 对日志、错误和 Trace 中的 API Key、Authorization 等敏感信息进行脱敏。
- 建立 Lint、类型检查、测试和 CI。

验收标准：

- 普通测试无需网络和真实 API Key。
- 核心流程具备确定性测试，不依赖模型恰好选择某个工具。
- 进程重启后可以恢复会话；运行达到预算或用户取消时能返回明确状态。
- 失败路径有测试，而不只测试成功回答。
- CI 至少执行格式检查、静态检查和单元测试。

### M3：扩展机制、策略与工具安全

目标版本：`v0.2`

优先级：P1

- 稳定 Provider、Tool、Memory、Retriever、Planner、Policy 和 EventSink 接口。
- 支持 `@tool` 和 `registry.tool` 两种注册方式。
- 支持按模块、配置和 Python Entry Point 加载插件。
- 提供自定义 Provider、Tool、Policy 和 EventSink 示例。
- 为工具增加风险等级、超时、并发限制、参数校验和结果模型。
- 增加工具策略、白名单、路径/域名限制、审批上下文和审核记录。
- 为危险工具实现暂停、人工确认、拒绝、恢复和中止流程。
- 增加进程或容器沙箱接口，至少为执行命令类工具提供隔离边界。
- 排除一个插件故障影响整个运行时，并记录插件版本和加载失败原因。

验收标准：

- 新增一个简单工具只需新增工具模块并完成注册，不修改 Agent 核心。
- 第三方项目可以在不复制源码的情况下安装 Aegntl 并加入自己的工具。
- 高风险工具在无审批时必须被拒绝；审批和拒绝均产生审计事件。
- 测试可注入独立注册表、Provider、Policy 和 EventSink，不依赖全局状态。

### M4：上下文、记忆与知识检索

目标版本：`v0.3`

优先级：P2

- 实现上下文分层、Token 预算、历史压缩和长会话摘要。
- 区分 Working Memory、Session Memory 和 Long-term Memory。
- 为记忆定义写入、召回、更新时间、置信度、删除和保留策略。
- 实现文档加载、清洗、分块、Embedding、索引和检索接口。
- 支持关键词、向量或混合检索，并提供可替换的 Reranker。
- 将检索结果连同来源、片段位置和引用注入上下文。
- 增加知识访问权限和租户隔离，不把无权限内容发送给模型。
- 为上下文构造和检索过程建立可解释 Trace。

验收标准：

- 长会话在预算内运行，并保留任务目标、关键事实和未完成事项。
- RAG 回答可追溯到具体来源，证据不足时能够明确表示无法判断。
- 用户删除记忆后，后续运行不再召回该内容。
- 上下文截断、摘要和检索失败都有可验证的降级行为。

### M5：规划、并行工具与多 Agent 编排

目标版本：`v0.4`

优先级：P2

- 将 Planner 与 Runtime 解耦，支持 ReAct 和 Plan-and-Execute 两种策略。
- 支持工具并行执行、依赖关系、超时、部分失败和结果合并。
- 支持流式响应、增量事件和取消传播。
- 增加 Agent 接口、Supervisor/Worker 拓扑、子任务预算和结果汇总。
- 为多 Agent 提供独立上下文、工具权限、最大深度和防递归限制。
- 增加任务暂停、恢复、重试和人工接管流程。
- 提供 HTTP API，明确认证、租户、限流、请求取消和错误协议。
- 增加异步执行、队列适配和水平扩展的边界。
- 增加多 Provider 路由、回退、成本和延迟策略。

验收标准：

- 单个工具失败不会无条件终止可恢复任务，最终结果能说明缺失信息。
- 用户取消可以传播到模型请求、工具执行和子 Agent。
- 多 Agent 任务受总预算、深度和工具权限约束，不能无限递归或扩增。
- CLI、SDK 与 HTTP API 对同一 Run 返回一致的停止语义和错误分类。

### M6：发布稳定平台版本

目标版本：`v1.0`

优先级：P1，在核心能力和接口稳定后执行

- 完善 README 的安装、配置、CLI、Python API、HTTP API 和扩展示例。
- 提供 `examples/`、`.env.example`、变更日志和贡献指南。
- 打包为可通过 `pip install` 安装的 Python 包。
- 固定公共 API，建立语义化版本和弃用流程。
- 建立存储 Schema 迁移、插件兼容和 Provider 契约测试。
- 建立发布流程、最小支持 Python 版本和安全响应流程。
- 提供端到端演示、故障排查和架构决策记录。

验收标准：

- 新用户按 README 可以在 10 分钟内完成安装、配置并运行一次 Agent。
- `pip install` 后 CLI 可用，示例和测试与发布版本一致。
- 公共接口具备契约测试，破坏性变更只能进入主版本。
- 发布包不包含密钥、缓存、虚拟环境或无关文件。

## 7. 评测与质量门禁

Agent 的“可用”不能只靠人工对话验证。至少建立以下评测维度：

| 维度       | 关注问题                                         |
| ---------- | ------------------------------------------------ |
| 任务成功率 | 是否真正完成用户目标，而非只生成看似合理的文本   |
| 工具正确性 | 是否选择正确工具、参数是否合法、是否处理返回结果 |
| 事实与引用 | 是否有证据、引用是否准确、是否编造未知信息       |
| 安全行为   | 是否拒绝越权工具、危险动作和提示词注入           |
| 停止与恢复 | 是否在预算内结束、失败是否可恢复、取消是否生效   |
| 稳定性     | 重复运行结果是否可靠，Provider/工具异常是否可控  |
| 性能与成本 | 首响应、总耗时、Token、费用和并发表现            |

评测集应覆盖无工具问答、单工具、多工具、工具失败、无答案、权限拒绝、长上下文、取消和恢复等路径。Prompt、模型、Provider 或工具策略变更都应有回归评测。

## 8. 非功能性基线

- 可维护性：组件通过接口解耦，核心循环不包含具体 Provider 或工具逻辑。
- 可测试性：所有外部能力可替换，默认测试离线、确定且可重复。
- 可观测性：关键运行可以仅凭 Trace 重建停止原因、工具动作和资源消耗。
- 安全性：默认最小权限，模型输出不可信，风险动作需要显式授权。
- 可靠性：所有循环、重试、并发和外部调用都有边界与取消机制。
- 可扩展性：新增工具、Provider、存储和策略无需修改核心。
- 可移植性：配置通过环境或注入提供，不在导入阶段强制读取密钥。
- 兼容性：公共 API、插件协议和存储 Schema 均有版本策略。

## 9. 近期开发顺序

下一轮开发仍从 M0 开始，严格按以下顺序推进：

1. 实现工具注册表接口并修复 `main.py`。
2. 更新测试，建立完全不联网的注册、Schema 和执行测试。
3. 添加 `pyproject.toml` 和 `.env.example`，形成可复现环境。
4. 引入 Provider、Tool Registry、Run State 的基础接口，只实现当前 OpenAI 兼容 Provider。
5. 增加错误分类、最大步骤、运行预算和结构化结果。
6. 实现最小 CLI 和 `tools list`。
7. 补使用示例、自定义工具示例和开发者文档。
8. 配置 CI 并发布 `v0.1.0`。
9. 再进入 Session 持久化、Trace、审批和沙箱阶段。

## 10. `v0.1.0` 完成定义

满足以下条件后，才将项目标记为“完整可用”的第一个版本：

- 新环境可按文档安装和启动。
- 可连接至少一种真实模型服务。
- 可完成无工具对话和至少一次多步骤工具调用。
- 工具可通过公共接口扩展，无需改核心代码。
- Agent 不直接依赖 HTTP 或某个具体模型名，Provider 可替换。
- 核心流程具备离线自动化测试和 CI。
- 超时、鉴权失败、工具失败、预算耗尽和最大步骤都有明确处理。
- 每次运行返回结构化结果和停止原因。
- 敏感配置不会进入仓库或普通日志。
- CLI、Python API、扩展示例和故障排查文档齐全。

## 11. 开发原则

- 先保证正确、可测试和安全，再追求功能数量。
- Provider、Tool、Memory、Storage、Policy 等外部能力通过接口注入。
- 默认测试不访问外网，真实 API 测试显式启用。
- 所有循环、网络请求、工具执行、子 Agent 和重试都必须有边界。
- 工具调用是可审计动作，应保留结构化 Trace。
- 完整架构必须覆盖能力，但能力按版本交付，不为了“看起来完整”提前破坏核心稳定性。
- 不把密钥写入代码、README、测试或提交记录。
- 兼容接口优先，避免二次开发被内部实现细节绑定。
