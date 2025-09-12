# ModelScope Image MCP 服务器

[English](README.md) | 中文

一个通过 ModelScope 图像生成 API 生成图片的最小可用 MCP (Model Context Protocol) 服务器。

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

## 可用工具

### generate_image

使用 ModelScope 异步接口根据文字提示生成图片。

参数：
- prompt (字符串，必填)：描述你想生成的图片
- model (字符串，可选，默认：Qwen/Qwen-Image)：API 使用的模型名称
- output_filename (字符串，可选，默认：result_image.jpg)：保存的本地文件名

示例调用（概念 JSON）：

```jsonc
{
  "name": "generate_image",
  "arguments": {
    "prompt": "一只金色的猫在花园里玩耍",
    "output_filename": "cat.jpg"
  }
}
```

示例文本返回：

```
图片生成成功！
提示词: 一只金色的猫在花园里玩耍
模型: Qwen/Qwen-Image
保存文件: cat.jpg
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
uv sync --dev
uv run python -m modelscope_image_mcp.server
# 或
uvx --from . modelscope-image-mcp
```

## 故障排查

| 现象 | 可能原因 | 处理 |
|------|----------|------|
| ValueError: 需要设置 MODELSCOPE_SDK_TOKEN 环境变量 | 缺少令牌 | 设置环境变量后重启 |
| 图片生成超时 | 模型处理缓慢 | 重试；未来将提供可调超时 |
| httpx 超时/网络错误 | 网络不稳定 | 检查网络后重试 |

## 更新日志

### 0.1.0
- 最小实现：异步轮询 + 本地保存
- 修复 `notification_options` 为 None 引发的 AttributeError

## 许可证

MIT 许可证

## 贡献

欢迎提交 Issue / PR，问题请附重现步骤。

## 免责声明

此项目为非官方集成示例，使用需遵守 ModelScope 服务条款。