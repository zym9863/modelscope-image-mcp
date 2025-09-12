"""
ModelScope Qwen-Image MCP Server

这是一个 MCP (Model Context Protocol) 服务器，用于调用 ModelScope 的 Qwen-Image 模型生成图片。
"""

import asyncio
import json
import time
import base64
from io import BytesIO
from typing import Any, Dict, Optional
import os
import sys

import requests
from PIL import Image
from dotenv import load_dotenv

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    EmptyResult,
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)


# 加载环境变量
load_dotenv()

# ModelScope API 配置
BASE_URL = 'https://api-inference.modelscope.cn/'
API_KEY = os.getenv("MODELSCOPE_API_KEY")
MODEL_NAME = "Qwen/Qwen-Image"

# 请求头
COMMON_HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

# 创建 MCP 服务器实例
server = Server("modelscope-image-mcp")


async def generate_image_async(prompt: str, return_base64: bool = False) -> Dict[str, Any]:
    """
    异步生成图片
    
    Args:
        prompt: 图片生成提示词
        return_base64: 是否返回 base64 编码的图片数据
        
    Returns:
        包含图片 URL 和可选的 base64 数据的字典
    """
    if not API_KEY:
        raise ValueError("MODELSCOPE_API_KEY 环境变量未设置")
    
    try:
        # 发送异步生成请求
        response = requests.post(
            f"{BASE_URL}v1/images/generations",
            headers={**COMMON_HEADERS, "X-ModelScope-Async-Mode": "true"},
            data=json.dumps({
                "model": MODEL_NAME,
                "prompt": prompt
            }, ensure_ascii=False).encode('utf-8')
        )
        
        response.raise_for_status()
        task_id = response.json()["task_id"]
        
        # 轮询任务状态
        max_attempts = 30  # 最多等待 150 秒 (30 * 5)
        for attempt in range(max_attempts):
            await asyncio.sleep(5)  # 等待 5 秒
            
            result = requests.get(
                f"{BASE_URL}v1/tasks/{task_id}",
                headers={**COMMON_HEADERS, "X-ModelScope-Task-Type": "image_generation"},
            )
            result.raise_for_status()
            data = result.json()
            
            if data["task_status"] == "SUCCEED":
                image_url = data["output_images"][0]
                result_data = {
                    "success": True,
                    "image_url": image_url,
                    "task_id": task_id
                }
                
                # 如果需要返回 base64 数据
                if return_base64:
                    try:
                        image_response = requests.get(image_url)
                        image_response.raise_for_status()
                        image = Image.open(BytesIO(image_response.content))
                        
                        # 转换为 base64
                        buffered = BytesIO()
                        image.save(buffered, format="JPEG")
                        img_str = base64.b64encode(buffered.getvalue()).decode()
                        result_data["base64"] = img_str
                    except Exception as e:
                        result_data["base64_error"] = f"无法下载或转换图片: {str(e)}"
                
                return result_data
                
            elif data["task_status"] == "FAILED":
                return {
                    "success": False,
                    "error": "图片生成失败",
                    "task_id": task_id,
                    "details": data.get("error_message", "未知错误")
                }
        
        # 超时
        return {
            "success": False,
            "error": f"任务超时，已等待 {max_attempts * 5} 秒",
            "task_id": task_id
        }
        
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"API 请求失败: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"未知错误: {str(e)}"
        }


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """
    列出可用的工具
    """
    return [
        Tool(
            name="generate_image",
            description="使用 ModelScope Qwen-Image 模型生成图片",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "图片生成提示词，支持中文和英文"
                    },
                    "return_base64": {
                        "type": "boolean",
                        "description": "是否返回图片的 base64 编码数据，默认为 False",
                        "default": False
                    }
                },
                "required": ["prompt"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent | ImageContent | EmbeddedResource]:
    """
    处理工具调用
    """
    if name != "generate_image":
        raise ValueError(f"未知工具: {name}")
    
    # 获取参数
    prompt = arguments.get("prompt")
    return_base64 = arguments.get("return_base64", False)
    
    if not prompt:
        raise ValueError("prompt 参数是必需的")
    
    # 生成图片
    result = await generate_image_async(prompt, return_base64)
    
    # 构建响应
    if result.get("success"):
        response_text = f"✅ 图片生成成功！\n\n"
        response_text += f"🔗 图片链接: {result['image_url']}\n"
        response_text += f"📝 提示词: {prompt}\n"
        response_text += f"🆔 任务ID: {result['task_id']}"
        
        if result.get("base64"):
            response_text += f"\n\n📎 已生成 base64 编码数据 (长度: {len(result['base64'])} 字符)"
        elif result.get("base64_error"):
            response_text += f"\n\n⚠️ base64 转换失败: {result['base64_error']}"
        
        return [TextContent(type="text", text=response_text)]
    else:
        error_text = f"❌ 图片生成失败\n\n"
        error_text += f"💬 提示词: {prompt}\n"
        error_text += f"🚫 错误信息: {result.get('error', '未知错误')}"
        
        if result.get("task_id"):
            error_text += f"\n🆔 任务ID: {result['task_id']}"
        
        if result.get("details"):
            error_text += f"\n📋 详细信息: {result['details']}"
        
        return [TextContent(type="text", text=error_text)]


async def main():
    """
    主函数 - 启动 MCP 服务器
    """
    # 检查 API Key
    if not API_KEY:
        print("错误: 未找到 MODELSCOPE_API_KEY 环境变量", file=sys.stderr)
        print("请设置环境变量: export MODELSCOPE_API_KEY=your_api_key", file=sys.stderr)
        sys.exit(1)
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="modelscope-image-mcp",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities={},
                ),
            ),
        )


def cli_main():
    """CLI 入口点"""
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("ModelScope Image MCP Server")
        print("Usage: modelscope-image-mcp")
        print("Environment variables:")
        print("  MODELSCOPE_API_KEY: Your ModelScope API key (required)")
        return
    
    asyncio.run(main())


if __name__ == "__main__":
    cli_main()