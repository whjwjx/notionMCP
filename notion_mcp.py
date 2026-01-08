import os
import json
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import requests
from datetime import datetime, timedelta, timezone
from fastmcp import FastMCP
import pypinyin

# Initialize MCP
mcp = FastMCP("Notion MCP Server")

API_BASE = "https://api.notion.com/v1/"
# Default to the most stable version for property operations
DEFAULT_NOTION_VERSION = "2022-06-28"

def get_now_str():
    """Get current time in ISO 8601 format for Notion date property (Beijing time)."""
    tz_beijing = timezone(timedelta(hours=8))
    return datetime.now(tz_beijing).isoformat()

def mask_id(id_str):
    """脱敏处理 ID，仅保留前后 4 位。"""
    if not id_str or len(id_str) <= 8:
        return "****"
    return f"{id_str[:4]}...{id_str[-4:]}"

def load_env_vars():
    """从环境变量或 .env 文件安全加载配置。"""
    token = os.environ.get("NOTION_TOKEN")
    db_id = os.environ.get("DATABASE_ID")
    
    # 如果系统环境变量中没有，再尝试读取本地 .env 文件
    if not token or not db_id:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        env_path = os.path.join(base_dir, ".env")
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        k, v = line.split("=", 1)
                        k, v = k.strip(), v.strip().strip('"').strip("'")
                        if k == "NOTION_TOKEN" and not token:
                            token = v
                        elif k == "DATABASE_ID" and not db_id:
                            db_id = v
    
    # 如果依然缺失，在 stderr 输出警告（有助于云端日志排查）
    if not token:
        print("⚠️ 警告: 未找到 NOTION_TOKEN 配置", file=sys.stderr)
    if not db_id:
        print("⚠️ 警告: 未找到 DATABASE_ID 配置", file=sys.stderr)
        
    return token, db_id

def notion_request(method, path, body=None, version=DEFAULT_NOTION_VERSION):
    """
    Unified Notion API request handler.
    """
    token, _ = load_env_vars()
    if not token:
        return 0, {"error": "Missing NOTION_TOKEN in environment or .env file"}
    
    url = API_BASE + path
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": version,
        "Accept": "application/json",
    }
    
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")
    
    req = Request(url, data=data, headers=headers, method=method.upper())
    try:
        with urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        err_body = e.read().decode("utf-8", errors="ignore")
        try:
            parsed = json.loads(err_body)
        except Exception:
            parsed = {"error": err_body}
        return e.code, parsed
    except URLError as e:
        return 0, {"error": str(e)}

def find_title_property_name(database_id):
    """Helper to find the property name of type 'title'."""
    status, result = notion_request("GET", f"databases/{database_id}")
    if status == 200:
        props = result.get("properties", {})
        for name, spec in props.items():
            if spec.get("type") == "title":
                return name
    return "Name"  # Default fallback

def normalize_properties(db_id, input_props, db_props=None):
    """
    智能属性转换：
    1. 将输入属性名映射到数据库实际属性名（支持拼音、别名、大小写及模糊匹配）。
    2. 将简单的字符串值包装成 Notion 要求的复杂 JSON 结构。
    """
    if not input_props:
        return {}
    
    # 如果没有传入 db_props，则实时从 Notion 获取最新架构
    if db_props is None:
        status, db = notion_request("GET", f"databases/{db_id}")
        if status != 200:
            return input_props 
        db_props = db.get("properties", {})
    
    normalized = {}
    
    def get_clean_key(text):
        return text.lower().replace(" ", "").replace("_", "").replace("-", "")

    def get_pinyin(text):
        return "".join(pypinyin.lazy_pinyin(text.lower()))

    # 建立多维度映射索引
    name_map = {}
    for name in db_props.keys():
        clean_name = get_clean_key(name)
        py_name = get_pinyin(name)
        name_map[clean_name] = name
        name_map[py_name] = name

    # 常见别名映射 (语义增强)
    alias_map = {
        "content": ["workcontent", "summary", "description", "desc", "note", "内容", "描述", "备注", "工作内容", "detail"],
        "status": ["state", "zhuangtai", "状态", "进度", "phase"],
        "date": ["time", "riqi", "shijian", "日期", "时间", "when"],
        "type": ["category", "worktype", "leixing", "类型", "工作类型", "tag"]
    }
    
    # 逆向别名索引
    reverse_alias = {}
    for standard, aliases in alias_map.items():
        for alias in aliases:
            reverse_alias[get_clean_key(alias)] = standard

    # 预先按类型对数据库属性进行分组，用于语义推断
    props_by_type = {}
    for name, spec in db_props.items():
        ptype = spec.get("type")
        if ptype not in props_by_type:
            props_by_type[ptype] = []
        props_by_type[ptype].append(name)

    for key, value in input_props.items():
        clean_key = get_clean_key(key)
        py_key = get_pinyin(key)
        
        # 1. 优先级最高：直接匹配 (含大小写/空格忽略/拼音)
        target_key = name_map.get(clean_key) or name_map.get(py_key)
        
        # 2. 优先级中等：别名逻辑
        if not target_key:
            standard_term = reverse_alias.get(clean_key)
            if standard_term:
                target_key = next((name for name in db_props.keys() if standard_term in get_clean_key(name) or standard_term in get_pinyin(name)), None)
            
            # 模糊匹配：输入 key 包含在某个属性名中
            if not target_key:
                target_key = next((name for name in db_props.keys() if clean_key in get_clean_key(name) or clean_key in get_pinyin(name)), None)

        # 3. 优先级最低：语义类型推断 (当名称完全无法对应时)
        if not target_key:
            if clean_key in ["content", "desc", "note"] and len(props_by_type.get("rich_text", [])) == 1:
                target_key = props_by_type["rich_text"][0]
            elif clean_key in ["status", "state"] and len(props_by_type.get("status", [])) == 1:
                target_key = props_by_type["status"][0]
            elif clean_key in ["date", "time"] and len(props_by_type.get("date", [])) == 1:
                target_key = props_by_type["date"][0]

        if not target_key:
            normalized[key] = value 
            continue
            
        prop_info = db_props[target_key]
        prop_type = prop_info.get("type")
        
        # 已经包装好的结构不再包装
        if isinstance(value, dict) and (prop_type in value or "type" in value):
            normalized[target_key] = value
            continue
            
        # 包装简单值
        if prop_type == "select":
            normalized[target_key] = {"select": {"name": str(value)}} if value else None
        elif prop_type == "multi_select":
            if isinstance(value, list):
                normalized[target_key] = {"multi_select": [{"name": str(v)} for v in value]}
            else:
                normalized[target_key] = {"multi_select": [{"name": str(value)}]}
        elif prop_type == "rich_text":
            normalized[target_key] = {"rich_text": [{"text": {"content": str(value)}}]}
        elif prop_type == "title":
            normalized[target_key] = {"title": [{"text": {"content": str(value)}}]}
        elif prop_type == "date":
            if isinstance(value, str):
                # 增强日期处理：支持关键字和自动时间填充
                date_val = value
                if value.lower() in ["now", "today", "当前时间", "今天"]:
                    date_val = get_now_str()
                normalized[target_key] = {"date": {"start": date_val}}
            else:
                normalized[target_key] = value
        elif prop_type == "status":
            normalized[target_key] = {"status": {"name": str(value)}}
        else:
            normalized[target_key] = value
            
    return normalized

def infer_work_type(title, content, db_props):
    """
    根据标题和正文内容智能预测“Work Type”。
    """
    text = (title + (content or "")).lower()
    
    # 定义关键字映射
    mapping = {
        "📱 小程序端": ["miniprogram", "weixin", "微信", "mp"],
        "💻 vue后台web端": ["vue", "web", "frontend", "前端", "css", "html", "js", "ts", "page"],
        "🔌 fastAPI后台接口端": ["fastapi", "api", "backend", "python", "database", "server"],
        "📝 日常记录": ["daily", "routine", "日常", "记录", "test", "summary", "mcp"]
    }
    
    # 动态寻找“Work Type”属性名
    work_type_attr = next((name for name in db_props.keys() if name.lower() in ["work type", "work_type", "工作类型"]), None)
    if not work_type_attr:
        return None

    work_type_prop = db_props.get(work_type_attr, {})
    options = [opt.get("name") for opt in work_type_prop.get("select", {}).get("options", [])]
    
    best_match = None
    max_hits = 0
    
    for opt_name, keywords in mapping.items():
        # 在选项列表中寻找最接近的真实名称
        actual_name = next((o for o in options if opt_name in o or o in opt_name), None)
        if not actual_name:
            continue
            
        hits = sum(1 for kw in keywords if kw in text)
        if hits > max_hits:
            max_hits = hits
            best_match = actual_name
            
    return best_match or next((o for o in options if "Daily" in o or "日常" in o), options[0] if options else None)

@mcp.tool()
def list_databases() -> str:
    """
    功能: 列出当前集成有权访问的所有数据库。
    
    返回: 数据库列表的 JSON 字符串，包含每个数据库的标题和 ID。
    """
    body = {
        "filter": {
            "value": "database",
            "property": "object"
        }
    }
    status, results = notion_request("POST", "search", body=body)
    if status != 200:
        return f"错误 (状态码 {status}): {json.dumps(results, indent=2, ensure_ascii=False)}"
    
    databases = []
    for db in results.get("results", []):
        title_list = db.get("title", [])
        title = title_list[0].get("plain_text", "Untitled") if title_list else "Untitled"
        databases.append({
            "title": title,
            "id": db.get("id"),
            "url": db.get("url")
        })
    
    return json.dumps(databases, indent=2, ensure_ascii=False)

@mcp.tool()
def get_database_info(database_id: str = None) -> str:
    """
    功能: 获取 Notion 数据库的完整元数据，包括标题、架构(Schema)和属性定义。
    
    入参:
        - database_id (str, 可选): Notion 数据库 ID。若不填则使用配置的默认 ID。
    
    参数结构: 字符串形式的 UUID，例如 "your_database_id_here"。
    
    返回: 数据库详情的 JSON 字符串，包含属性名、类型及选项等信息。
    """
    _, default_db_id = load_env_vars()
    db_id = database_id or default_db_id
    if not db_id:
        return "错误: 未提供 database_id 且未发现默认配置。"

    status, db = notion_request("GET", f"databases/{db_id}")
    if status != 200:
        return f"错误 (状态码 {status})，数据库 ID: {mask_id(db_id)}。请检查集成权限。"
    return json.dumps(db, indent=2, ensure_ascii=False)

@mcp.tool()
def get_database_properties(database_id: str = None) -> str:
    """
    功能: 仅检索数据库的属性定义（列信息），用于了解有哪些字段可以操作。
    
    入参:
        - database_id (str, 可选): 数据库 ID。
    
    参数结构: 字符串，例如 "your_database_id_here"。
    
    返回: 属性架构的 JSON 字符串，显示每个属性的名称、ID 和类型（如 select, multi_select）。
    """
    _, default_db_id = load_env_vars()
    db_id = database_id or default_db_id
    if not db_id:
        return "Error: No database_id provided and no default DATABASE_ID found."

    status, db = notion_request("GET", f"databases/{db_id}")
    if status != 200:
        return f"Error (Status {status}): {json.dumps(db, indent=2, ensure_ascii=False)}"
    return json.dumps(db.get("properties", {}), indent=2, ensure_ascii=False)

@mcp.tool()
def query_database(database_id: str = None, filter_params: dict = None) -> str:
    """
    功能: 根据特定条件筛选并查询数据库中的页面。
    
    入参:
        - database_id (str, 可选): 目标数据库 ID。
        - filter_params (dict, 可选): Notion 标准查询对象。
    
    参数结构:
        - database_id: "your_database_id_here"
        - filter_params: {"property": "状态", "select": {"equals": "已完成"}}
          注：属性名支持拼音，如 {"property": "zhuang_tai", ...}
    
    返回: 匹配页面的列表 JSON，包含页面 ID、属性摘要及 URL。
    """
    _, default_db_id = load_env_vars()
    db_id = database_id or default_db_id
    if not db_id:
        return "Error: No database_id provided."

    # Clean ID
    db_id = db_id.strip().strip("<>").replace("-", "")
    
    body = {}
    if filter_params:
        body["filter"] = filter_params
        
    status, results = notion_request("POST", f"databases/{db_id}/query", body=body)
    if status != 200:
        return f"Error (Status {status}): {json.dumps(results, indent=2, ensure_ascii=False)}"
    return json.dumps(results, indent=2, ensure_ascii=False)

@mcp.tool()
def create_notion_page(database_id: str = None, title: str = "", properties: dict = None, content: str = None) -> str:
    """
    功能: 在指定数据库中创建一个新页面。
    
    入参:
        - database_id (str, 可选): 数据库 ID。
        - title (str, 必填): 页面标题。
        - properties (dict, 可选): 其他属性键值对。支持拼音映射和简单值自动包装。
        - content (str, 可选): 写入页面正文的内容。
    
    参数结构:
        - title: "优化用户登录页面"
        - properties: {"zhuang_tai": "已完成", "gong_zuo_lei_xing": "💻 vue后台web端"}
          (属性名会自动映射到“状态”、“工作类型”，字符串值会自动包装为对应的 select 或 rich_text 结构)
        - content: "修复了CSS兼容性问题..."
    
    返回: 成功时返回新页面的 URL，失败返回错误信息。
    """
    _, default_db_id = load_env_vars()
    db_id = database_id or default_db_id
    if not db_id:
        return "Error: No database_id provided."

    # 1. 实时获取数据库最新架构 (核心优化：确保每次操作前同步最新列名)
    status_db, db_meta = notion_request("GET", f"databases/{db_id}")
    if status_db != 200:
        return f"Error fetching database metadata: {json.dumps(db_meta)}"
    
    db_props_meta = db_meta.get("properties", {})
    
    # 2. 归一化输入属性 (透传实时获取的 db_props_meta)
    normalized_input = normalize_properties(db_id, properties or {}, db_props=db_props_meta)
    
    # 3. 构造最终属性 payload
    payload_props = {}
    
    # 寻找标题属性名称
    title_prop_name = next((name for name, spec in db_props_meta.items() if spec.get("type") == "title"), "Name")
    
    # 处理标题：优先从归一化属性中提取，其次使用 title 参数
    if title_prop_name in normalized_input:
        payload_props[title_prop_name] = normalized_input.pop(title_prop_name)
    elif title:
        payload_props[title_prop_name] = {"title": [{"text": {"content": title}}]}
    
    # 处理正文 (Content)：优先寻找名字匹配的属性，其次作为正文 Block
    content_placed_in_prop = False
    if content:
        # 定义内容属性可能的候选名 (根据属性名来放内容)
        content_keywords = ["内容", "正文", "描述", "备注", "summary", "content", "description", "note", "detail"]
        
        # 1. 尝试在数据库中寻找匹配这些关键词的 rich_text 属性
        target_content_prop = next((name for name, spec in db_props_meta.items() 
                                   if spec.get("type") == "rich_text" and 
                                   any(kw in name.lower() or kw in "".join(pypinyin.lazy_pinyin(name.lower())) for kw in content_keywords)), None)
        
        if target_content_prop and target_content_prop not in normalized_input:
            payload_props[target_content_prop] = {"rich_text": [{"text": {"content": content}}]}
            content_placed_in_prop = True

    # 4. 自动填充辅助属性 (如果数据库支持且未手动提供)
    
    # 记录时间 (智能寻找日期属性)
    date_prop = next((name for name, spec in db_props_meta.items() if spec.get("type") == "date"), None)
    if date_prop and date_prop not in payload_props and date_prop not in normalized_input:
        payload_props[date_prop] = {"date": {"start": get_now_str()}}
    
    # 智能预测工作类型 (如果未手动提供)
    select_props = [name for name, spec in db_props_meta.items() if spec.get("type") == "select"]
    work_type_prop = next((name for name in select_props if any(kw in name.lower() or kw in "".join(pypinyin.lazy_pinyin(name.lower())) for kw in ["type", "类型"])), None)
    
    if work_type_prop and work_type_prop not in normalized_input:
        predicted = infer_work_type(title, content, db_props_meta)
        if predicted:
            payload_props[work_type_prop] = {"select": {"name": predicted}}
    
    # 5. 合并剩余属性
    payload_props.update(normalized_input)
    
    # 最终检查：移除任何可能导致 Notion 报错的空值或不规范键
    final_props = {k: v for k, v in payload_props.items() if k in db_props_meta}
    
    # 确保标题存在 (兜底)
    if title_prop_name not in final_props:
        if title:
            final_props[title_prop_name] = {"title": [{"text": {"content": title}}]}
        elif properties:
             first_val = list(properties.values())[0]
             final_props[title_prop_name] = {"title": [{"text": {"content": str(first_val)}}]}
        else:
             return f"Error: Title property ('{title_prop_name}') is mandatory."

    payload = {
        "parent": {"database_id": db_id},
        "properties": final_props
    }

    # 如果 content 没有被放入属性，则作为正文 Block 插入
    if content and not content_placed_in_prop:
        payload["children"] = [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": content}}]
                }
            }
        ]
    
    status, created = notion_request("POST", "pages", body=payload)
    if status not in (200, 201):
        return f"Error: {json.dumps(created, indent=2, ensure_ascii=False)}"
    
    return f"Page created successfully with content: {created.get('url')}"

@mcp.tool()
def get_page_info(page_id: str) -> str:
    """
    功能: 获取 Notion 页面的所有属性值和元数据。
    
    入参:
        - page_id (str, 必填): 页面 ID。
    
    参数结构: UUID 字符串，例如 "your_page_id_here"。
    
    返回: 页面完整详情的 JSON 字符串。
    """
    status, page = notion_request("GET", f"pages/{page_id}")
    if status != 200:
        return f"Error: {json.dumps(page, indent=2, ensure_ascii=False)}"
    return json.dumps(page, indent=2, ensure_ascii=False)

@mcp.tool()
def update_notion_page(page_id: str, properties: dict) -> str:
    """
    功能: 修改现有页面的属性值。
    
    入参:
        - page_id (str, 必填): 页面 ID。
        - properties (dict, 必填): 要更新的属性。支持拼音名和简单值。
    
    参数结构:
        - page_id: "your_page_id_here"
        - properties: {"zhuang_tai": "已完成", "Priority": "High"}
    
    返回: 更新成功后的页面 URL。
    """
    # 获取页面所属的数据库 ID 及其最新架构
    status_page, page_info = notion_request("GET", f"pages/{page_id}")
    if status_page != 200:
        return f"Error fetching page: {json.dumps(page_info)}"
    
    db_id = page_info.get("parent", {}).get("database_id")
    if not db_id:
        # 如果不是数据库页面，直接使用原始属性
        normalized_props = properties
    else:
        # 实时获取数据库最新架构
        status_db, db_meta = notion_request("GET", f"databases/{db_id}")
        db_props = db_meta.get("properties", {}) if status_db == 200 else None
        normalized_props = normalize_properties(db_id, properties, db_props=db_props)

    payload = {"properties": normalized_props}
    status, updated = notion_request("PATCH", f"pages/{page_id}", body=payload)
    if status not in (200, 201):
        return f"Error: {json.dumps(updated, indent=2, ensure_ascii=False)}"
    
    return f"Page updated successfully: {updated.get('url')}"

@mcp.tool()
def append_page_content(page_id: str, content: str) -> str:
    """
    功能: 向页面内容末尾追加文本段落。
    
    入参:
        - page_id (str, 必填): 页面 ID。
        - content (str, 必填): 要追加的文本字符串。
    
    参数结构:
        - page_id: "your_page_id_here"
        - content: "这是追加的内容。"
    
    返回: 成功或失败的确认消息。
    """
    payload = {
        "children": [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": content}}]
                }
            }
        ]
    }
    status, result = notion_request("PATCH", f"blocks/{page_id}/children", body=payload)
    if status != 200:
        return f"Error: {json.dumps(result, indent=2, ensure_ascii=False)}"
    
    return "Content appended to page successfully."

@mcp.tool()
def update_database_properties(database_id: str = None, properties: dict = None) -> str:
    """
    功能: 修改数据库的架构，包括添加、重命名或删除列。
    
    入参:
        - database_id (str, 可选): 数据库 ID。
        - properties (dict, 必填): 描述属性变更的字典。
    
    参数结构:
        - properties: {"新列名": {"rich_text": {}}, "旧列名": null}
          (值为 null 时表示删除该列)
    
    返回: 成功后的数据库属性列表。
    """
    _, default_db_id = load_env_vars()
    db_id = database_id or default_db_id
    if not db_id:
        return "Error: No database_id provided."

    if not properties:
        return "Error: No property changes provided."

    status, result = notion_request("PATCH", f"databases/{db_id}", body={"properties": properties})
    if status != 200:
        return f"Error: {json.dumps(result, indent=2, ensure_ascii=False)}"
    
    return f"Database schema updated successfully. Current properties: {list(result.get('properties', {}).keys())}"

@mcp.tool()
def upgrade_database_schema(database_id: str = None) -> str:
    """
    功能: 一键升级数据库架构，添加标准的“工作类型”和“状态”选择字段。
    
    入参:
        - database_id (str, 可选): 数据库 ID。
    
    返回: 确认升级成功的消息。
    """
    _, default_db_id = load_env_vars()
    db_id = database_id or default_db_id
    if not db_id:
        return "Error: No database_id provided."

    properties = {
        "工作类型": {
            "select": {
                "options": [
                    {"name": "📱 小程序端", "color": "blue"},
                    {"name": "💻 vue后台web端", "color": "green"},
                    {"name": "🔌 fastAPI后台接口端", "color": "purple"},
                    {"name": "📝 日常记录", "color": "gray"}
                ]
            }
        },
        "状态": {
            "select": {
                "options": [
                    {"name": "未开始", "color": "gray"},
                    {"name": "进行中", "color": "blue"},
                    {"name": "已完成", "color": "green"}
                ]
            }
        }
    }

    status, result = notion_request("PATCH", f"databases/{db_id}", body={"properties": properties})
    if status != 200:
        return f"Error: {json.dumps(result, indent=2, ensure_ascii=False)}"
    
    return "Database schema upgraded with '工作类型' and '状态' properties."

if __name__ == "__main__":
    mcp.run()
