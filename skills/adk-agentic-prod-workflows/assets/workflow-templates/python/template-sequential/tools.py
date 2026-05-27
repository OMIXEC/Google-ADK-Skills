"""Tool definitions for sequential pipeline (ETL)."""

from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger(__name__)


class ExtractParams(BaseModel):
    source: str = Field(description="Data source (db table, API endpoint, file path)")
    since: str | None = Field(default=None, description="Incremental extraction timestamp")


class ExtractResult(BaseModel):
    data: list[dict]
    count: int
    source: str
    status: str


def extract_data(params: ExtractParams) -> ExtractResult:
    """Extract data from source."""
    logger.info("tool_call", tool="extract_data", source=params.source)
    return ExtractResult(data=[], count=0, source=params.source, status="ok")


class TransformParams(BaseModel):
    data: list[dict] = Field(description="Raw data to transform")
    rules: list[str] = Field(default_factory=list, description="Transform rules to apply")


class TransformResult(BaseModel):
    data: list[dict]
    stats: dict
    status: str
    error: str | None = None


def transform_data(params: TransformParams) -> TransformResult:
    """Transform raw data."""
    logger.info("tool_call", tool="transform_data", rules=params.rules)
    return TransformResult(data=params.data, stats={}, status="ok", error=None)


class LoadParams(BaseModel):
    data: list[dict] = Field(description="Transformed data to load")
    destination: str = Field(description="Target destination")
    mode: str = Field(default="append", description="Load mode: append, overwrite, upsert")


class LoadResult(BaseModel):
    rows_loaded: int
    destination: str
    status: str


def load_data(params: LoadParams) -> LoadResult:
    """Load data to destination."""
    logger.info("tool_call", tool="load_data", destination=params.destination)
    return LoadResult(rows_loaded=len(params.data), destination=params.destination, status="ok")
