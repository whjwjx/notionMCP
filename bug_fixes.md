# Notion MCP 问题与解决记录

## 1. 环境变量读取失败 (Missing NOTION_TOKEN)

### 问题描述
在 MCP 服务器模式下运行时，即使项目根目录下存在 `.env` 文件，代码仍报错 `Missing NOTION_TOKEN`。

### 原因分析
MCP 服务器的启动路径（Working Directory）可能与脚本所在目录不一致，导致使用相对路径 `os.path.exists(".env")` 无法定位到配置文件。

### 解决办法
在 `get_token` 函数中，通过 `os.path.abspath(__file__)` 获取脚本的绝对路径，并据此构建 `.env` 的绝对路径，确保在任何启动环境下都能正确读取。

---

## 2. 数据库查询报错 (Invalid request URL / Status 400)

### 问题描述
调用 `query_database` 接口时，API 返回 `400 Invalid request URL`。

### 原因分析
1. **API 版本差异**：Notion API `2025-09-03` 版本对标准数据库的 `query` 端点可能存在兼容性或严格性要求（主要针对多数据源设计）。
2. **ID 格式问题**：输入的 `database_id` 可能带有尖括号 `<>` 或连字符 `-`，导致 URL 拼接非法。

### 解决办法
1. 在 `query_database` 函数中，针对查询操作强制回退到更稳定的 `2022-06-28` 版本。
2. 增加了 ID 清理逻辑，自动剔除首尾空格、尖括号及中间的连字符。

---

## 3. 属性名不匹配 (Property 'Name' does not exist)

### 问题描述
查询或创建页面时报错，提示属性名不存在。

### 原因分析
代码默认假设数据库的标题属性名为 `Name`，但实际数据库中该属性可能被重命名（如本例中的 `日期`）。

### 解决办法
1. 引入了 `find_title_property_name` 函数，通过获取数据库元数据动态识别类型为 `title` 的属性名称。
2. 在所有涉及属性操作的工具中，优先调用自动识别逻辑，而非硬编码属性名。
