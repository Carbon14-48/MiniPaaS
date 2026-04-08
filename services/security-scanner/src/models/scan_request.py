from pydantic import BaseModel, Field


class ScanRequest(BaseModel):
    image_tag: str = Field(..., description="Full image tag, e.g. user42/myapp:v1")
    user_id: int = Field(..., description="Owner user ID")
    app_name: str = Field(..., description="Application name")
