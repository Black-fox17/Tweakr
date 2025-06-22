from fastapi import APIRouter
from api.v1.routes.auth import auth
from api.v1.routes.google_login import google_auth
from api.v1.routes.faq import faq
from api.v1.routes.citations import citations
from api.v1.routes.subscription import subscription
from api.v1.routes.documents import document

api_version_one = APIRouter(prefix="/api/v1")

api_version_one.include_router(auth)
api_version_one.include_router(google_auth)
api_version_one.include_router(faq)
api_version_one.include_router(citations)
api_version_one.include_router(subscription)
api_version_one.include_router(document)