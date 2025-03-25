import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
from dotenv import load_dotenv
from src.database import Base
from src.models.user import User, StyleQuestion, Preference, UserResponse, FaceMeasurement, Frame

# 環境変数の読み込み
load_dotenv()

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# 環境変数をConfigに設定
section = config.config_ini_section
config.set_section_option(section, "DB_USER", os.getenv("DB_USER"))
config.set_section_option(section, "DB_PASSWORD", os.getenv("DB_PASSWORD"))
config.set_section_option(section, "DB_HOST", os.getenv("DB_HOST"))
config.set_section_option(section, "DB_PORT", os.getenv("DB_PORT"))
config.set_section_option(section, "DB_NAME", os.getenv("DB_NAME"))

# SSLの設定
ssl_args = {
    "ssl": {
        "ssl_verify_cert": True,
        "ssl_verify_identity": True,
        "ssl": {
            "verify_mode": "VERIFY_IDENTITY",
            "check_hostname": True,
        }
    }
}

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# モデルのメタデータを追加
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.connect_args"] = str(ssl_args)
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()