# ModelScope Image MCP 服务器

[English](README.md) | 中文

一个通过 ModelScope 图像生成 API 生成图片的 MCP (Model Context Protocol) 服务器。该服务器提供与 AI 助手的无缝集成，使其能够通过自然语言提示创建图片，具有强大的异步处理和本地文件管理功能。

> 说明：先前 README 中提到的 base64 返回、负面提示词等功能当前代码尚未实现。当前版本仅包含一个 `generate_image` 工具：提交异步任务 -> 轮询结果 -> 下载第一张图片并保存到本地。未来计划见“路线图”。

## 当前功能

- 使用 ModelScope 异步任务 API 生成图片
- 每 5 秒轮询一次任务状态（最多约 2 分钟）
- 保存第一张输出图片到本地文件
- 将任务状态、图片 URL、保存文件信息返回 MCP 客户端
- 明确的错误与超时信息
- 通过 `uvx` 一条命令即可运行

## 环境变量

程序从以下环境变量读取访问凭证：

```
MODELSCOPE_SDK_TOKEN
```

如果缺失会抛出异常。令牌申请地址：https://modelscope.cn/my/myaccesstoken

Windows (cmd)：
```
set MODELSCOPE_SDK_TOKEN=your_token_here
```
PowerShell：
```
$env:MODELSCOPE_SDK_TOKEN="your_token_here"
```
Linux/macOS：
```
export MODELSCOPE_SDK_TOKEN=your_token_here
```

## 安装与 MCP 客户端配置

可直接在支持 MCP 的客户端（例如 Claude Desktop）里通过 `uvx` 注册，无需手动预装。

### 方式 1：PyPI （发布后推荐）

```jsonc
{
  "mcpServers": {
    "modelscope-image": {
      "command": "uvx",
      "args": ["modelscope-image-mcp"],
      "env": { "MODELSCOPE_SDK_TOKEN": "your_token_here" }
    }
  }
}
```

### 方式 2：直接使用 GitHub 源码

```jsonc
{
  "mcpServers": {
    "modelscope-image": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/zym9863/modelscope-image-mcp.git",
        "modelscope-image-mcp"
      ],
      "env": { "MODELSCOPE_SDK_TOKEN": "your_token_here" }
    }
  }
}
```

### 方式 3：本地源码开发

```bash
git clone https://github.com/zym9863/modelscope-image-mcp.git
cd modelscope-image-mcp
uv sync
```

然后在 MCP 客户端配置：

```jsonc
{
  "mcpServers": {
    "modelscope-image": {
      "command": "uvx",
      "args": ["--from", ".", "modelscope-image-mcp"],
      "env": { "MODELSCOPE_SDK_TOKEN": "your_token_here" }
    }
  }
}
```

## 本地快速测试

```bash
uvx --from . modelscope-image-mcp
```

看到日志输出任务提交与轮询状态即表示运行正常。

```

## 使用示例

### 基础图片生成

```jsonc
{
  "name": "generate_image",
  "arguments": {
    "prompt": "日落时分的宁静山景"
  }
}
```

### 高级配置

```jsonc
{
  "name": "generate_image",
  "arguments": {
    "prompt": "未来城市，有飞行的汽车，赛博朋克风格",
    "model": "Qwen/Qwen-Image",
    "size": "1024x1024",
    "output_filename": "cyberpunk_city.png",
    "output_dir": "./generated_images"
  }
}
```

### 创意提示词

- **艺术风格**: "梵高风格", "水墨画", "数字艺术"
- **构图**: "特写肖像", "广角风景", "鸟瞰视角"
- **光线**: "戏剧性光线", "黄金时段", "工作室灯光"
- **氛围**: "神秘氛围", "鲜艳色彩", "极简设计"

### 最佳实践

1. **具体描述**: 详细的提示词比模糊的描述产生更好的结果
2. **使用参考**: 提及特定的艺术风格、艺术家或时代
3. **多尝试**: 尝试提示词的各种变体以找到最佳结果
4. **组织输出**: 使用描述性的文件名和有组织的目录
5. **监控状态**: 监控异步任务状态以了解长时间运行的生成

### generate_image

使用 ModelScope 异步接口根据文字提示生成图片。

参数：
- prompt (字符串，必填)：描述你想生成的图片
- model (字符串，可选，默认：Qwen/Qwen-Image)：API 使用的模型名称
- size (字符串，可选，默认：1024x1024)：生成图像分辨率大小，Qwen-Image支持：[64x64,1664x1664]
- output_filename (字符串，可选，默认：result_image.jpg)：保存的本地文件名
- output_dir (字符串，可选，默认：./outputs)：图片保存的目录路径

示例调用（概念 JSON）：

```jsonc
{
  "name": "generate_image",
  "arguments": {
    "prompt": "一只金色的猫在花园里玩耍",
    "size": "1024x1024",
    "output_filename": "cat.jpg",
    "output_dir": "./my_images"
  }
}
```

示例文本返回：

```
图片生成成功！
提示词: 一只金色的猫在花园里玩耍
模型: Qwen/Qwen-Image
保存路径: /path/to/my_images/cat.jpg
输出目录: /path/to/my_images
文件名: cat.jpg
图片URL: https://.../generated_image.jpg
```

说明：
- 目前仅保存第一张图片
- 失败或超时会返回对应提示
- 尚未返回 base64 数据（列入路线图）

## 内部流程

1. 使用 `X-ModelScope-Async-Mode: true` 提交异步任务
2. 每 5 秒轮询 `/v1/tasks/{task_id}`（最多 120 次）
3. 成功后下载第一张图片并用 Pillow 保存
4. 返回结果文本到 MCP 客户端
5. 出错 / 超时给出明确描述

## 路线图（计划特性）

- 可选返回 base64 数据
- 负面提示词 / 指导系数
- 可调轮询间隔与超时时间
- 多图片输出选择
- 进度通知（notifications）

## 开发

```bash
# 安装所有依赖（包括开发依赖）
uv sync --dev

# 直接运行服务器模块
uv run python -m modelscope_image_mcp.server

# 或通过 uvx 使用本地源码
uvx --from . modelscope-image-mcp

# 使用环境变量运行
MODELSCOPE_SDK_TOKEN=your_token_here uv run python -m modelscope_image_mcp.server

# 格式化代码（如果配置了 ruff）
uv run ruff format .

# 检查代码（如果配置了 ruff）
uv run ruff check . --fix
```

### 项目结构

```
modelscope-image-mcp/
├── src/modelscope_image_mcp/
│   ├── __init__.py
│   └── server.py          # 主要的 MCP 服务器实现
├── pyproject.toml         # 项目配置和依赖
├── uv.lock               # 锁定文件，确保可重现构建
├── README.md             # 英文文档
└── README-zh.md         # 中文文档（本文件）
```

## 故障排查

| 现象 | 可能原因 | 处理 |
|------|----------|------|
| ValueError: 需要设置 MODELSCOPE_SDK_TOKEN 环境变量 | 缺少令牌 | 设置环境变量后重启 |
| 图片生成超时 | 模型处理缓慢 | 重试；未来将提供可调超时 |
| httpx 超时/网络错误 | 网络不稳定 | 检查网络后重试 |
| PIL cannot identify image file | 收到无效图片数据 | 尝试不同的提示词或模型 |
| Permission denied when saving | 输出目录权限问题 | 检查写入权限或更改 output_dir |
| No such file or directory | 输出目录不存在 | 服务器会自动创建，或指定现有路径 |

## 更新日志

### 1.0.1
- 新增size参数支持，可自定义图像分辨率
- 改进图片生成，支持Qwen-Image模型分辨率范围[64x64,1664x1664]
- 增强文档说明，添加size参数使用示例

### 1.0.0
- 重大更新：改进异步处理和输出目录支持
- 新增可配置的输出目录参数
- 增强错误处理和日志记录
- 更新依赖使用httpx以获得更好的异步支持
- 修复初始版本中的notification_options错误

### 0.1.0
- 最小实现：异步轮询 + 本地保存
- 修复 `notification_options` 为 None 引发的 AttributeError

## 许可证

MIT 许可证

## 贡献

欢迎提交 Issue / PR，问题请附重现步骤。

## 免责声明

此项目为非官方集成示例，使用需遵守 ModelScope 服务条款。