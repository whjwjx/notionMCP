import os
import json
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import requests
from datetime import datetime, timedelta, timezone
from mcp.server.fastmcp import FastMCP
import pypinyin
# Initialize MCP
mcp = FastMCP("Notion MCP Server")

API_BASE = "https://api.notion.com/v1/"
# Default to the most stable version for property operations
DEFAULT_NOTION_VERSION = "2022-06-28"

def get_now_str():
    """Get current time in ISO 8601 format for Notion date property."""
    return datetime.now().strftime("%Y-%m-%d")

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

def normalize_properties(db_id, input_props):
    """
    智能属性转换：
    1. 将拼音或不完全匹配的属性名映射到数据库实际属性名。
    2. 将简单的字符串值包装成 Notion 要求的复杂 JSON 结构。
    """
    if not input_props:
        return {}
    
    status, db = notion_request("GET", f"databases/{db_id}")
    if status != 200:
        return input_props # 失败则原样返回
    
    db_props = db.get("properties", {})
    normalized = {}
    
    # 建立拼音到实际名称的映射
    def get_pinyin(text):
        return "".join(pypinyin.lazy_pinyin(text, style=pypinyin.Style.NORMAL)).lower()
    
    py_map = {get_pinyin(name): name for name in db_props.keys()}
    
    for key, value in input_props.items():
        # 1. 尝试直接匹配或拼音匹配属性名
        target_key = None
        if key in db_props:
            target_key = key
        else:
            py_key = key.lower().replace("_", "")
            if py_key in py_map:
                target_key = py_map[py_key]
        
        if not target_key:
            normalized[key] = value # 没找到匹配，原样保留
            continue
            
        # 2. 检查值是否需要包装
        prop_type = db_props[target_key].get("type")
        
        # 如果值已经是字典且包含类型键，说明已经是 Notion 格式
        if isinstance(value, dict) and (prop_type in value or "type" in value):
            normalized[target_key] = value
            continue
            
        # 根据类型包装简单值
        if prop_type == "select":
            # 支持传入字符串作为选项名
            if isinstance(value, str):
                normalized[target_key] = {"select": {"name": value}}
            else:
                normalized[target_key] = value
        elif prop_type == "multi_select":
            if isinstance(value, list):
                normalized[target_key] = {"multi_select": [{"name": v} for v in value]}
            elif isinstance(value, str):
                normalized[target_key] = {"multi_select": [{"name": value}]}
            else:
                normalized[target_key] = value
        elif prop_type == "rich_text":
            if isinstance(value, str):
                normalized[target_key] = {"rich_text": [{"text": {"content": value}}]}
            else:
                normalized[target_key] = value
        elif prop_type == "date":
            if isinstance(value, str):
                normalized[target_key] = {"date": {"start": value}}
            else:
                normalized[target_key] = value
        elif prop_type == "status":
            if isinstance(value, str):
                normalized[target_key] = {"status": {"name": value}}
            else:
                normalized[target_key] = value
        else:
            normalized[target_key] = value
            
    return normalized

def infer_work_type(title, content, db_props):
    """
    根据标题和正文内容智能预测“工作类型”。
    """
    text = (title + (content or "")).lower()
    
    # 定义关键字映射
    mapping = {
        "📱 小程序端": ["小程序", "miniprogram", "weixin", "微信"],
        "💻 vue后台web端": ["vue", "web", "前端", "css", "html", "js", "ts", "页面", "组件", "侧边栏"],
        "🔌 fastAPI后台接口端": ["fastapi", "api", "接口", "后端", "python", "数据库", "db", "server", "服务端"],
        "📝 日常记录": ["日常", "记录", "测试", "总结", "笔记", "mcp"]
    }
    
    # 检查数据库中实际存在的选项名（防止带 emoji 的名称不匹配）
    work_type_prop = db_props.get("工作类型", {})
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
            
    return best_match or next((o for o in options if "日常" in o), options[0] if options else None)

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

    title_prop = find_title_property_name(db_id)
    
    payload_props = {
        title_prop: {"title": [{"text": {"content": title}}]}
    }

    # 自动设置记录时间 (北京时间 UTC+8)
    tz_beijing = timezone(timedelta(hours=8))
    now_iso = datetime.now(tz_beijing).isoformat()
    # 检查数据库中是否存在“记录时间”属性
    status_check, db_info = notion_request("GET", f"databases/{db_id}")
    if status_check == 200:
        db_props = db_info.get("properties", {})
        if "记录时间" in db_props:
            payload_props["记录时间"] = {"date": {"start": now_iso}}
        
        # 智能预测工作类型
        if properties:
            # 如果用户没传 工作类型 或 其拼音形式，则进行预测
            has_work_type = any(k in properties for k in ["工作类型", "gong_zuo_lei_xing", "zuo_pin_lei_xing"])
            if not has_work_type:
                predicted = infer_work_type(title, content, db_props)
                if predicted:
                    payload_props["工作类型"] = {"select": {"name": predicted}}
        else:
            # 完全没传 properties
            predicted = infer_work_type(title, content, db_props)
            if predicted:
                payload_props["工作类型"] = {"select": {"name": predicted}}
    
    if properties:
        # 使用智能归一化处理属性
        normalized_props = normalize_properties(db_id, properties)
        payload_props.update(normalized_props)
    
    payload = {
        "parent": {"database_id": db_id},
        "properties": payload_props
    }

    if content:
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
    # 获取页面所属的数据库 ID
    status_page, page_info = notion_request("GET", f"pages/{page_id}")
    if status_page != 200:
        return f"Error fetching page: {json.dumps(page_info)}"
    
    db_id = page_info.get("parent", {}).get("database_id")
    if not db_id:
        # 如果不是数据库页面，直接使用原始属性
        normalized_props = properties
    else:
        normalized_props = normalize_properties(db_id, properties)

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
    import asyncio
    import nest_asyncio
    
    # 仅在作为脚本直接运行时应用补丁
    nest_asyncio.apply()
    
    # 检查是否已在异步循环中
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # 如果已经在运行循环中（如云端环境），则不重复启动
        print("检测到正在运行的事件循环，跳过 mcp.run()，由平台接管", file=sys.stderr)
    else:
        # 只有在没有运行循环时（如本地直接运行）才启动
        try:
            token, db_id = load_env_vars()
            print("=" * 50, file=sys.stderr)
            print("🚀 fastNotion MCP Server 正在启动...", file=sys.stderr)
            print(f"📡 Notion Token: {mask_id(token)}", file=sys.stderr)
            print(f"📊 默认数据库: {mask_id(db_id)}", file=sys.stderr)
            print("✅ 服务已就绪，正在监听 MCP 请求 (stdio 模式)", file=sys.stderr)
            print("=" * 50, file=sys.stderr)
            # 本地运行使用默认的 stdio
            mcp.run()
        except RuntimeError as e:
            if "Already running asyncio" in str(e):
                pass
            else:
                raise e
