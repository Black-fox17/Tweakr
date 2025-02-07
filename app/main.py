
# from app.core.references_generator import ReferenceGenerator
# from datapipeline.core.constants import MONGO_DB_NAME, MONGODB_ATLAS_CLUSTER_URI
# from app.core.intext_citation import InTextCitationProcessor
# from app.core.paper_matcher import PaperKeywordMatcher



# if __name__ == "__main__":
#     matcher = PaperKeywordMatcher()
#     file_path = "/Users/naija/Documents/gigs/tweakr/tweakr-mvp/test_docs/testdoc.docx"
#     output_doc = "/Users/naija/Documents/gigs/tweakr/tweakr-mvp/test_docs/testdoc_with_citations.docx"
#     category = "quantum_physics"
#     matching_titles = matcher.match_keywords(file_path, category)

#     relevant_papers = []
#     if matching_titles:
#         print("Matching Papers:")
#         for title in matching_titles:
#             print(f"- {title}")
#             relevant_papers.append(title)

#         reference_generator = ReferenceGenerator(style="APA")
#         references = reference_generator.generate_references(matching_titles, category)

#         print("\nReferences:")
#         for reference in references:
#             print(f"- {reference}")
#         try:
#             intext_citation = InTextCitationProcessor(style="APA", collection_name="quantum_physics")
#             modified_file_path = intext_citation.process_sentences(file_path, output_doc)
#             print(f"Modified draft saved to: {modified_file_path}")
#         except Exception as e:
#             print(f"Error processing draft: {e}")
#     else:
#         print("No matching papers found.")



import logfire
from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer
from fastapi.openapi.utils import get_openapi
from scalar_fastapi import get_scalar_api_reference


from app.monitoring.services import request_attributes_mapper, monitoring
from app.auth.routes import router as auth_router


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="PoeAI | Main",
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


app = FastAPI()

monitoring.instrument_fastapi(app, request_attributes_mapper=request_attributes_mapper)
monitoring.instrument_system_metrics()

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

app.include_router(auth_router, prefix="/auth", tags=["AUTH"])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
