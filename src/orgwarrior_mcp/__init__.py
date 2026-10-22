"""The org agenda for Claude: an MCP server over orgwarrior's engine."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("orgwarrior-mcp")
except PackageNotFoundError:
    __version__ = "0"
