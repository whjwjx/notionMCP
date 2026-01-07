import os
import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from fastmcp import FastMCP

# Initialize MCP
mcp = FastMCP("fastNotion MCP Server")

API_BASE = "https://api.notion.com/v1/"
NOTION_VERSION = "2025-09-03"

def get_token():
    """Retrieve Notion token from environment variables."""
    token = os.environ.get("NOTION_TOKEN")
    if not token:
        # Try reading from .env using absolute path
        base_dir = os.path.dirname(os.path.abspath(__file__))
        env_path = os.path.join(base_dir, ".env")
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("NOTION_TOKEN="):
                        return line.split("=", 1)[1].strip().strip('"').strip("'")
    return token

def get_default_database_id():
    """Retrieve default database ID from environment variables."""
    db_id = os.environ.get("DATABASE_ID")
    if not db_id:
        # Try reading from .env using absolute path
        base_dir = os.path.dirname(os.path.abspath(__file__))
        env_path = os.path.join(base_dir, ".env")
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("DATABASE_ID="):
                        return line.split("=", 1)[1].strip().strip('"').strip("'")
    return db_id

def notion_request(method, path, body=None, version=NOTION_VERSION):
    token = get_token()
    if not token:
        return 0, {"error": "Missing NOTION_TOKEN"}
    
    url = API_BASE + path
    # print(f"DEBUG: Requesting {method} {url}") # Helpful for debugging
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

def get_database_properties(database_id, version="2022-06-28"):
    status, db = notion_request("GET", f"databases/{database_id}", version=version)
    if status != 200:
        return status, {}
    return 200, db.get("properties", {})

def find_title_property_name(database_id):
    # Use older version to get properties structure
    p_status, props = get_database_properties(database_id, version="2022-06-28")
    if p_status == 200 and props:
        for name, spec in props.items():
            if spec.get("type") == "title":
                return name
        if "Name" in props:
            return "Name"
    return "Name"

@mcp.tool
def get_database_info(database_id: str = None) -> str:
    """
    Fetch details of a Notion database.
    
    Args:
        database_id: The ID of the Notion database. If not provided, uses the default ID from configuration.
    """
    if not database_id:
        database_id = get_default_database_id()
    if not database_id:
        return "Error: No database_id provided and no default DATABASE_ID found in environment."

    status, db = notion_request("GET", f"databases/{database_id}")
    if status != 200:
        return f"Error fetching database: {json.dumps(db, indent=2)}"
    return json.dumps(db, indent=2, ensure_ascii=False)

@mcp.tool
def query_database(database_id: str = None, filter_params: dict = None) -> str:
    """
    Query pages in a Notion database.
    
    Args:
        database_id: The ID of the Notion database. If not provided, uses the default ID from configuration.
        filter_params: Optional filter conditions (Notion API filter object).
    """
    if not database_id:
        database_id = get_default_database_id()
    if not database_id:
        return "Error: No database_id provided and no default DATABASE_ID found in environment."

    # Clean database_id (remove potential spaces or brackets)
    database_id = database_id.strip().strip("<>").replace("-", "")
    
    body = {}
    if filter_params:
        body["filter"] = filter_params
        
    status, results = notion_request("POST", f"databases/{database_id}/query", body=body, version="2022-06-28")
    if status != 200:
        return f"Error querying database (Status {status}): {json.dumps(results, indent=2, ensure_ascii=False)}"
    return json.dumps(results, indent=2, ensure_ascii=False)

@mcp.tool
def create_notion_page(database_id: str = None, title: str = "", content: str = "", work_prop: str = "Work Content") -> str:
    """
    Create a new page in a Notion database.
    
    Args:
        database_id: The ID of the target Notion database. If not provided, uses the default ID from configuration.
        title: The title of the new page.
        content: The text content to put in the 'Work Content' (or specified) property.
        work_prop: The name of the property to store the content (default: 'Work Content').
    """
    if not database_id:
        database_id = get_default_database_id()
    if not database_id:
        return "Error: No database_id provided and no default DATABASE_ID found in environment."

    # 1. Find title property name
    title_prop = find_title_property_name(database_id)
    
    # 2. Construct payload (Standard database parent)
    payload = {
        "parent": {
            "database_id": database_id
        },
        "properties": {
            title_prop: {
                "title": [{"type": "text", "text": {"content": title}}]
            },
            work_prop: {
                "rich_text": [{"type": "text", "text": {"content": content}}]
            }
        }
    }
    
    status, created = notion_request("POST", "pages", body=payload)
    if status not in (200, 201):
        return f"Error creating page: {json.dumps(created, indent=2)}"
    
    return f"Page created successfully: {created.get('url')}"

@mcp.tool
def update_notion_page(page_id: str, content: str, work_prop: str = "Work Content") -> str:
    """
    Update the content of an existing Notion page.
    
    Args:
        page_id: The ID of the Notion page to update.
        content: The new text content for the specified property.
        work_prop: The name of the property to update (default: 'Work Content').
    """
    payload = {
        "properties": {
            work_prop: {
                "rich_text": [{"type": "text", "text": {"content": content}}]
            }
        }
    }
    
    status, updated = notion_request("PATCH", f"pages/{page_id}", body=payload)
    if status not in (200, 201):
        return f"Error updating page: {json.dumps(updated, indent=2)}"
    
    return f"Page updated successfully: {updated.get('url')}"

if __name__ == "__main__":
    mcp.run()
