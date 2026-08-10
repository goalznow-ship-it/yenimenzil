from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    application: str
    database: str
    redis: str
