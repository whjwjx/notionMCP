from fastmcp import FastMCP

mcp = FastMCP("FastMCP Demo")

@mcp.tool
def add(a: int, b: int) -> int:
    return a + b

if __name__ == "__main__":
    mcp.run()

