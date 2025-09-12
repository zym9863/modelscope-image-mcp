#!/usr/bin/env python3
"""
修复版本的 ModelScope MCP 服务器
解决了 notification_options 为 None 的问题
"""

import asyncio
import logging
import os
from functools import lru_cache
from typing import Any, Optional

import httpx
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp import types
from pydantic import AnyUrl


# 配置日志记录
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("modelscope-image-mcp")

# ModelScope API配置
MODELSCOPE_API_BASE = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis"
DEFAULT_MODEL = "wanx-v1"

app = Server("modelscope-image-mcp")


@lru_cache(maxsize=1)
def get_api_key() -> str:
    """
    获取API密钥
    优先从环境变量MODELSCOPE_API_KEY获取，如果没有则从DASHSCOPE_API_KEY获取
    """
    api_key = os.getenv("MODELSCOPE_API_KEY") or os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("需要设置 MODELSCOPE_API_KEY 或 DASHSCOPE_API_KEY 环境变量")
    return api_key


@app.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    列出可用工具
    """
    return [
        types.Tool(
            name="generate_image",
            description="使用ModelScope生成图片",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "图片生成提示词",
                    },
                    "negative_prompt": {
                        "type": "string",
                        "description": "负面提示词（可选）",
                    },
                    "model": {
                        "type": "string",
                        "description": f"模型名称，默认为 {DEFAULT_MODEL}",
                        "default": DEFAULT_MODEL,
                    },
                    "size": {
                        "type": "string",
                        "description": "图片尺寸，格式为 'widthxheight'，默认为 '1024x1024'",
                        "default": "1024x1024",
                    },
                    "steps": {
                        "type": "integer",
                        "description": "生成步数，默认为 20",
                        "default": 20,
                        "minimum": 1,
                        "maximum": 50,
                    },
                },
                "required": ["prompt"],
            },
        )
    ]


@app.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
    """
    处理工具调用
    """
    if name == "generate_image":
        return await generate_image(**arguments)
    else:
        raise ValueError(f"未知工具: {name}")


async def generate_image(
    prompt: str,
    negative_prompt: Optional[str] = None,
    model: str = DEFAULT_MODEL,
    size: str = "1024x1024",
    steps: int = 20,
) -> list[types.TextContent]:
    """
    生成图片的核心函数
    """
    try:
        api_key = get_api_key()
        
        # 解析图片尺寸
        try:
            width, height = map(int, size.split("x"))
        except ValueError:
            raise ValueError(f"无效的图片尺寸格式: {size}，应为 'widthxheight' 格式")
        
        # 准备API请求参数
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        
        data = {
            "model": model,
            "input": {
                "prompt": prompt,
                "negative_prompt": negative_prompt or "",
            },
            "parameters": {
                "size": f"{width}*{height}",
                "n": 1,
                "steps": steps,
            },
        }
        
        logger.info(f"正在使用模型 {model} 生成图片，提示词: {prompt}")
        
        # 发送API请求
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(MODELSCOPE_API_BASE, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            
            if "output" in result and "results" in result["output"]:
                image_url = result["output"]["results"][0]["url"]
                return [
                    types.TextContent(
                        type="text",
                        text=f"图片生成成功！\n"
                        f"提示词: {prompt}\n"
                        f"模型: {model}\n"
                        f"尺寸: {size}\n"
                        f"步数: {steps}\n"
                        f"图片URL: {image_url}",
                    )
                ]
            else:
                error_msg = result.get("message", "未知错误")
                logger.error(f"图片生成失败: {error_msg}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"图片生成失败: {error_msg}",
                    )
                ]
                
    except Exception as e:
        logger.error(f"生成图片时发生错误: {str(e)}")
        return [
            types.TextContent(
                type="text",
                text=f"生成图片时发生错误: {str(e)}",
            )
        ]


async def main():
    """
    主函数 - 修复了 notification_options 为 None 的问题
    """
    async with stdio_server() as (read_stream, write_stream):
        # 修复：确保 notification_options 不为 None
        notification_options = NotificationOptions()
        
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="modelscope-image-mcp",
                server_version="1.0.0",
                capabilities=app.get_capabilities(
                    notification_options=notification_options,  # 传递有效的对象而不是 None
                    experimental_capabilities={},
                ),
            ),
        )


def cli_main():
    """
    CLI入口点
    """
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("服务器已停止")
    except Exception as e:
        logger.error(f"服务器启动失败: {e}")
        raise


if __name__ == "__main__":
    cli_main()