# Notion API 2025‑09‑03 Demo (Multi‑Data‑Source Database)

This project provides a Python script example that demonstrates how to use the latest Notion API 2025‑09‑03 version to work with a multi‑data‑source database: discover data sources, create pages with a data source as the parent, and write text to the Work Content field. It also supports updating specific fields on existing pages.

## Quick Start
- Requirements
  - Python 3.8+ (no third‑party dependencies)
- Obtain the token
  - Create a Notion integration and share the database with that integration
  - Copy the integration token and set it as an environment variable or write it into `.env`
- Configure `.env`
  - Create a `.env` file in the project root (or edit it if it already exists):

    ```
    NOTION_TOKEN=your integration token
    # Optional: default database ID (can also be provided at runtime via --database-id)
    # DATABASE_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    ```

- Run
  - Show help:

    ```bash
    python d:\whj\notionMCP\notion_demo.py --help
    ```

  - Create a page and write Work Content:

    ```bash
    python d:\whj\notionMCP\notion_demo.py --database-id <database_id> --title "Test Page" --work-content "Work content added via API"
    ```

  - Update the Work Content of an existing page:

    ```bash
    python d:\whj\notionMCP\notion_demo.py --page-id <page_id> --work-content "Text to add"
    ```

## Parameters
- `--database-id` Target database ID (copyable from the Notion app)
- `--title` Title text for the new page (default: API Demo Page)
- `--work-content` Text written to the Work Content property (default: Work content added via API)
- `--page-id` If provided, update the specified page instead of creating a new one
- `--work-prop` Work Content property name (default: Work Content; property type must be rich_text)
- `--title-prop` Title property name (usually auto‑detected; explicit override if needed)
- `--print-db` Print basic database information (per the 2025‑09‑03 response)
- `--version` Notion-Version request header (default: 2025‑09‑03)

## How It Works
- Multi‑data‑source database
  - The 2025‑09‑03 version introduces the `data_sources` concept; a database can contain multiple data sources
  - For creating pages and establishing relations, use `data_source_id` as the parent or target
- Data source discovery
  - Use `GET /v1/databases/{database_id}` (Notion-Version: 2025‑09‑03) to fetch the `data_sources` list
  - The script selects the first data source as the parent by default
- Compatible property discovery
  - For compatibility with existing property structures, the script reads `properties` under the older version (2022‑06‑28) and auto‑detects the title property name (for example, if your database title is “Date”)
- Writing Work Content
  - Treat `Work Content` as a rich_text property and write the provided text; if the property name differs, specify it via `--work-prop`

## FAQ
- “Name is not a property that exists.”
  - The database title property may not be called “Name”. The script auto‑detects it; if auto‑detection fails, specify it explicitly via `--title-prop` (e.g., Date, Name)
- Property type mismatch
  - `Work Content` must be of rich_text type. If it is another type (e.g., multi_select), adjust `--work-prop` and modify the write format accordingly
- Permissions and token
  - Ensure the database is shared with your integration and the token is valid with sufficient permissions
- Multiple data sources
  - If the database contains multiple data sources, the script currently uses the first; you can extend it to filter by data source name

## Security Tips
- Do not commit `.env` to the repository; keep your token locally
- If the token leaks, revoke it immediately in the Notion console and rotate it

## Code Location
- Main script: [notion_demo.py](file:///d:/whj/notionMCP/notion_demo.py)

## References
- Upgrade guide: <https://developers.notion.com/docs/upgrade-guide-2025-09-03>
- API introduction: <https://developers.notion.com/reference/intro>
