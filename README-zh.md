# ModelScope Image MCP 服务器

[English](README.md) | 中文

一个用于使用 ModelScope Qwen-Image 模型生成图像的 MCP (Model Context Protocol) 服务器。

## 功能特性

- 使用 ModelScope Qwen-Image 模型生成高质量图像
- 支持异步任务处理和状态轮询
- 支持图像 URL 和 base64 编码数据
- 完善的错误处理和超时保护
- 支持 uvx 一键运行

## 安装和配置

### 1. 克隆或下载项目

```bash
git clone https://github.com/zym9863/modelscope-image-mcp.git
cd modelscope-image-mcp
```

### 2. 配置环境变量

复制环境变量示例文件：
```bash
cp .env.example .env
```

编辑 `.env` 文件设置您的 ModelScope API Key：
```bash
MODELSCOPE_API_KEY=your_actual_api_key_here
```

**获取 API Key：**
1. 访问 [ModelScope 个人中心](https://modelscope.cn/my/myaccesstoken)
2. 登录您的账户
3. 生成并复制 Access Token

### 3. 安装依赖

使用 uv 安装依赖：
```bash
uv sync
```

## 使用方法

### 方法 1：直接使用 uvx 运行（推荐）

```bash
# 设置环境变量
export MODELSCOPE_API_KEY="your_api_key"

# 运行 MCP 服务器
uvx --from . modelscope-image-mcp
```

### 方法 2：在 MCP 客户端中配置

添加到 Claude Desktop 或其他 MCP 客户端配置文件：

```json
{
  "mcpServers": {
    "modelscope-image": {
      "command": "uvx",
      "args": ["--from", "/path/to/modelscope-image-mcp", "modelscope-image-mcp"],
      "env": {
        "MODELSCOPE_API_KEY": "your_api_key"
      }
    }
  }
}
```

## API 工具说明

### generate_image

主要的图像生成工具。

**参数：**
- `prompt`（必需）：图像生成提示词，支持中英文
- `return_base64`（可选）：是否返回 base64 编码的图像数据，默认为 `false`

**示例调用：**

```python
# 基础用法 - 仅返回图像 URL
{
  "prompt": "一只金色的猫在花园里玩耍"
}

# 高级用法 - 返回 URL 和 base64 数据
{
  "prompt": "夕阳下的未来城市，有飞行汽车",
  "return_base64": true
}
```

**返回结果：**
成功时返回：
- 成功状态
- 图像链接
- 使用的提示词
- 任务 ID
- base64 数据（如果请求）

失败时返回：
- 错误状态
- 错误消息  
- 详细错误描述

## 技术细节

### 工作流程

1. **异步任务提交**：向 ModelScope API 提交图像生成请求
2. **任务轮询**：每 5 秒检查任务状态，最多等待 150 秒
3. **结果处理**：任务完成时获取图像 URL，可选下载并转换为 base64
4. **错误处理**：优雅地捕获和处理各种可能的错误

### 超时和重试

- 最大等待时间：150 秒（30 次轮询 × 5 秒间隔）
- 网络请求超时：使用 requests 库默认超时设置
- 任务状态检查间隔：5 秒

### 支持的图像格式

- 生成格式：ModelScope API 默认格式
- base64 转换：JPEG 格式

## 开发和测试

### 本地开发

```bash
# 安装开发依赖
uv sync --dev

# 运行服务器
uv run python -m modelscope_image_mcp.server

# 或使用 uvx
uvx --from . modelscope-image-mcp
```

### 测试连接

服务器启动后，您可以在支持 MCP 协议的客户端中测试图像生成功能。

## 环境要求

- Python >= 3.10
- uv 包管理器
- ModelScope API Key
- 网络连接

## 许可证

本项目使用 MIT 许可证。

## 贡献

欢迎提交 Issue 和 Pull Request！

## 更新日志

### v0.1.0
- 初始版本
- 支持基本图像生成功能
- 支持 base64 编码返回
- 完善的错误处理机制