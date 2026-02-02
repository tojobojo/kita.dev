import uvicorn
import os

if __name__ == "__main__":
    # Check for API Key warning
    if not os.environ.get("OPENAI_API_KEY") and not os.environ.get("ANTHROPIC_API_KEY"):
        print("WARNING: No LLM API Keys found. Agent will likely fail or use Mock.")
        
    print("Starting Kita.dev Agent Service...")
    uvicorn.run("api.app:app", host="0.0.0.0", port=8000, reload=True)
