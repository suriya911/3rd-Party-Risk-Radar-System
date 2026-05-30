"""
Entry point: starts the FastAPI backend on port 8000.
Run with: python run.py

For the MCP server: python -m backend.mcp_server.server
For the frontend:   cd frontend && npm install && npm run dev
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
