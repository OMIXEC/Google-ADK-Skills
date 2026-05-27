"""Tool definitions for parallel fan-out workers."""

from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger(__name__)


class ChunkInput(BaseModel):
    chunk: dict = Field(description="Data chunk to process")
    worker_id: str = Field(description="Worker identifier (A, B, or C)")


class ChunkOutput(BaseModel):
    result: dict
    worker_id: str
    processing_time_ms: float


def process_chunk(params: ChunkInput) -> ChunkOutput:
    """Process a data chunk. Each worker calls this independently."""
    logger.info("tool_call", tool="process_chunk", worker_id=params.worker_id)
    return ChunkOutput(result=params.chunk, worker_id=params.worker_id, processing_time_ms=0.0)
