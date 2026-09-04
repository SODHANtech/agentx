import logging
import sys
from typing import Dict, Any, List

try:
    from google.antigravity import StdioMCPServerConfig
except ImportError:
    class StdioMCPServerConfig:
        def __init__(self, command: str, args: List[str], name: str):
            self.command = command
            self.args = args
            self.name = name

logger = logging.getLogger(__name__)


class MCPServerMatrix:
    """Configures and mounts System, Web, and Device Model Context Protocol (MCP) servers."""

    @staticmethod
    def get_system_mcp_config() -> StdioMCPServerConfig:
        """Configures System MCP server for filesystem and sandboxed shell actions."""
        return StdioMCPServerConfig(
            command=sys.executable,
            args=["-m", "personalai.mcp_hub.system_server"],
            name="system_mcp",
        )

    @staticmethod
    def get_web_mcp_config() -> StdioMCPServerConfig:
        """Configures Web MCP server for local Playwright/Puppeteer browser control."""
        return StdioMCPServerConfig(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-puppeteer"],
            name="web_mcp",
        )

    @staticmethod
    def get_device_mcp_config() -> StdioMCPServerConfig:
        """Configures Device MCP server for cross-platform Android control routing."""
        return StdioMCPServerConfig(
            command=sys.executable,
            args=["-m", "personalai.mcp_hub.device_server"],
            name="device_mcp",
        )

    @classmethod
    def get_all_mcp_servers(cls) -> List[StdioMCPServerConfig]:
        """Returns mounted MCP server configs list."""
        return [
            cls.get_system_mcp_config(),
            cls.get_device_mcp_config(),
        ]
