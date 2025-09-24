#!/usr/bin/env python3
"""
修复版本的 ModelScope MCP 服务器
解决了 notification_options 为 None 的问题
"""

import asyncio
import logging
import os
import json
from functools import lru_cache
from typing import Any, Optional
from io import BytesIO

import httpx
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp import types
from PIL import Image
from dotenv import load_dotenv


# 读取环境变量（支持 .env 文件）
load_dotenv()

# 配置日志记录（支持通过环境变量 MODELSCOPE_LOG_LEVEL 控制）
LOG_LEVEL = os.getenv("MODELSCOPE_LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO))
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


def get_polling_config() -> dict[str, Any]:
    """
    读取轮询策略配置，支持以下环境变量：
    - MODELSCOPE_POLL_INTERVAL_SECONDS: 基础轮询间隔(秒)，默认 5
    - MODELSCOPE_MAX_POLL_ATTEMPTS: 最大轮询尝试次数，默认 120（约 10 分钟）
    - MODELSCOPE_POLL_BACKOFF: 是否启用指数退避，默认 false
    - MODELSCOPE_MAX_POLL_INTERVAL_SECONDS: 退避的最大间隔(秒)，默认 30
    """
    def _as_bool(v: Optional[str]) -> bool:
        return str(v).lower() in {"1", "true", "yes", "y"}

    return {
        "base_interval": float(os.getenv("MODELSCOPE_POLL_INTERVAL_SECONDS", "5")),
        "max_attempts": int(os.getenv("MODELSCOPE_MAX_POLL_ATTEMPTS", "120")),
        "backoff": _as_bool(os.getenv("MODELSCOPE_POLL_BACKOFF", "false")),
        "max_interval": float(os.getenv("MODELSCOPE_MAX_POLL_INTERVAL_SECONDS", "30")),
    }


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
                    "size": {
                        "type": "string",
                        "description": "生成图像分辨率大小，Qwen-Image支持:[64x64,1664x1664]，默认为 '1024x1024'",
                        "default": "1024x1024",
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
                    "poll_interval_seconds": {
                        "type": "number",
                        "description": "轮询基础间隔(秒)，默认取环境变量或 5",
                    },
                    "max_poll_attempts": {
                        "type": "integer",
                        "description": "最大轮询次数，默认取环境变量或 120（约 10 分钟）",
                    },
                    "poll_backoff": {
                        "type": "boolean",
                        "description": "是否开启指数退避，默认取环境变量或 false",
                    },
                    "max_poll_interval_seconds": {
                        "type": "number",
                        "description": "指数退避的最大间隔(秒)，默认取环境变量或 30",
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
    size: str = "1024x1024",
    output_filename: str = "result_image.jpg",
    output_dir: str = "./outputs",
    poll_interval_seconds: Optional[float] = None,
    max_poll_attempts: Optional[int] = None,
    poll_backoff: Optional[bool] = None,
    max_poll_interval_seconds: Optional[float] = None,
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

        # 加载轮询配置（环境变量 + 可选参数覆盖）
        cfg = get_polling_config()
        base_interval = poll_interval_seconds if poll_interval_seconds is not None else cfg["base_interval"]
        max_attempts = max_poll_attempts if max_poll_attempts is not None else cfg["max_attempts"]
        use_backoff = poll_backoff if poll_backoff is not None else cfg["backoff"]
        max_interval = max_poll_interval_seconds if max_poll_interval_seconds is not None else cfg["max_interval"]
        
        # 准备请求头
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-ModelScope-Async-Mode": "true"
        }
        
        # 准备请求数据
        data = {
            "model": model,
            "prompt": prompt,
            "size": size
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
            submit_request_id = response.headers.get("X-Request-Id")
            if not task_id:
                return [
                    types.TextContent(
                        type="text",
                        text=(
                            "任务提交失败\n"
                            f"status_code: {response.status_code}\n"
                            f"request_id: {submit_request_id}\n"
                            f"body: {task_result}"
                        ),
                    )
                ]
            
            logger.info(f"任务已提交，任务ID: {task_id}")
            
            # 准备轮询请求头
            poll_headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "X-ModelScope-Task-Type": "image_generation"
            }
            
            # 轮询任务状态（默认最多约 10 分钟，可配置）
            attempt = 0
            
            while attempt < max_attempts:
                # 动态等待时间（固定或指数退避）
                wait_time = base_interval if not use_backoff else min(base_interval * (2 ** attempt), max_interval)
                await asyncio.sleep(wait_time)
                attempt += 1
                
                result_response = await client.get(
                    f"{MODELSCOPE_API_BASE}v1/tasks/{task_id}",
                    headers=poll_headers
                )
                result_response.raise_for_status()
                result_data = result_response.json()
                
                task_status = result_data.get("task_status")
                poll_request_id = result_response.headers.get("X-Request-Id")
                logger.info(
                    f"任务状态: {task_status} (尝试 {attempt}/{max_attempts}, wait={wait_time:.2f}s)"
                )
                
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
                    image_request_id = image_response.headers.get("X-Request-Id")
                    content_type = image_response.headers.get("Content-Type", "")
                    if not content_type.startswith("image/"):
                        logger.error(
                            f"下载的内容不是图片，Content-Type={content_type}, status={image_response.status_code}"
                        )
                        return [
                            types.TextContent(
                                type="text",
                                text=(
                                    "图片下载失败：返回的内容不是图片\n"
                                    f"status_code: {image_response.status_code}\n"
                                    f"request_id: {image_request_id}\n"
                                    f"content_type: {content_type}"
                                ),
                            )
                        ]
                    
                    # 使用PIL保存图片
                    image = Image.open(BytesIO(image_response.content))
                    # 根据扩展名自动推断格式，若为 JPG 且存在 alpha 通道，转换为 RGB 以避免保存报错
                    try:
                        if output_path.lower().endswith((".jpg", ".jpeg")) and image.mode in ("RGBA", "P"):
                            image = image.convert("RGB")
                        image.save(output_path)
                    except Exception as save_err:
                        logger.error(f"图片保存失败: {save_err}")
                        return [
                            types.TextContent(
                                type="text",
                                text=f"图片保存失败: {save_err}",
                            )
                        ]
                    
                    return [
                        types.TextContent(
                            type="text",
                            text=f"图片生成成功！\n"
                                 f"提示词: {prompt}\n"
                                 f"模型: {model}\n"
                                 f"分辨率: {size}\n"
                                 f"保存路径: {os.path.abspath(output_path)}\n"
                                 f"输出目录: {os.path.abspath(output_dir)}\n"
                                 f"文件名: {output_filename}\n"
                                 f"图片URL: {image_url}\n"
                                 f"request_id: {poll_request_id or submit_request_id}",
                        )
                    ]
                    
                elif task_status == "FAILED":
                    error_msg = result_data.get("message", "任务失败")
                    status_code = result_data.get("status_code") or result_data.get("code") or result_response.status_code
                    logger.error(
                        f"图片生成失败: {error_msg}, status_code={status_code}, request_id={poll_request_id}, body={result_data}"
                    )
                    return [
                        types.TextContent(
                            type="text",
                            text=(
                                f"图片生成失败: {error_msg}\n"
                                f"status_code: {status_code}\n"
                                f"request_id: {poll_request_id}\n"
                                f"body: {result_data}"
                            ),
                        )
                    ]
                
                # 如果状态是PENDING或RUNNING，继续轮询
                
            # 超时
            return [
                types.TextContent(
                    type="text",
                    text=(
                        "图片生成超时，任务可能仍在处理中\n"
                        f"max_attempts: {max_attempts}\n"
                        f"base_interval: {base_interval}\n"
                        f"backoff: {use_backoff}\n"
                        f"max_interval: {max_interval}"
                    ),
                )
            ]
                
    except httpx.HTTPStatusError as http_err:
        resp = http_err.response if hasattr(http_err, "response") else None
        status_code = getattr(resp, "status_code", None)
        request_id = resp.headers.get("X-Request-Id") if resp else None
        body = None
        try:
            body = resp.text if resp else None
        except Exception:
            body = None
        logger.error(
            f"HTTP错误: status_code={status_code}, request_id={request_id}, body={body}"
        )
        return [
            types.TextContent(
                type="text",
                text=(
                    "请求失败\n"
                    f"status_code: {status_code}\n"
                    f"request_id: {request_id}\n"
                    f"body: {body}"
                ),
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
                server_version="1.1.0",
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