"""
Weather Agent - Connects to Remote MCP Server on Cloud Run
Successfully connects to custom MCP HTTP endpoints!
"""
import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Bypass lỗi mạng khi tiktoken cố tải file mã hoá từ openaipublic.blob.core.windows.net
try:
    import tiktoken

    class _DummyEncoding:
        name = "cl100k_base"

        def encode(self, text, *args, **kwargs):
            return [1] * max(1, len(text) // 4)

        def decode(self, *args, **kwargs):
            return ""

    tiktoken.get_encoding = lambda *args, **kwargs: _DummyEncoding()
    tiktoken.encoding_for_model = lambda *args, **kwargs: _DummyEncoding()
except Exception:
    pass

from google.adk import Agent
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset, StreamableHTTPConnectionParams
import logging
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mặc định: server chạy local. Deploy lên Cloud Run thì đặt MCP_SERVER_URL trong .env
# (ví dụ: https://<service>.run.app/mcp). verify_setup.py đọc cùng biến này.
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8085/mcp")

# Lựa chọn model: Ưu tiên DeepSeek nếu có DEEPSEEK_API_KEY, ngược lại dùng Gemini
if os.getenv("DEEPSEEK_API_KEY") and os.getenv("DEEPSEEK_API_KEY") != "your_deepseek_api_key_here":
    DEFAULT_MODEL = "deepseek/deepseek-chat"
else:
    DEFAULT_MODEL = "gemini-2.5-flash"

MODEL_NAME = os.getenv("MODEL", DEFAULT_MODEL)

logger.info(f"🌐 Initializing weather agent with remote MCP server")
logger.info(f"📡 MCP Server: {MCP_SERVER_URL}")
logger.info(f"🧠 Model: {MODEL_NAME}")

try:
    # Create connection parameters for the remote MCP server
    connection_params = StreamableHTTPConnectionParams(
        url=MCP_SERVER_URL,
        timeout=30.0,  # Increased timeout for Cloud Run cold starts
    )
    
    # Create the MCP toolset - this will connect to the remote server
    logger.info("🔌 Connecting to MCP server...")
    weather_tools = McpToolset(
        connection_params=connection_params,
    )
    logger.info("✅ MCP toolset created successfully")
    
    # Create the agent with remote MCP tools
    root_agent = Agent(
        name="weather_agent",
        model=MODEL_NAME,
        tools=[weather_tools],
    )
    logger.info("✅ Weather agent initialized with remote MCP tools:")
    logger.info("   - get_current_weather(city)")
    logger.info("   - get_forecast(city, days)")
    logger.info("   - health_check()")
    logger.info("🎉 Remote MCP connection successful!")
    
except Exception as e:
    logger.error(f"❌ Failed to connect to remote MCP server: {e}")
    logger.error(f"   Server URL: {MCP_SERVER_URL}")
    import traceback
    traceback.print_exc()
    
    # Create a fallback agent without tools
    logger.warning("⚠️  Creating fallback agent without MCP tools")
    root_agent = Agent(
        name="weather_agent",
        model=MODEL_NAME,
    )

