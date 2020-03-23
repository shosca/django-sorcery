"""Default alembic config things."""

from ...db import signals


@signals.alembic_config_created.connect
def setup_config(config):
    """The default alembic config created handler."""
    config.set_section_option("loggers", "keys", "root,sqlalchemy,alembic")
    config.set_section_option("handlers", "keys", "console")
    config.set_section_option("formatters", "keys", "generic")
    config.set_section_option("logger_root", "level", "WARN")
    config.set_section_option("logger_root", "handlers", "console")
    config.set_section_option("logger_sqlalchemy", "level", "WARN")
    config.set_section_option("logger_sqlalchemy", "qualname", "sqlalchemy.engine")
    config.set_section_option("logger_alembic", "level", "INFO")
    config.set_section_option("logger_alembic", "qualname", "alembic")
    config.set_section_option("handler_console", "class", "StreamHandler")
    config.set_section_option("handler_console", "formatter", "generic")
