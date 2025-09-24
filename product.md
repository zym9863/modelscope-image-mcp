# 产品待办清单

## 项目概览
- **产品名称**: ModelScope Image MCP 服务器
- **目标用户**: 使用 MCP 客户端（如 Claude Desktop）进行图片生成的开发者与 AI 助手用户
- **核心价值**: 提供稳定、可扩展的图片生成工具接口，简化与 ModelScope API 的集成与使用
- **当前版本**: 1.1.0

## 产品愿景
打造一个可扩展、可观测、易集成的 ModelScope 图像生成 MCP 服务器，实现从提示词到成品图片的端到端体验，并支持企业级的配置、监控与多输出场景。

## MVP 目标
1. 支持异步任务提交与轮询，稳定下载并保存首张图片。
2. 提供基础的错误处理与日志记录，确保最小化故障排查成本。
3. 通过 `uvx` 命令即可快速集成至 MCP 客户端。

## 产品路线图
- **短期（1-2 个版本）**
  - 丰富错误信息与上下文返回。
  - 提供可配置的轮询参数与日志级别。
  - 补充单元测试与基础 CI 工作流。
- **中期（3-5 个版本）**
  - 支持多图片下载与选择。
  - 新增 base64 输出选项与负面提示词参数。
  - 引入并发任务队列提升吞吐量。
- **长期（6 个版本以上）**
  - 构建监控与告警能力，支持通知回调。
  - 与其他生成式模型打通（如文本、音频）。
  - 提供可视化管理后台。

## 产品待办列表

### 高优先级
- **US-003**: 作为 QA，我希望项目具备核心单元测试与 CI 流程，以避免回归问题。

### 已完成（v1.1.0）
- **US-001（已完成）**: 失败与成功路径均返回更详细的上下文信息。
  - 响应中包含 `status_code`、`request_id`、`body`（失败时）；成功结果返回 `request_id`。
  - 日志记录原始响应体与时间戳，便于追踪。
- **US-002（已完成）**: 通过环境变量与工具参数控制日志与轮询策略。
  - 环境变量：`MODELSCOPE_LOG_LEVEL`、`MODELSCOPE_POLL_INTERVAL_SECONDS`、`MODELSCOPE_MAX_POLL_ATTEMPTS`、`MODELSCOPE_POLL_BACKOFF`、`MODELSCOPE_MAX_POLL_INTERVAL_SECONDS`。
  - 工具参数：`poll_interval_seconds`、`max_poll_attempts`、`poll_backoff`、`max_poll_interval_seconds`。

### 中优先级
- **US-004**: 作为终端用户，我希望能够选择保存多张生成图片，以便比较最佳输出。
- **US-005**: 作为开发者，我需要在工具参数中配置负面提示词与指导系数，以提升图像质量。
- **US-006**: 作为 AI 助手，我希望服务返回 base64 编码数据，便于在无文件系统环境中展示图片。

### 低优先级
- **US-007**: 作为管理员，我需要查看任务执行统计与性能指标，以监控运行状况。
- **US-008**: 作为产品经理，我希望访问基于 Web 的管理界面，以便配置模型与查看任务历史。
- **US-009**: 作为集成者，我希望支持更多模型与跨模态（文本、音频）的扩展，满足多样化需求。

## 验收标准示例
- **US-001**
  - 当后端返回失败时，响应中包含 `status_code`、`request_id` 字段。
  - 日志中记录原始响应体与时间戳，便于追踪。
- **US-004**
  - 工具参数允许传入 `max_images` 或索引列表。
  - 本地保存的图片以有序命名（如 `result_image_1.jpg`）。
- **US-006**
  - 当调用者请求 base64 数据时，响应文本包含 `data:image/jpeg;base64,` 前缀。
  - 文档更新，说明安全与性能注意事项。

## 配置说明（v1.1.0）
- **日志级别**: 通过 `MODELSCOPE_LOG_LEVEL` 控制（默认 `INFO`）。
- **轮询策略**:
  - `MODELSCOPE_POLL_INTERVAL_SECONDS`（默认 `5`）
  - `MODELSCOPE_MAX_POLL_ATTEMPTS`（默认 `120`）
  - `MODELSCOPE_POLL_BACKOFF`（默认 `false`）
  - `MODELSCOPE_MAX_POLL_INTERVAL_SECONDS`（默认 `30`）
- **工具参数覆盖**:
  - `poll_interval_seconds`、`max_poll_attempts`、`poll_backoff`、`max_poll_interval_seconds`

## 依赖与风险
- **API 可用性**: 依赖 ModelScope 官方服务，需监控接口变动与配额限制。
- **网络稳定性**: 异步轮询受网络质量影响，需要重试与超时策略。
- **合规要求**: 涉及图像生成与存储，需遵守相关法规与平台政策。
