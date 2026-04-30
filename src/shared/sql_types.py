"""
Portable SQLAlchemy types used across the app.

The production database is PostgreSQL, but unit tests run against SQLite.
These helpers keep model metadata portable without giving up PostgreSQL's
JSONB / ARRAY / pgvector support in production.
"""

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, Text, Uuid
from sqlalchemy.dialects.postgresql import ARRAY, JSONB

UUIDType = Uuid(as_uuid=True)
JSONType = JSON().with_variant(JSONB, "postgresql")
StringListType = JSON().with_variant(ARRAY(Text), "postgresql")


def vector_type(dimensions: int):
    """Use pgvector on PostgreSQL and JSON arrays elsewhere."""
    return JSON().with_variant(Vector(dimensions), "postgresql")
