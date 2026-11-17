"""Metadata schema migration chain and stamp helpers (spec 4sd62s Section 5.1, 5.3)."""

from agent_workflows.migrations.chain import (
    CURRENT_METADATA_SCHEMA,
    MIGRATIONS,
    MetadataSchemaError,
    Migration,
    read_metadata_schema,
    repo_has_legacy_records,
    require_current_schema,
    write_metadata_schema,
)

__all__ = [
    "CURRENT_METADATA_SCHEMA",
    "MIGRATIONS",
    "MetadataSchemaError",
    "Migration",
    "read_metadata_schema",
    "repo_has_legacy_records",
    "require_current_schema",
    "write_metadata_schema",
]
