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

---

## 9. FastMCP Cloud 部署报错 (Already running asyncio)

### 问题描述
在 FastMCP Cloud 部署时，服务启动失败并报 `ERROR Failed to run: Already running asyncio` 和 `Runtime.ExitError`。

### 原因分析
云端部署环境（如 FastMCP Cloud）通常已经运行在一个异步事件循环中。`mcp.run()` 内部尝试启动新的事件循环，导致与现有循环冲突。

### 解决办法
1. **事件循环感知**：修改启动逻辑，通过 `asyncio.get_running_loop()` 检测当前是否已有运行中的循环。
2. **条件启动**：如果检测到已在异步环境中，则跳过 `mcp.run()`，允许平台直接加载 `mcp` 对象；仅在本地直接执行脚本时才调用 `mcp.run()`。
3. **Entrypoint 优化**：推荐将云端启动入口配置为 `notion_mcp.py:mcp`，绕过 `__main__` 块。

---

## 10. 启动时缺少提示信息 (Missing Startup Hints in Stdio Mode)

### 问题描述
本地启动 MCP 服务时，控制台没有任何反应，用户无法确认服务是否已就绪或配置是否正确。

### 原因分析
MCP 默认使用 `stdio` 传输协议。如果直接使用 `print()` 输出提示，这些内容会被发送到 `stdout`，干扰 MCP 协议的数据传输，导致客户端解析错误。

### 解决办法
1. **重定向到 Stderr**：使用 `print(..., file=sys.stderr)` 将所有启动提示、配置状态及错误警告输出到标准错误流。
2. **信息脱敏展示**：增加启动 Banner，并对敏感的 Token 进行掩码处理（如 `ntn_...****`），既提供了反馈又保护了隐私。

---

## 13. 属性名修改导致匹配失效 (Property Matching Robustness)

### 问题描述
当用户将 Notion 数据库的列名从“工作内容”改为 `Summary` 或 `Description` 时，系统无法识别并将数据写入了错误的列，或因找不到必填项报错。

### 原因分析
1. **别名库不全**：最初的 `alias_map` 缺少对 `summary` 等常用词的覆盖。
2. **缺乏实时感知**：系统未能在操作前同步最新的 Schema，导致仍使用旧的列名逻辑进行匹配。
3. **分发策略单一**：默认将 content 放入正文 Block，未优先检查是否存在同名的属性列。

### 解决办法
1. **重构匹配引擎**：实现精准 > 拼音 > 别名 > 类型推断的多级匹配逻辑。
2. **引入架构驱动**：在 `create_notion_page` 和 `update_notion_page` 执行前强制拉取最新数据库定义。
3. **语义别名扩充**：在 `alias_map` 中补齐了 `summary`, `detail`, `phase` 等关键词。
4. **内容分发优化**：增加“属性名优先”原则，内容优先尝试归位到匹配的列中。

### 问题描述
在尝试保存网页内容到 Notion 时，频繁报 `400 validation_error`，提示 `body.properties.标题.id should be defined` 或 `Title property is mandatory`。

### 原因分析
1. **Notion API 严格校验**：`title` 属性（数据库中名为“标题”）是必填项，且必须符合特定的嵌套 JSON 结构。之前的代码在自动包装属性值时，有时无法准确识别标题属性，导致发送的结构不符合 Notion 规范。
2. **拼音映射冲突**：原有的拼音转换逻辑在处理带空格或下划线的复杂属性名（如 `Work_Content`）时不够稳健，且容易与数据库中已有的其他属性产生重合。
3. **数据结构重叠**：在自动填充“记录时间”等辅助属性时，由于缺乏类型校验，有时会错误地覆盖掉必填的标题属性。

### 解决办法
1. **推荐标准化命名**：通过将数据库属性名改为英文（如 `Title`, `Status`, `Work Type`, `Date`），从根本上消除了编码和拼音转换带来的不确定性。
2. **重构属性处理引擎**：
   - 引入了 `get_clean_key` 逻辑，实现对属性名大小写、空格、下划线的全兼容匹配。
   - 增加了基于数据库元数据的类型预检，确保每个值都按其真实类型（`title`, `select`, `date` 等）进行精确包装。
   - 实现了多级标题提取保底逻辑，确保无论用户如何传参，标题属性始终存在。
3. **精简映射逻辑**：移除了冗余的 `pypinyin` 依赖，采用更直接、高效的键值对映射，降低了代码复杂度。
