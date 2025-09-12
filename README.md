# ModelScope Image MCP Server

English | [中文](README-zh.md)

A MCP (Model Context Protocol) server for generating images using ModelScope Qwen-Image model.

## Features

- Generate high-quality images using ModelScope Qwen-Image model
- Support for async task processing and status polling
- Support for both image URL and base64 encoded data
- Complete error handling and timeout protection
- One-click run with uvx

## Installation and Configuration

### Method 1: Install from PyPI (Recommended)

The simplest way to use this MCP server is to install it directly from PyPI:

```json
{
  "mcpServers": {
    "modelscope-image": {
      "command": "uvx",
      "args": ["modelscope-image-mcp"],
      "env": {
        "MODELSCOPE_API_KEY": "your_api_key"
      }
    }
  }
}
```

### Method 2: Install from GitHub Repository

You can also install directly from the GitHub repository without cloning:

```json
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
        "MODELSCOPE_API_KEY": "your_api_key"
      }
    }
  }
}
```

### Method 3: Local Development Installation

For development or if you prefer to clone the repository:

#### 3.1. Clone or download the project

```bash
git clone https://github.com/zym9863/modelscope-image-mcp.git
cd modelscope-image-mcp
```

#### 3.2. Configure environment variables

Copy the environment variables example file:
```bash
cp .env.example .env
```

Edit the `.env` file to set your ModelScope API Key:
```bash
MODELSCOPE_API_KEY=your_actual_api_key_here
```

**Get API Key:**
1. Visit [ModelScope Personal Center](https://modelscope.cn/my/myaccesstoken)
2. Login to your account
3. Generate and copy Access Token

#### 3.3. Install dependencies

Use uv to install dependencies:
```bash
uv sync
```

## Usage

After installing via any of the above methods, the MCP server can be used with Claude Desktop or any other MCP-compatible client.

### Quick Test

If you want to test the server locally before adding it to your MCP client:

```bash
# Method 1: Test PyPI installation
uvx modelscope-image-mcp

# Method 2: Test from GitHub
uvx --from git+https://github.com/zym9863/modelscope-image-mcp.git modelscope-image-mcp

# Method 3: Test local installation
uvx --from . modelscope-image-mcp
```

## API Tool Description

### generate_image

The main tool for generating images.

**Parameters:**
- `prompt` (required): Image generation prompt, supports Chinese and English
- `return_base64` (optional): Whether to return base64 encoded image data, default is `false`

**Example calls:**

```python
# Basic usage - returns only image URL
{
  "prompt": "A golden cat playing in a garden"
}

# Advanced usage - returns URL and base64 data
{
  "prompt": "A futuristic city at sunset with flying cars",
  "return_base64": true
}
```

**Return results:**
On success returns:
- Success status
- Image link
- Used prompt
- Task ID
- base64 data (if requested)

On failure returns:
- Error status
- Error message  
- Detailed error description

## Technical Details

### Workflow

1. **Async task submission**: Submit image generation request to ModelScope API
2. **Task polling**: Check task status every 5 seconds, wait up to 150 seconds
3. **Result processing**: Get image URL when task completes, optionally download and convert to base64
4. **Error handling**: Capture and handle various possible errors gracefully

### Timeout and Retry

- Maximum wait time: 150 seconds (30 polls × 5 second intervals)
- Network request timeout: Uses requests library default timeout settings
- Task status check interval: 5 seconds

### Supported Image Formats

- Generation format: ModelScope API default format
- base64 conversion: JPEG format

## Development and Testing

### Local Development

```bash
# Install dev dependencies
uv sync --dev

# Run server
uv run python -m modelscope_image_mcp.server

# Or use uvx
uvx --from . modelscope-image-mcp
```

### Test Connection

After the server starts, you can test image generation functionality in MCP protocol supporting clients.

## Environment Requirements

- Python >= 3.10
- uv package manager
- ModelScope API Key
- Network connection

## License

This project uses MIT License.

## Contributing

Issues and Pull Requests are welcome!

## Changelog

### v0.1.0
- Initial version
- Support basic image generation functionality
- Support base64 encoded return
- Complete error handling mechanism