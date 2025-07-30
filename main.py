import logfire
from fastapi import FastAPI

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
# from app.monitoring.services import request_attributes_mapper, monitoring
from datapipeline.routes import app as datapipeline_router
import httpx

async def keep_service_awake():
    while True:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("https://salamstudy.onrender.com/health")
                print(f"[KeepAlive] Pinged service: {response.status_code}")
        except Exception as e:
            print(f"[KeepAlive] Error pinging service: {e}")
        await asyncio.sleep(10)  # wait 10 seconds before pinging again


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
        keep_service_awake()
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


@app.get("/health")
def read_root():
    return {"Hello": "Service is live"}


@app.get("/scalar", include_in_schema=False)
async def scalar_html():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title=app.title,
    )


app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# app.include_router(auth_router, prefix="/auth", tags=["AUTH"])
# app.include_router(references_router, prefix="/references", tags=['REFERENCES'])
app.include_router(datapipeline_router, prefix="/datapipeline", tags=['DATAPIPELINE'])
app.include_router(api_version_one)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, port=8000)
