<div align="center">

# ⚡ fastNotion MCP
### 极智 Notion 连接器：让 AI 助手拥有“原生” Notion 操作超能力

<p align="center">
  <img src="https://img.shields.io/badge/Notion-API-000000?style=for-the-badge&logo=notion&logoColor=white" height="34" alt="Notion API" />
  &nbsp;&nbsp;&nbsp;
  <img src="https://img.shields.io/badge/fastMCP-Framework-5B8DEF?style=for-the-badge&logo=python&logoColor=white" height="34" alt="fastMCP" />
</p>

<p align="center">
  <b>Notion API</b> &nbsp; 🤝 &nbsp; <b>fastMCP</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Trae-000000?style=for-the-badge&logo=trae&logoColor=white" />
  <img src="https://img.shields.io/badge/Cursor-000000?style=for-the-badge&logo=cursor&logoColor=white" />
  <img src="https://img.shields.io/badge/Claude-7C3AED?style=for-the-badge&logo=anthropic&logoColor=white" />
  <img src="https://img.shields.io/badge/VS_Code-007ACC?style=for-the-badge&logo=visual-studio-code&logoColor=white" />
</p>

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![fastMCP](https://img.shields.io/badge/fastMCP-Framework-5B8DEF.svg)](https://github.com/jlowin/fastmcp)
[![Notion API](https://img.shields.io/badge/Notion-API-black.svg)](https://developers.notion.com/)

---

**fastNotion MCP** 基于 fastMCP 打造，让你的 AI 助手（Trae/Cursor/Claude）真正“读懂”并“操作” Notion。

</div>

不用再手动复制粘贴 ID，不用担心 API 报错，它就像给你的 AI 装了一个 **Notion 专用插件**。

---

## ✨ 为什么它这么强？ (Superpowers)

| 🛠️ 核心功能 | 🎯 痛点解决 | 🚀 极致体验 |
| :--- | :--- | :--- |
| **AI 灵感落库** | 代码复盘、工作日志、AI 总结出的干货难以快速归档。 | **一键直连 Notion**，无需手动搬运，让 AI 成果瞬间转化为结构化知识。 |
| **Schema 自适应** | 数据库字段名改了、属性变了？传统工具容易报错失效。 | **智能识别标题与属性**，无需硬编码，AI 能像人类一样理解你的表格。 |
| **API 稳如磐石** | Notion API 版本迭代快，请求参数复杂，老代码动不动就挂。 | 内置 **API 智能路由** 与多版本兼容逻辑，长效稳定，告别 400 报错。 |
| **开发者直供** | 小工具最怕没人维护，遇到 Bug 没人管。 | **作者深度自用**，持续进化，Bug 发现即修复，体验永远保持在第一梯队。 |
---

## 🛠️ 部署流程 (Deployment Workflow)

请按照以下步骤在您的本地环境部署并激活服务：

### 1. 克隆项目与安装环境
首先，将项目克隆到本地并安装必要的依赖库：
```bash
# 克隆仓库 (请替换为您的实际 URL)
git clone https://github.com/whjwjx/notionMCP.git
cd notionMCP

# 安装核心依赖
pip install -r requirements.txt
```

### 2. 配置 Notion 凭证
在项目根目录创建 `.env` 文件，用于存储私密配置：
```env
# 必填：Notion 机器人 Integration Token
NOTION_TOKEN=your_integration_token_here

# 必填：目标数据库 ID
DATABASE_ID=your_database_id_here
```
> 💡 **重要**：请确保在 Notion 数据库设置中通过 `Add connections` 邀请了您的机器人。

### 3. 本地验证与启动
在接入 IDE 前，建议手动运行脚本以确认环境与凭证无误：
```bash
python notion_mcp.py
```
若未提示错误（控制台保持静默即表示 `stdio` 传输已就绪），则说明配置成功。

### 4. IDE 接入 (以 Trae 为例)
打开 Trae 的 MCP 设置（通常在 `Settings -> MCP`），添加如下 JSON 配置：
```json
{
  "mcpServers": {
    "notion-mcp": {
      "command": "python",
      "args": ["<您的项目绝对路径>\\notion_mcp.py"],
      "workingDirectory": "<您的项目绝对路径>",
      "transport": "stdio"
    }
  }
}
```
*注意：请将 `<您的项目绝对路径>` 替换为您本地克隆项目的实际路径。*

---

## 📖 使用指南 (Usage Examples)

您可以像和同事沟通一样，在 AI 对话框中下达指令。以下是核心功能的详细调用参考：

### 1. 数据库管理与探索
- **功能描述**：获取数据库的元数据、结构、ID 以及数据源信息。
- **指令示例**：`帮我查一下 Notion 数据库 <您的数据库ID> 的结构信息`
- **调用工具**：`get_database_info(database_id="...")`
- **预期结果**：返回数据库的 JSON 定义，包括标题（如“工作日志”）、创建时间及关联的数据源 ID。

### 2. 精准页面搜索
- **功能描述**：在数据库内根据关键词或特定条件筛选页面。
- **指令示例**：`在数据库 <您的数据库ID> 中搜一下标题包含“测试”的页面`
- **调用工具**：`query_database(database_id="...", filter_params={"property": "...", "title": {"contains": "测试"}})`
- **预期结果**：返回匹配的页面列表，包含页面 ID、标题摘要及访问链接。

### 3. 智能页面创建
- **功能描述**：在指定数据库中自动关联数据源并创建新页面。
- **指令示例**：`在数据库 <您的数据库ID> 中新建页面，标题“今日代码提交”，内容“完成 MCP 接口封装”`
- **调用工具**：`create_notion_page(database_id="...", title="...", content="...")`
- **预期结果**：在 Notion 中成功创建记录，并返回该页面的完整 URL 链接。

### 4. 动态属性更新
- **功能描述**：通过页面 ID 快速更新现有页面的富文本属性内容。
- **指令示例**：`更新 Notion 页面 <您的页面ID> 的内容为“测试更新功能成功”`
- **调用工具**：`update_notion_page(page_id="...", content="...")`
- **预期结果**：目标页面属性被即时修改，并返回更新后的页面跳转链接。

---

## 📂 项目架构 (Architecture)

```text
.
├── notion_mcp.py    # 核心：MCP 服务入口与工具定义
├── notion_demo.py   # 底层：Notion API 请求封装引擎
├── requirements.txt # 依赖：项目运行环境清单
├── features.md      # 文档：全量功能支持手册
└── bug_fixes.md     # 记录：已知问题修复路线图
```

---

## 🛡️ 安全与合规 (Safety)

- **隐私第一**：本项目严禁在代码中硬编码任何密钥。请务必妥善保管 `.env` 文件，避免提交至公开仓库。
- **权限最小化**：建议仅为 Integration 开启必要的数据库访问权限，遵循最小授权原则。

---

## 🗺️ 未来路线图 (Roadmap)

### 🧱 内容深度管理 (Content Mastery)
- [x] **动态属性识别**：自动适配数据库 Schema，无需硬编码。
- [x] **多版本 API 路由**：智能兼容 Notion 不同时期的 API 特性。
- [ ] **块级（Blocks）深度读写**：支持 AI 直接操作页面内的代码块、待办列表。
- [ ] **互动评论集成**：在 IDE 内直接查看并回复 Notion 页面评论。

### ⚙️ 自动化工作流 (Workflow Automation)
- [ ] **任务状态自动流转**：一键完成任务状态更新及时间戳记录。
- [ ] **AI 自动化摘要**：根据数据库变动自动生成日报/周报。
- [ ] **模板化一键建页**：支持调用 Notion 数据库模板创建结构化内容。

### 🔍 搜索与导航 (Search & Navigation)
- [ ] **全局跨库搜索**：突破单一数据库限制，实现全空间检索。
- [ ] **层级导航增强**：让 AI 理解页面间的父子嵌套关系。

---
