#!/usr/bin/env python3
"""
修复版本的 ModelScope MCP 服务器
解决了 notification_options 为 None 的问题
"""

import asyncio
import logging
import os
import time
import json
from functools import lru_cache
from typing import Any, Optional
from io import BytesIO

import httpx
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp import types
from pydantic import AnyUrl
from PIL import Image


# 配置日志记录
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("modelscope-image-mcp")

# ModelScope API配置
MODELSCOPE_API_BASE = "https://api-inference.modelscope.cn/"
DEFAULT_MODEL = "Qwen/Qwen-Image"

app = Server("modelscope-image-mcp")


@lru_cache(maxsize=1)
def get_api_key() -> str:
    """
    获取API密钥
    从环境变量MODELSCOPE_SDK_TOKEN获取
    """
    api_key = os.getenv("MODELSCOPE_SDK_TOKEN")
    if not api_key:
        raise ValueError("需要设置 MODELSCOPE_SDK_TOKEN 环境变量")
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
                    "model": {
                        "type": "string",
                        "description": f"模型名称，默认为 {DEFAULT_MODEL}",
                        "default": DEFAULT_MODEL,
                    },
                    "output_filename": {
                        "type": "string", 
                        "description": "输出图片文件名，默认为 'result_image.jpg'",
                        "default": "result_image.jpg",
                    },
                    "output_dir": {
                        "type": "string",
                        "description": "输出目录路径，默认为 './outputs'",
                        "default": "./outputs",
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
    model: str = DEFAULT_MODEL,
    output_filename: str = "result_image.jpg",
    output_dir: str = "./outputs",
) -> list[types.TextContent]:
    """
    生成图片的核心函数 - 使用异步任务处理
    """
    try:
        # 创建输出目录（如果不存在）
        os.makedirs(output_dir, exist_ok=True)
        
        # 构建完整的输出文件路径
        output_path = os.path.join(output_dir, output_filename)
        
        api_key = get_api_key()
        
        # 准备请求头
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-ModelScope-Async-Mode": "true"
        }
        
        # 准备请求数据
        data = {
            "model": model,
            "prompt": prompt
        }
        
        logger.info(f"正在使用模型 {model} 生成图片，提示词: {prompt}")
        
        # 异步提交任务
        async with httpx.AsyncClient(timeout=60.0) as client:
            # 提交异步任务
            response = await client.post(
                f"{MODELSCOPE_API_BASE}v1/images/generations",
                headers=headers,
                content=json.dumps(data, ensure_ascii=False).encode('utf-8')
            )
            response.raise_for_status()
            
            # 获取任务ID
            task_result = response.json()
            task_id = task_result.get("task_id")
            if not task_id:
                return [
                    types.TextContent(
                        type="text",
                        text=f"任务提交失败: {task_result}",
                    )
                ]
            
            logger.info(f"任务已提交，任务ID: {task_id}")
            
            # 准备轮询请求头
            poll_headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "X-ModelScope-Task-Type": "image_generation"
            }
            
            # 轮询任务状态
            max_attempts = 120  # 最多轮询2分钟
            attempt = 0
            
            while attempt < max_attempts:
                await asyncio.sleep(5)  # 等待5秒后查询状态
                attempt += 1
                
                result_response = await client.get(
                    f"{MODELSCOPE_API_BASE}v1/tasks/{task_id}",
                    headers=poll_headers
                )
                result_response.raise_for_status()
                result_data = result_response.json()
                
                task_status = result_data.get("task_status")
                logger.info(f"任务状态: {task_status} (尝试 {attempt}/{max_attempts})")
                
                if task_status == "SUCCEED":
                    # 任务成功，获取图片
                    output_images = result_data.get("output_images", [])
                    if not output_images:
                        return [
                            types.TextContent(
                                type="text", 
                                text="任务成功但没有输出图片",
                            )
                        ]
                    
                    image_url = output_images[0]
                    logger.info(f"图片生成成功，URL: {image_url}")
                    
                    # 下载并保存图片
                    image_response = await client.get(image_url)
                    image_response.raise_for_status()
                    
                    # 使用PIL保存图片
                    image = Image.open(BytesIO(image_response.content))
                    image.save(output_path)
                    
                    return [
                        types.TextContent(
                            type="text",
                            text=f"图片生成成功！\n"
                                 f"提示词: {prompt}\n"
                                 f"模型: {model}\n"
                                 f"保存路径: {os.path.abspath(output_path)}\n"
                                 f"输出目录: {os.path.abspath(output_dir)}\n"
                                 f"文件名: {output_filename}\n"
                                 f"图片URL: {image_url}",
                        )
                    ]
                    
                elif task_status == "FAILED":
                    error_msg = result_data.get("message", "任务失败")
                    logger.error(f"图片生成失败: {error_msg}")
                    return [
                        types.TextContent(
                            type="text",
                            text=f"图片生成失败: {error_msg}",
                        )
                    ]
                
                # 如果状态是PENDING或RUNNING，继续轮询
                
            # 超时
            return [
                types.TextContent(
                    type="text",
                    text="图片生成超时，任务可能仍在处理中",
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