import uvicorn
import os

if __name__ == "__main__":
    try:
        print("🚀 Starting server...")
        uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)
    except Exception as e:
        print(f"❌ Server startup failed: {e}")
