import os
import sys
import uvicorn

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.getcwd()))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 