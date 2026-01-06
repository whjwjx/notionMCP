import os
import sys
import json
import argparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


API_BASE = "https://api.notion.com/v1/"


def read_env_file(path=".env"):
    values = {}
    if not os.path.exists(path):
        return values
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    values[k.strip()] = v.strip().strip('"').strip("'")
    except Exception:
        pass
    return values


def get_env(name, default=None):
    v = os.environ.get(name)
    if v:
        return v
    file_vals = read_env_file()
    return file_vals.get(name, default)


def notion_request(method, path, token, version="2025-09-03", body=None):
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


def get_database_properties(database_id, token, version="2022-06-28"):
    status, db = notion_request("GET", f"databases/{database_id}", token, version=version)
    if status != 200:
        return status, {}
    return 200, db.get("properties", {})


def find_title_property_name(database_obj):
    props = database_obj.get("properties", {})
    if isinstance(props, dict):
        for name, spec in props.items():
            t = spec.get("type")
            if t == "title" or ("title" in spec and isinstance(spec.get("title"), dict)):
                return name
        if "Name" in props:
            return "Name"
        if props:
            return next(iter(props.keys()))
        return "Name"
    if isinstance(props, list):
        for spec in props:
            name = spec.get("name")
            t = spec.get("type")
            if t == "title" and name:
                return name
        for spec in props:
            if spec.get("name") == "Name":
                return "Name"
        if props:
            return props[0].get("name", "Name")
        return "Name"
    return "Name"


def create_page_payload(data_source_id, title_prop, title_text):
    return {
        "parent": {
            "type": "data_source_id",
            "data_source_id": data_source_id,
        },
        "properties": {
            title_prop: {
                "title": [
                    {
                        "type": "text",
                        "text": {"content": title_text},
                    }
                ]
            }
        },
    }


def main():
    parser = argparse.ArgumentParser(
        prog="notion_demo",
        description="Notion API 2025-09-03 demo: data_sources discovery and page creation",
    )
    parser.add_argument("--database-id", dest="database_id", help="Target Notion database ID")
    parser.add_argument("--title", dest="title", default="API Demo Page", help="Page title for creation")
    parser.add_argument("--version", dest="version", default="2025-09-03", help="Notion-Version header")
    parser.add_argument("--print-db", dest="print_db", action="store_true", help="Print database JSON after fetch")
    parser.add_argument("--page-id", dest="page_id", help="Update an existing page's Work Content")
    parser.add_argument("--work-content", dest="work_content", default="Work content added via API", help="Text content written to the Work Content field")
    parser.add_argument("--title-prop", dest="title_prop", help="Explicitly specify the title property name; auto-detected by default")
    parser.add_argument("--work-prop", dest="work_prop", default="Work Content", help="Work Content property name (rich_text)")
    args = parser.parse_args()

    token = get_env("NOTION_TOKEN")
    if not token:
        print("Missing NOTION_TOKEN. Set it in environment variables or in the .env file.", file=sys.stderr)
        sys.exit(2)

    database_id = args.database_id or get_env("DATABASE_ID")
    if not database_id:
        print("Missing database ID. Pass via --database-id or set DATABASE_ID in .env.", file=sys.stderr)
        sys.exit(2)

    status, db = notion_request("GET", f"databases/{database_id}", token, version=args.version)
    if status != 200:
        print(f"Failed to fetch database: HTTP {status}", file=sys.stderr)
        print(json.dumps(db, ensure_ascii=False, indent=2))
        sys.exit(1)

    if args.print_db:
        print(json.dumps(db, ensure_ascii=False, indent=2))

    data_sources = db.get("data_sources", [])
    if not data_sources:
        print("No available data sources in this database.", file=sys.stderr)
        print(json.dumps({"database_id": database_id, "title": db.get("title", [])}, ensure_ascii=False, indent=2))
        sys.exit(1)

    selected = data_sources[0]
    title_prop = args.title_prop
    if not title_prop:
        # Fallback to the old version to read the property schema and determine the title property name
        p_status, props = get_database_properties(database_id, token, version="2022-06-28")
        if p_status == 200 and props:
            for name, spec in props.items():
                if spec.get("type") == "title":
                    title_prop = name
                    break
            if not title_prop and "Name" in props:
                title_prop = "Name"
        if not title_prop:
            title_prop = find_title_property_name({"properties": props})

    work_prop = args.work_prop

    if args.page_id:
        update_body = {
            "properties": {
                work_prop: {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": args.work_content},
                        }
                    ]
                }
            }
        }
        status, updated = notion_request("PATCH", f"pages/{args.page_id}", token, version=args.version, body=update_body)
        if status not in (200, 201):
            print(f"Failed to update page: HTTP {status}", file=sys.stderr)
            print(json.dumps(updated, ensure_ascii=False, indent=2))
            sys.exit(1)
        output = {
            "updated_page_id": updated.get("id"),
            "url": updated.get("url"),
            "updated_property": work_prop,
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return
    else:
        payload = create_page_payload(selected["id"], title_prop, args.title)
        # Merge Work Content property
        payload["properties"][work_prop] = {
            "rich_text": [
                {
                    "type": "text",
                    "text": {"content": args.work_content},
                }
            ]
        }
        status, created = notion_request("POST", "pages", token, version=args.version, body=payload)
        if status not in (200, 201):
            print(f"Failed to create page: HTTP {status}", file=sys.stderr)
            print(json.dumps(created, ensure_ascii=False, indent=2))
            sys.exit(1)

        output = {
            "database_id": database_id,
            "data_source": selected,
            "created_page_id": created.get("id"),
            "created_page_url": created.get("url"),
            "title_property": title_prop,
            "work_property": work_prop,
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
