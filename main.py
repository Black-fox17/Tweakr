import logfire
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Response
from pypdf import PdfReader, PdfWriter
import io
import json
from typing import Dict
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer
from fastapi.openapi.utils import get_openapi
from scalar_fastapi import get_scalar_api_reference
from api.v1.routes import api_version_one
from api.db.database import get_db
import asyncio
from threading import Thread
from api.v1.services.documents import document_service
from api.v1.services.subscription import subscription_service
import httpx

async def keep_service_awake():
    while True:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("https://salamstudy.onrender.com/health")
                print(f"[KeepAlive] Pinged service: {response.status_code}")
        except Exception as e:
            print(f"[KeepAlive] Error pinging service: {e}")
        await asyncio.sleep(120)  # wait 120 seconds before pinging again


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Tweakr | Main",
        version="1.0.0",
        description="Create your dream podcasts",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "Bearer": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
    }
    openapi_schema["security"] = [{"Bearer": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

async def cleanup_expired_users():
    while True:
        try:
            db = next(get_db())
            deleted_count = subscription_service.cleanup_expired_subs(db)
            if deleted_count > 0:
                print(f"Cleaned up {deleted_count} users")
        except Exception as e:
            print(f"Error during cleanup: {e}")
        finally:
            if 'db' in locals():
                db.close()
        await asyncio.sleep(3600)
async def cleanup_expired_documents():
    while True:
        try:
            db = next(get_db())
            deleted_count = document_service.cleanup_expired(db)
            if deleted_count > 0:
                print(f"Cleaned up {deleted_count} expired documents")
        except Exception as e:
            print(f"Error during cleanup: {e}")
        finally:
            if 'db' in locals():
                db.close()
        await asyncio.sleep(3600)

async def run_all_cleanup_tasks():
    await asyncio.gather(
        cleanup_expired_documents(),
        cleanup_expired_users(),
        # keep_service_awake()
    )

def start_cleanup_task():
    def run_cleanup():
        asyncio.run(run_all_cleanup_tasks())

    cleanup_thread = Thread(target=run_cleanup, daemon=True)
    cleanup_thread.start()

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    start_cleanup_task()
    print("Background cleanup task started")

app.openapi = custom_openapi
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/verify-code/")


@app.get("/", include_in_schema=False)
async def redirect_to_docs():
    """
    Redirects users from the root endpoint to the docs endpoint.
    """
    return RedirectResponse(url="/docs")

@app.post("/merge-pdfs/")
async def merge_pdfs(files: list[UploadFile] = File(...)):
    writer = PdfWriter()
    output_buffer = io.BytesIO()

    for uploaded_file in files:
        if uploaded_file.filename and uploaded_file.filename.lower().endswith(".pdf"):
            content = await uploaded_file.read()
            reader = PdfReader(io.BytesIO(content))
            for page in reader.pages:
                writer.add_page(page)

    writer.write(output_buffer)
    output_buffer.seek(0)

    return Response(
        content=output_buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=merged.pdf"}
    )



@app.get("/health")
def read_root():
    return {"Hello": "Service is live"}


@app.get("/scalar", include_in_schema=False)
async def scalar_html():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title=app.title,
    )

clients: Dict[str, WebSocket] = {}
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    user_id = websocket.query_params.get("userId")

    if not user_id:
        await websocket.close()
        return

    await websocket.accept()
    clients[user_id] = websocket
    print(f"WebSocket client connected: {user_id}. Total clients: {len(clients)}")

    try:
        while True:
            message = await websocket.receive_text()

            try:
                data = json.loads(message)
                to_user = data.get("to")
                from_user = data.get("from")
                content = data.get("content")

                if not to_user or not from_user or not content:
                    print("Invalid message received:", data)
                    continue

                print(f"Routing message from {from_user} to {to_user}")

                recipient = clients.get(to_user)

                if recipient:
                    await recipient.send_text(
                        json.dumps({"from": from_user, "content": content})
                    )
                    print(f"Message successfully sent to {to_user}")
                else:
                    print(f"Recipient {to_user} not found or connection not open.")

            except Exception as e:
                print("Failed to process message:", e)

    except WebSocketDisconnect:
        for key, value in list(clients.items()):
            if value == websocket:
                del clients[key]
                print(f"WebSocket client disconnected: {key}. Total clients: {len(clients)}")
                break

    except Exception as e:
        print("WebSocket error:", e)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://www.tweakrr.com",  
        "http://localhost:5173",
        "http://localhost:3000",
        "https://tweakr-payment.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# app.include_router(auth_router, prefix="/auth", tags=["AUTH"])
# app.include_router(references_router, prefix="/references", tags=['REFERENCES'])
app.include_router(api_version_one)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, port=8000)
