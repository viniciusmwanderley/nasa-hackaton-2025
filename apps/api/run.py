# ABOUTME: Development server runner using uv for modern Python tooling
# ABOUTME: Simple wrapper to start FastAPI server with uv run

if __name__ == "__main__":
    from app.main import run_dev_server
    run_dev_server()