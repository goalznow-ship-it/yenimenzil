import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

import app.models  # noqa: F401  (register all models on Base.metadata)
from alembic import context
from app.core.config import get_settings
from app.db.base import Base

config = context.config
config.set_main_option("sqlalchemy.url", get_settings().DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

POSTGIS_SYSTEM_TABLES = frozenset(
    {
        "spatial_ref_sys",
        "geometry_columns",
        "geography_columns",
        "raster_columns",
        "raster_overviews",
        "layer",
        "topology",
        "addr",
        "addrfeat",
        "bg",
        "county",
        "county_lookup",
        "countysub_lookup",
        "cousub",
        "direction_lookup",
        "edges",
        "faces",
        "featnames",
        "geocode_settings",
        "geocode_settings_default",
        "loader_lookuptables",
        "loader_platform",
        "loader_variables",
        "pagc_gaz",
        "pagc_lex",
        "pagc_rules",
        "place",
        "place_lookup",
        "secondary_unit_lookup",
        "state",
        "state_lookup",
        "street_type_lookup",
        "tabblock",
        "tabblock20",
        "tract",
        "water",
        "zcta5",
        "zip_lookup",
        "zip_lookup_all",
        "zip_lookup_base",
        "zip_state",
        "zip_state_loc",
    }
)
POSTGIS_SYSTEM_SCHEMAS = frozenset({"tiger", "tiger_data", "topology"})


def include_object(object, name, type_, reflected, compare_to):
    if type_ == "table":
        schema = getattr(object, "schema", None)
        if schema in POSTGIS_SYSTEM_SCHEMAS or name in POSTGIS_SYSTEM_TABLES:
            return False
    if type_ == "index":
        table = getattr(object, "table", None)
        if table is not None and table.name in POSTGIS_SYSTEM_TABLES:
            return False
        if name == "idx_property_locations_point":
            return False
    return True


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
