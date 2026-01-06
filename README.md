# Notion MCP Server

本项目提供了一个基于 Python 的 Notion MCP (Model Context Protocol) 服务，支持通过 IDE 插件（如 Trae）直接调用 Notion API。

## 核心功能
- **页面管理**：创建页面、更新属性（适配 Notion API 2025-09-03 版本）。
- **多数据源支持**：支持 Notion 的 `data_sources` 概念，自动识别并关联父级数据源。
- **MCP 集成**：通过 `fastmcp` 封装，支持 IDE 插件无缝调用。

## 快速配置

### 1. 环境准备
在项目根目录创建 `.env` 文件：
```env
NOTION_TOKEN=your_integration_token
# 可选：默认数据库 ID
# DATABASE_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

### 2. 在 Trae 中添加 MCP
在 Trae 的 MCP 配置文件中添加以下内容：
```json
{
  "mcpServers": {
    "notion-mcp": {
      "command": "<PYTHON_PATH>\\python.exe",
      "args": [
        "<PROJECT_PATH>\\mcp_demo.py"
      ],
      "workingDirectory": "<PROJECT_PATH>",
      "transport": "stdio"
    }
  }
}
```
*请将 `<PYTHON_PATH>` 和 `<PROJECT_PATH>` 替换为您的实际路径。*

## 使用说明
- **创建/更新页面**：
  ```bash
  python notion_demo.py --database-id <id> --title "标题" --work-content "内容"
  ```
- **验证 MCP**：启动后在 IDE 中尝试调用 `add` 或 Notion 相关工具。

## 安全提示
- **不要提交 `.env` 文件**。
- 定期更换 Notion Integration Token 以确保安全。

## 相关代码
- [notion_demo.py](file:///d:/github_items/notionMCP/notion_demo.py)：Notion API 核心逻辑。
- [mcp_demo.py](file:///d:/github_items/notionMCP/mcp_demo.py)：MCP 服务入口。
