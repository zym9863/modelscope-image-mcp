# 代码审查报告

## 审查概览
- **仓库**: `modelscope-image-mcp`
- **审查范围**: `src/modelscope_image_mcp/server.py`、`main.py`、根目录文档及配置
- **审查日期**: 2025-09-24
- **审查者**: Cascade AI 助手

## 主要优点
- **结构简单清晰**: `server.py` 将 API 调用流程划分为工具注册、任务提交、轮询、下载保存等函数，逻辑链条紧凑易读。
- **异常处理完善**: 关键网络请求均包裹在 `try/except` 中，并通过日志与文字反馈向调用方暴露错误信息，提升了可观测性。
- **配置可缓存**: `get_api_key()` 使用 `lru_cache` 缓存环境变量读取，避免重复 I/O 调用，体现出对性能与健壮性的关注。

## 主要风险与改进建议
- **指数级重试策略缺失**: 轮询逻辑固定每 5 秒请求一次，总时长最长 10 分钟，若后台长期 pending 会持续消耗资源。建议抽象轮询参数，或引入指数退避机制并允许外部配置。
- **对图片内容缺乏校验**: 下载后直接用 `PIL.Image.open()` 打开并保存，若返回非图片或体积过大可能抛异常或阻塞。建议在下载前检查 `Content-Type` 与文件尺寸，并在保存后返回摘要信息。
- **缺少单元测试与集成测试**: 当前仓库无测试覆盖，未来更改易于引入回归问题。建议为核心函数（如 `generate_image()`）编写模拟 API 的单元测试，并在 CI 中加入网络交互的冒烟测试。
- **缺少配置文件与日志级别控制**: 日志全局使用 `INFO` 级别，可能在生产环境过于冗长。建议引入配置文件或环境变量来控制日志级别与输出格式。

## P0 修复落实（v1.1.0）
- 已支持可配置的轮询策略与可选指数退避：
  - 新增环境变量：`MODELSCOPE_POLL_INTERVAL_SECONDS`、`MODELSCOPE_MAX_POLL_ATTEMPTS`、`MODELSCOPE_POLL_BACKOFF`、`MODELSCOPE_MAX_POLL_INTERVAL_SECONDS`。
  - 新增可覆盖的工具参数：`poll_interval_seconds`、`max_poll_attempts`、`poll_backoff`、`max_poll_interval_seconds`。
  - 新增函数 `get_polling_config()`，在 `generate_image()` 中合并环境变量与工具入参。
- 已增强错误上下文：
  - 所有关键请求在失败时返回 `status_code`、`request_id`、`body`，成功结果包含 `request_id`。
  - 日志记录原始响应体，便于排查（`server.py`）。
- 已增加图片内容校验与保存稳健性：
  - 下载前校验 `Content-Type` 前缀为 `image/`，否则返回详细错误。
  - JPG 保存时若存在透明通道，自动转为 `RGB`，避免保存异常。
- 已支持通过环境变量控制日志级别：
  - 新增 `MODELSCOPE_LOG_LEVEL`（默认 `INFO`），并引入 `python-dotenv` 自动加载 `.env`。
- 版本同步：
  - `server.py` 中 `server_version` 更新为 `1.1.0`。

## 建议的短期行动
- **补充 README**: 在 `README-zh.md` 中补充关于凭证安全、输出目录权限与新环境变量/工具参数的说明。
- **补充单元测试与 CI**: 为 `generate_image()` 编写单元测试与集成冒烟测试，并在 CI 中添加必要的工作流。

## 长期演进方向
- **多图片选择与元数据返回**: 接口返回的 `output_images` 目前只保存第一项，未来可扩展为返回全部图片，或允许使用者选择保留的索引。
- **提高并发能力**: 当前代码单线程串行执行，未来可考虑使用任务队列或并发下载提高吞吐量。
- **健壮的配置管理**: 引入 `pydantic` 设置模型或 `.env` 解析工具，集中管理 API 基础地址、默认模型等配置。
