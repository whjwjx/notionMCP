# Notion MCP Server

本项目提供了一个基于 Python 的 Notion MCP (Model Context Protocol) 服务，支持通过 IDE 插件（如 Trae）直接调用 Notion API 进行数据库操作。

## 核心功能

- **动态属性检测**：自动识别 Notion 数据库的标题属性（Title Property），无需硬编码。
- **页面管理**：支持查询、创建及更新页面内容，适配最新的 API 版本。
- **稳定性增强**：针对不同操作自动选择最匹配的 Notion API 版本（如 2022-06-28 用于查询，2025-09-03 用于多数据源支持）。
- **MCP 集成**：通过 `fastmcp` 封装，支持在 Trae 等 IDE 中通过对话直接操控 Notion。

## 快速配置

### 1. 环境准备
在项目根目录创建 `.env` 文件（参考 `.env.example`）：
```env
NOTION_TOKEN=your_integration_token_here
DATABASE_ID=your_database_id_here
```

### 2. 在 Trae 中添加 MCP
打开 Trae 的 MCP 设置，添加以下配置：
```json
{
  "mcpServers": {
    "notion-mcp": {
      "command": "python",
      "args": [
        "D:\\github_items\\notionMCP\\notion_mcp.py"
      ],
      "workingDirectory": "D:\\github_items\\notionMCP",
      "transport": "stdio"
    }
  }
}
```
*注意：请根据您的实际环境修改 `args` 和 `workingDirectory` 中的路径。*

## 使用示例

在 Trae 对话框中，您可以直接发送指令，例如：
- "在 Notion 数据库中搜索标题包含 '测试' 的页面"
- "在 Notion 中新建一个页面，标题为 '今日进度'，内容为 '已完成接口开发'"
- "更新 Notion 页面 ID 为 <PAGE_ID> 的工作内容"

## 项目结构

- [notion_mcp.py](file:///d:/github_items/notionMCP/notion_mcp.py)：MCP 服务核心实现，包含所有工具定义。
- [notion_demo.py](file:///d:/github_items/notionMCP/notion_demo.py)：Notion API 底层请求封装。
- [features.md](file:///d:/github_items/notionMCP/features.md)：详细的功能支持列表及参数说明。
- [bug_fixes.md](file:///d:/github_items/notionMCP/bug_fixes.md)：已知问题及其修复记录。

## 安全提示

- **隐私保护**：严禁将包含真实 Token 或 ID 的 `.env` 文件提交至仓库。
- **权限管理**：确保您的 Notion Integration 拥有目标数据库的读取和写入权限。
