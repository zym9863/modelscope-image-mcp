# 发布说明

## 已完成的修改

### 1. 更新了 `pyproject.toml`
- 添加了发布到 PyPI 所需的所有元数据
- 包括作者信息、许可证、关键词、分类器等
- 配置了项目 URL（主页、仓库、问题跟踪）

### 2. 创建了 GitHub Actions 工作流
- 文件位置：`.github/workflows/publish.yml`
- 支持在创建 release 或推送 tag 时自动发布到 PyPI
- 使用了 Trusted Publisher 机制，无需 API token

### 3. 更新了 README 文档
- 添加了三种安装方法：
  - **方法1（推荐）**：从 PyPI 直接安装：`uvx modelscope-image-mcp`
  - **方法2**：从 GitHub 仓库直接安装
  - **方法3**：本地开发安装
- 更新了使用说明和测试方法

### 4. 测试了构建和发布流程
- ✅ 本地构建成功：`uv build`
- ✅ wheel 文件安装测试成功
- ✅ 命令行入口点工作正常

## 下一步操作

要完成发布到 PyPI，需要：

1. **推送代码到 GitHub**：
   ```bash
   git add .
   git commit -m "Prepare for PyPI release"
   git push
   ```

2. **创建 release**：
   - 在 GitHub 上创建一个新的 release（例如 v0.1.0）
   - GitHub Actions 会自动触发并发布到 PyPI

3. **配置 PyPI Trusted Publisher**（首次发布需要）：
   - 访问 https://pypi.org/manage/account/publishing/
   - 添加新的 Trusted Publisher
   - Owner: `zym9863`
   - Repository name: `modelscope-image-mcp`
   - Workflow name: `publish.yml`

## 使用方式

发布成功后，用户可以像 `markitdown-mcp` 一样简单配置：

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

不再需要克隆仓库到本地！