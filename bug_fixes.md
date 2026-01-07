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

---

## 6. 复杂属性添加失败 (Status 400 / Validation Error)

### 问题描述
尝试通过 MCP 工具新增 `status` 类型属性或复杂的 `select` 属性时，API 返回 `400 validation_error`。

### 原因分析
1. **嵌套结构解析问题**：MCP 框架在处理嵌套字典参数（如 `{"status": {}}`）时，有时会将其错误地序列化为 `null`，而 Notion API 要求新增属性时必须提供空对象 `{}`。
2. **类型限制**：`status` 属性在通过 API 新增时校验极其严格，且不如 `select` 类型灵活。

### 解决办法
1. **改用 Select 类型**：对于“状态”类需求，优先使用 `select` 类型，其 API 结构更简单且支持自定义颜色和选项。
2. **硬编码结构化工具**：在专门的结构升级工具（如 `upgrade_database_schema`）中直接定义完整的属性 JSON 结构，避免通过动态参数传递可能导致的解析歧义。

---

## 7. 页面正文写入支持 (Children blocks in create_notion_page)

### 问题描述
原工具仅支持设置数据库属性，无法在创建页面时直接写入详细的工作内容（正文）。

### 原因分析
Notion API 将属性（Properties）和正文（Children/Blocks）分开处理。原 `create_notion_page` 仅封装了 `properties` 字段。

### 解决办法
1. **升级工具参数**：为 `create_notion_page` 增加了可选的 `content` 参数。
2. **构造 Children 字段**：在请求体中动态构建 `children` 数组，将 `content` 作为第一个 `paragraph` 块写入。
3. **新增追加工具**：实现了 `append_page_content` 工具，支持向已有页面继续追加内容块。

---

## 8. Docstring 中的敏感数据泄露 (Sensitive Data Leakage in Docstrings)

### 问题描述
在为 AI 优化 MCP 接口描述（Docstrings）时，示例代码中不慎包含了真实的 `database_id` 和 `page_id`。

### 原因分析
为了确保 AI 能够理解参数格式，开发过程中直接使用了测试环境下的真实 ID 作为 `参数结构` 的示例，导致这些敏感信息暴露在源代码和 MCP 注册信息中。

### 解决办法
1. **数据脱敏**：对所有 MCP 接口的 `Docstrings` 进行了审查，将真实的 UUID 替换为通用的占位符（如 `your_database_id_here`）。
2. **规范化模板**：确立了接口描述的标准化结构（功能、入参、参数结构、返回），并在示例中使用明显的非真实数据，防止未来再次发生类似泄露。
3. **安全审计**：执行了全局搜索，确认除了受保护的 `.env` 文件外，代码库中不再存留任何真实的集成凭据。
