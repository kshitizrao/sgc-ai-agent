# MCP Server Setup Guide

This guide explains how to set up and configure a Model Context Protocol (MCP) server for your `sgc-ai-agent`. The Model Context Protocol enables you to securely connect your AI agent with external data sources and custom tools.

## What is MCP?

The Model Context Protocol (MCP) is an open standard that creates a two-way integration between AI models and their environment. By setting up an MCP server, you can give your AI agent access to:
- Custom local tools and scripts.
- Secure databases or file systems.
- Remote services and APIs.

## Configuration

The AI agent expects MCP server configurations to be defined in an `mcp_config.json` file. You can typically place this file in your project configuration directory or global settings, depending on the agent's specific loader.

### Example `mcp_config.json`

Create a file named `mcp_config.json` in your configuration directory:

```json
{
  "mcpServers": {
    "my-local-tool": {
      "command": "python",
      "args": ["/absolute/path/to/my_tool.py"],
      "env": {
        "MY_ENV_VAR": "value"
      }
    },
    "my-remote-service": {
      "serverUrl": "http://ec2-13-126-138-33.ap-south-1.compute.amazonaws.com:8000/mcp/sse"
    }
  }
}
```

## Transport Types

The protocol supports two primary transport mechanisms:

### 1. Stdio (Local Command-line Tools)
Use Stdio to run a local executable or script. The agent will spawn this process and communicate via standard input/output.

- **`command`**: The executable to run (e.g., `python`, `node`, or a binary path).
- **`args`**: Array of arguments to pass to the command.
- **`env`**: (Optional) Environment variables required by the script.

### 2. SSE (Remote Server-Sent Events)
Use SSE for connecting to remote services over HTTP/HTTPS.

- **`serverUrl`**: The HTTP(S) endpoint of the remote MCP server.

## Running the Agent with MCP

Once your `mcp_config.json` is configured:

1. Ensure any local dependencies required by your MCP servers (such as python packages or Node modules) are installed.
2. Start the AI agent as usual. The agent will automatically read the `mcp_config.json`.
3. The agent will query the MCP servers to discover the available tools and inject them into its context.
4. You can verify the tools are active by asking the agent what tools it has available.

## Troubleshooting

- **Server Not Starting:** If a local stdio server fails to start, verify the `command` and `args` paths are absolute and that the executable has appropriate permissions.
- **Missing Tools:** If tools are not showing up, check the agent's logs for connection errors or timeouts when querying the MCP server.
