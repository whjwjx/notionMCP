# fastNotion MCP 问题与解决记录

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

---

## 4. 跨项目调用时丢失 Database ID (Invalid request URL / Missing ID)

### 问题描述
在非项目工作区调用 MCP 时，AI 无法获取当前项目的环境变量，导致传给 `query_database` 等工具的 `database_id` 为空，从而引发 `400 Invalid request URL` 错误。

### 原因分析
1. **上下文缺失**：AI 在新项目中没有关于上一个项目配置的记忆。
2. **参数必填**：原代码将 `database_id` 设为必填参数，且未提供默认回退机制。

### 解决办法
1. **参数可选化**：将所有工具的 `database_id` 参数设为可选（`None`）。
2. **增加回退逻辑**：实现 `get_default_database_id` 函数，优先从 `os.environ`（MCP 配置的环境变量）读取，其次读取 `.env` 文件。
3. **优化工具描述**：在 Docstring 中明确告知 AI 该参数可选，如果不填则使用配置的默认值。

---

## 5. 创建页面结构错误 (Incorrect parent structure in create_notion_page)

### 问题描述
调用 `create_notion_page` 时，即使参数正确，Notion API 也会报错，无法成功创建页面。

### 原因分析
代码中错误地使用了 `data_source_id` 作为父级节点类型。这属于 Notion 某些特定同步数据库的 API 结构。对于绝大多数普通数据库，应该直接使用 `database_id`。

### 解决办法
将 `create_notion_page` 中的 `payload` 结构修改为标准的 `{"parent": {"database_id": database_id}}`，并移除了不必要的 `data_sources` 查询逻辑，提高了执行效率和兼容性。
