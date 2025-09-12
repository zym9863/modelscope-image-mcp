# ModelScope Image MCP Server

English | [中文](README-zh.md)

An MCP (Model Context Protocol) server for generating images via the ModelScope image generation API.

> IMPORTANT: Earlier drafts of this README mentioned features like returning base64 data, negative prompts, and additional parameters. The current released code (see `src/modelscope_image_mcp/server.py`) implements a focused minimal feature set: one tool `generate_image` that submits an async task and saves the resulting image locally. Planned / upcoming features are listed in the roadmap below.

## Current Features

- Asynchronous image generation using ModelScope async task API
- Periodic task status polling (every 5 seconds, up to 2 minutes)
- Saves the first generated image to a local file
- Returns task status and image URL to the MCP client
- Robust error handling + timeout messaging
- Simple one-command start with `uvx`

## Environment Variable

The server reads your credential from:

```
MODELSCOPE_SDK_TOKEN
```

If it is missing, the server will raise an error. Obtain a token from: https://modelscope.cn/my/myaccesstoken

### Set on Windows (cmd):
```
set MODELSCOPE_SDK_TOKEN=your_token_here
```
PowerShell:
```
$env:MODELSCOPE_SDK_TOKEN="your_token_here"
```
Unix/macOS bash/zsh:
```
export MODELSCOPE_SDK_TOKEN=your_token_here
```

## Installation & MCP Client Configuration

You can register the server directly in an MCP-compatible client (e.g. Claude Desktop) without a prior manual install thanks to `uvx`.

### Option 1: PyPI (Recommended once published)

```jsonc
{
  "mcpServers": {
    "modelscope-image": {
      "command": "uvx",
      "args": ["modelscope-image-mcp"],
      "env": {
        "MODELSCOPE_SDK_TOKEN": "your_token_here"
      }
    }
  }
}
```

### Option 2: Direct from GitHub

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
      "env": {
        "MODELSCOPE_SDK_TOKEN": "your_token_here"
      }
    }
  }
}
```

### Option 3: Local Development Checkout

```bash
git clone https://github.com/zym9863/modelscope-image-mcp.git
cd modelscope-image-mcp
uv sync
```

Then configure MCP client entry using:

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

## Quick Local Smoke Test

```bash
# Run directly (local checkout)
uvx --from . modelscope-image-mcp
```

When running successfully you should see log lines showing task submission and polling.

## Available Tool

### generate_image

Creates an image from a text prompt using the ModelScope async API.

Parameters:
- prompt (string, required): The text description of the desired image
- model (string, optional, default: Qwen/Qwen-Image): Model name passed to API
- output_filename (string, optional, default: result_image.jpg): Local filename to save the first output image

Sample invocation (conceptual JSON sent by MCP client):

```jsonc
{
  "name": "generate_image",
  "arguments": {
    "prompt": "A golden cat playing in a garden",
    "output_filename": "cat.jpg"
  }
}
```

Sample textual response payload (returned to the client):

```
图片生成成功！
提示词: A golden cat playing in a garden
模型: Qwen/Qwen-Image
保存文件: cat.jpg
图片URL: https://.../generated_image.jpg
```

Notes:
- Only the first image URL is used (if multiple are ever returned)
- If the task fails or times out you receive a descriptive message
- No base64 data is currently returned (roadmap item)

## Internal Flow

1. Submit async generation request with header `X-ModelScope-Async-Mode: true`
2. Poll task endpoint `/v1/tasks/{task_id}` every 5 seconds (max 120 attempts ~= 2 minutes)
3. On SUCCEED download first image and save via Pillow (PIL)
4. Return textual metadata to MCP client
5. Provide clear error / timeout messages otherwise

## Roadmap

Planned enhancements (not yet implemented in `server.py`):
- Optional base64 return data
- Negative prompt & guidance parameters
- Adjustable polling interval & timeout via arguments
- Multiple image outputs selection
- Streaming progress notifications

## Development

```bash
# Install all (including dev) dependencies
uv sync --dev

# Run server module
uv run python -m modelscope_image_mcp.server

# Or via uvx using local source
uvx --from . modelscope-image-mcp
```

## Troubleshooting

| Symptom | Possible Cause | Action |
|---------|----------------|--------|
| ValueError: 需要设置 MODELSCOPE_SDK_TOKEN 环境变量 | Token missing | Export / set environment variable then restart |
| 图片生成超时 | Slow model processing | Re-run; later we will expose longer timeout argument |
| 网络相关 httpx.TimeoutException | Connectivity issues | Check network / retry |

## Changelog

### 0.1.0
- Initial minimal implementation with async polling & local image save
- Fixed bug: `notification_options` previously None causing AttributeError

## License

MIT License

## Contributing

PRs & issues welcome. Please describe reproduction steps for any failures.

## Disclaimer

This is an unofficial integration example. Use at your own risk; abide by ModelScope Terms of Service.