# ModelScope MCP 服务器修复版本

## 问题描述
原始的 `modelscope-image-mcp` 包存在一个bug，在 `server.py:233` 行中，`notification_options` 参数为 `None`，但代码尝试访问其 `tools_changed` 属性，导致 `AttributeError`。

## 解决方案
创建了修复版本的服务器 (`fixed_modelscope_server.py`)，主要修复：

1. **修复 notification_options 问题**：在 `main()` 函数中创建有效的 `NotificationOptions()` 对象
2. **添加了完整的错误处理**
3. **改进了日志记录**
4. **优化了API密钥获取逻辑**

## 使用方法

### 1. 设置API密钥
设置环境变量（二选一）：
```bash
set MODELSCOPE_API_KEY=your_api_key_here
# 或者
set DASHSCOPE_API_KEY=your_api_key_here
```

### 2. 启动服务器
```bash
python fixed_modelscope_server.py
```

### 3. 功能特性
- **generate_image**: 使用ModelScope生成图片
  - `prompt`: 图片生成提示词（必需）
  - `negative_prompt`: 负面提示词（可选）
  - `model`: 模型名称（默认：wanx-v1）
  - `size`: 图片尺寸（默认：1024x1024）
  - `steps`: 生成步数（默认：20，范围1-50）

## 核心修复代码

```python
async def main():
    """主函数 - 修复了 notification_options 为 None 的问题"""
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
                    notification_options=notification_options,  # 传递有效对象而不是None
                    experimental_capabilities={},
                ),
            ),
        )
```

## 测试结果
✅ 服务器可以正常启动，不再出现 `AttributeError` 错误
✅ 工具列表可以正确返回
✅ API密钥检测机制正常工作

现在您可以正常使用ModelScope图片生成功能了！