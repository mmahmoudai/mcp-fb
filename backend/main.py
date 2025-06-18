from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware # Add this import
from pydantic import BaseModel
import asyncio
import sys
import os

# Add the parent directory of 'automation_script' to sys.path
# This assumes backend/main.py and automation_script/ are siblings in the project structure
# Adjust this path if your project structure is different.
current_dir = os.path.dirname(__file__)
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
automation_script_dir = os.path.join(parent_dir, 'automation_script')

if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir) # Insert at the beginning to ensure it's checked first
if automation_script_dir not in sys.path: # Also add automation_script itself if needed for its internal imports
    sys.path.insert(0, automation_script_dir)


try:
    from automation_script.main import FacebookAutomator, logger as automation_logger
except ImportError as e:
    # This provides a more informative error if the import fails.
    print(f"Error importing FacebookAutomator: {e}")
    print(f"Current sys.path: {sys.path}")
    print(f"Expected location of automation_script: {automation_script_dir}")
    # Fallback for environments where the import might still fail, to allow FastAPI to start
    # and show other errors if any. This is mostly for robust startup.
    FacebookAutomator = None
    automation_logger = None
    print("FacebookAutomator could not be imported. API calls requiring it will fail.")


app = FastAPI()

# CORS Middleware
origins = [
    "http://localhost:5173", # Default Vite dev server port
    "http://localhost:3000", # Common alternative React dev server port
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods
    allow_headers=["*"], # Allows all headers
)

# Pydantic Models for Request Validation
class SearchRequest(BaseModel):
    query: str

class CommentRequest(BaseModel):
    post_url: str
    comment_text: str

@app.get("/")
async def root():
    return {"message": "Facebook Automation Backend is running"}

async def run_automation_task(task_type: str, **kwargs):
    """
    Generic helper to run FacebookAutomator tasks in a separate thread.
    task_type can be 'search' or 'comment'.
    kwargs are arguments for the specific task.
    """
    if FacebookAutomator is None:
        return {"error": "FacebookAutomator not available due to import error."}

    automator = None
    try:
        automator = FacebookAutomator() # Initializes WebDriver
        if not automator.driver: # Check if driver init failed
             return {"error": "Failed to initialize WebDriver for FacebookAutomator."}

        login_success = automator.login() # Uses env vars for credentials
        if not login_success:
            return {"error": "Facebook login failed. Check credentials or page status."}

        if task_type == "search":
            query = kwargs.get("query")
            if not query:
                return {"error": "Search query not provided."}
            results = automator.search(query)
            return results # This could be a list of posts or an error dict

        elif task_type == "comment":
            post_url = kwargs.get("post_url")
            comment_text = kwargs.get("comment_text")
            if not post_url or not comment_text:
                return {"error": "Post URL or comment text not provided."}
            success = automator.comment(post_url, comment_text)
            return {"success": success, "message": "Comment action performed." if success else "Comment action failed."}

        else:
            return {"error": "Invalid task type."}

    except Exception as e:
        # Log this exception with automation_logger if available, or backend's logger
        if automation_logger:
            automation_logger.error(f"Exception during automation task '{task_type}': {e}", exc_info=True)
        else:
            print(f"Exception during automation task '{task_type}': {e}") # Fallback print
        # Return a generic error to the client
        return {"error": f"An server-side error occurred during the '{task_type}' task: {str(e)}"}
    finally:
        if automator:
            automator.close_driver()


@app.post("/api/search")
async def api_search(request_data: SearchRequest):
    # automation_logger can be used here if needed for backend-specific logging before task run
    if automation_logger:
        automation_logger.info(f"Received API search request for query: {request_data.query}")

    results = await asyncio.to_thread(
        run_automation_task,
        task_type="search",
        query=request_data.query
    )

    if isinstance(results, dict) and "error" in results:
        # Consider different HTTP status codes based on the error
        if "login failed" in results["error"].lower() or "credentials" in results["error"].lower():
            raise HTTPException(status_code=401, detail=results["error"])
        elif "WebDriver" in results["error"]: # Covers init and other WebDriver issues
             raise HTTPException(status_code=503, detail=results["error"]) # Service Unavailable
        raise HTTPException(status_code=500, detail=results["error"])

    # Ensure the key matches what the frontend expects, e.g. "search_results"
    # If results is already a list, wrap it. If it's an error dict from automator, it's handled above.
    # If it's an empty list from automator.search, it will be returned as {"search_results": []}
    return {"search_results": results if isinstance(results, list) else [] }


@app.post("/api/comment")
async def api_comment(request_data: CommentRequest):
    if automation_logger:
        automation_logger.info(f"Received API comment request for URL: {request_data.post_url}")

    status = await asyncio.to_thread(
        run_automation_task,
        task_type="comment",
        post_url=request_data.post_url,
        comment_text=request_data.comment_text
    )

    if isinstance(status, dict) and "error" in status:
        if "login failed" in status["error"].lower() or "credentials" in status["error"].lower():
            raise HTTPException(status_code=401, detail=status["error"])
        elif "WebDriver" in status["error"]:
             raise HTTPException(status_code=503, detail=status["error"])
        raise HTTPException(status_code=500, detail=status["error"])

    if not (isinstance(status, dict) and status.get("success")):
        # If the task didn't return an "error" dict but success is false,
        # or if status is not the expected dict format.
        error_message = status.get("message", "Comment operation failed or returned unexpected status.") if isinstance(status, dict) else "Comment operation returned unexpected status."
        raise HTTPException(status_code=500, detail=error_message)

    return status # Should be {"success": True, "message": "..."}

# To run this application (from the backend directory):
# uvicorn main:app --reload
# Ensure FB_USER and FB_PASS environment variables are set for the uvicorn process.
# Ensure Chrome/Chromedriver are available in the environment where uvicorn runs.
