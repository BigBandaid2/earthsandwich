"""T014 — SQLAlchemy 2.x reflection of the target schema (US2)."""
from __future__ import annotations

from sqlalchemy import create_engine, inspect

from project.create import OperatorError, _normalize_dsn


def reflect_schema(dsn: str) -> dict:
    """Reflect tables, columns, types, PK/FK, and NOT-NULL constraints.

    Returns ``{"tables": [{"name", "columns": [{"name","type","nullable",
    "primary_key"}], "foreign_keys": [{"column","references"}]}]}``.
    """
    try:
        engine = create_engine(_normalize_dsn(dsn), connect_args=_connect_args(dsn))
    except Exception as exc:
        raise OperatorError(f"target DSN rejected: {exc}")
    try:
        inspector = inspect(engine)
        tables = []
        for table_name in sorted(inspector.get_table_names()):
            pk_cols = set((inspector.get_pk_constraint(table_name) or {}).get("constrained_columns") or [])
            columns = [
                {
                    "name": col["name"],
                    "type": str(col["type"]),
                    "nullable": bool(col.get("nullable", True)),
                    "primary_key": col["name"] in pk_cols,
                }
                for col in inspector.get_columns(table_name)
            ]
            foreign_keys = [
                {
                    "column": ", ".join(fk.get("constrained_columns") or []),
                    "references": f"{fk.get('referred_table')}({', '.join(fk.get('referred_columns') or [])})",
                }
                for fk in inspector.get_foreign_keys(table_name)
            ]
            tables.append({"name": table_name, "columns": columns, "foreign_keys": foreign_keys})
        return {"tables": tables}
    except OperatorError:
        raise
    except Exception as exc:
        raise OperatorError(f"target schema reflection failed: {exc}")
    finally:
        engine.dispose()


def _connect_args(dsn: str) -> dict:
    if _normalize_dsn(dsn).startswith(("postgresql", "mysql", "mariadb")):
        return {"connect_timeout": 10}
    return {}
