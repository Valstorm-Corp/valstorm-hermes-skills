---
name: valstorm-backend-patterns
description: Use when building Python backend API routes or WebSockets.
tags: [valstorm, backend, python, fastapi, websockets, routing]
---

# Valstorm Backend Patterns

Use this skill when modifying the Valstorm FastAPI backend (`apps/api`).

## WebSocket Authentication
When writing a new WebSocket route (e.g., `@router.websocket("/ws-endpoint")`), the backend must explicitly wait for and validate the authentication payload from the frontend before allowing the stream to proceed.

**Implementation Pattern:**
```python
from valstorm.auth import get_current_user_websocket

@router.websocket("/ws-endpoint")
async def my_websocket_route(websocket: WebSocket):
    await websocket.accept()
    
    # Wait for the client to send the authentication token payload
    try:
        auth_message = await websocket.receive_text()
        auth_data = json.loads(auth_message)
        if auth_data.get('type') != 'authenticate' or not auth_data.get('token'):
            await websocket.close(code=4000, reason="Missing or invalid auth payload")
            return
            
        user = await get_current_user_websocket(token=auth_data.get('token'))
        if not user:
            await websocket.close(code=4001, reason="Invalid token")
            return
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        await websocket.close(code=4002, reason="Authentication failed")
        return
        
    # Proceed with authenticated logic...
```

## Bypassing Complex Workflows (Ad-Hoc Modifications)
When temporarily bypassing complex systems (like background video compression) inside route logic, do not simply comment out the background task invocation. 
You must also intercept any flag or conditional that relies on that workflow running. 

For example, if you comment out the `compress_and_finalize_direct_video` task, you must also locate where the system determines if the file *needs* compression (e.g., `is_video = False`) and override it, so downstream consumers don't get stuck waiting for a background task that will never fire. Finally, if there is a unit test explicitly asserting the background task is called, update the mock assertion to `mock_task.assert_not_called()`.

## Pyright/Type-Checking Database Results
When querying the MongoDB wrapper using `platform.query.sql()`, the return type can be ambiguous to Pyright/Pylance (it might return a `dict`, a list, or a custom `QueryRecordList` object).

When extracting `records` from the response, strictly check for both dictionary keys and class attributes to satisfy the type checker and prevent runtime crashes:

```python
count_res = await platform.query.sql("SELECT id FROM ...")
if isinstance(count_res, dict):
    count_records = count_res.get("records", [])
elif hasattr(count_res, "records") and not isinstance(count_res, list):
    count_records = getattr(count_res, "records", [])
else:
    count_records = count_res
```