# mcp_tester_client.py
import asyncio
from fastmcp import Client


HEADERS = {
    # "X-MCP-Api-Key": "lovethisapp",   
}

async def main():

    client = Client("http://localhost:8765/mcp/")

    # context manager auto-connects and closes
    async with client:
        # optional: sanity ping
        await client.ping()

        tools = await client.list_tools()
        resources = await client.list_resource_templates()
        prompts = await client.list_prompts()

        print("TOOLS:", [t.name for t in tools])
        print("RESOURCES:", resources)
        print("PROMPTS:", prompts)

        # Example: call a tool
        resp = await client.call_tool(
                "spend_summary",
                {
                    "input": {
                        "customerId": 1,
                        "from": "2025-07-11T01:31:31",
                        "to":   "2025-08-10T01:31:31",
                        "fxBase": "USD"
                    },
                    "headers": {"x-mcp-api-key": "lovethisapp"} 
                }
            )
        print("spend_summary ->", resp)



        # Example: read a resource
        res = await client.read_resource("resource://customers/1")
        print("resource customers/1 ->", res)

if __name__ == "__main__":
    asyncio.run(main())