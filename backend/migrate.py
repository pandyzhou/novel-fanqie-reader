"""Migration workflow helper for Flask-Migrate/Alembic.

Run from repository root:

    python backend/migrate.py status
    python backend/migrate.py guide
    python backend/migrate.py heads
    python backend/migrate.py current
    python backend/migrate.py stamp-head --apply
    python backend/migrate.py upgrade
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Iterable

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import inspect as sa_inspect, text as sql_text

ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
MIGRATIONS_DIR = BACKEND_DIR / "migrations"
ALEMBIC_INI = MIGRATIONS_DIR / "alembic.ini"


def _load_app_context():
    os.environ.setdefault("SKIP_STARTUP_SCHEMA_PREPARATION", "true")
    if str(BACKEND_DIR) not in sys.path:
        sys.path.insert(0, str(BACKEND_DIR))

    from app import app, AUTO_CREATE_TABLES, RUN_LEGACY_RUNTIME_SCHEMA_PATCHES  # pylint: disable=import-outside-toplevel
    from database import db  # pylint: disable=import-outside-toplevel

    return app, db, AUTO_CREATE_TABLES, RUN_LEGACY_RUNTIME_SCHEMA_PATCHES


def _get_head_revisions():
    config = Config(str(ALEMBIC_INI))
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    script = ScriptDirectory.from_config(config)
    return list(script.get_heads())


def get_status_snapshot():
    app, db, auto_create_tables, run_legacy_runtime_schema_patches = _load_app_context()

    with app.app_context():
        inspector = sa_inspect(db.engine)
        table_names = inspector.get_table_names()
        has_alembic_version = "alembic_version" in table_names
        current_versions: list[str] = []
        if has_alembic_version:
            current_versions = [
                value
                for value in db.session.execute(sql_text("SELECT version_num FROM alembic_version")).scalars().all()
                if value
            ]

        return {
            "database_url": str(db.engine.url),
            "database_backend": db.engine.url.get_backend_name(),
            "auto_create_tables": auto_create_tables,
            "run_legacy_runtime_schema_patches": run_legacy_runtime_schema_patches,
            "migration_directory": str(MIGRATIONS_DIR),
            "table_count": len(table_names),
            "table_names": table_names,
            "has_alembic_version": has_alembic_version,
            "current_versions": current_versions,
            "head_versions": _get_head_revisions(),
        }


def print_status():
    snapshot = get_status_snapshot()
    print("=== Migration Status ===")
    print(f"Database backend      : {snapshot['database_backend']}")
    print(f"Database URL          : {snapshot['database_url']}")
    print(f"Migration directory   : {snapshot['migration_directory']}")
    print(f"AUTO_CREATE_TABLES    : {snapshot['auto_create_tables']}")
    print(f"Legacy schema patches : {snapshot['run_legacy_runtime_schema_patches']}")
    print(f"Head revisions        : {', '.join(snapshot['head_versions']) or '-'}")
    print(
        "Current revisions     : "
        + (", ".join(snapshot["current_versions"]) if snapshot["current_versions"] else "<none>")
    )
    print(f"alembic_version table : {snapshot['has_alembic_version']}")
    print(f"Detected tables       : {snapshot['table_count']}")

    if snapshot["table_names"]:
        preview = ", ".join(snapshot["table_names"][:8])
        if len(snapshot["table_names"]) > 8:
            preview += ", ..."
        print(f"Table preview         : {preview}")


def print_guide():
    snapshot = get_status_snapshot()

    print("=== Migration Guide ===")
    if snapshot["table_count"] == 0:
        print("当前数据库为空，可以直接切换到迁移模式。")
        print("建议步骤：")
        print("1. 设置 AUTO_CREATE_TABLES=false")
        print("2. 运行: python backend/migrate.py upgrade")
        print("3. 再启动应用服务")
        return

    if not snapshot["has_alembic_version"]:
        print("当前数据库已有业务表，但还没有 alembic_version 记录。")
        print("建议步骤：")
        print("1. 先完整备份当前 PostgreSQL / MySQL / SQLite 数据库")
        print("2. 确认当前数据库结构与 backend/migrations 的 baseline 匹配")
        print("3. 执行 dry-run 检查：python backend/migrate.py stamp-head")
        print("4. 确认无误后执行：python backend/migrate.py stamp-head --apply")
        print("5. 将 AUTO_CREATE_TABLES 改为 false")
        print("6. 重启 backend / celery_worker，并运行 smoke 测试")
        return

    if set(snapshot["current_versions"]) != set(snapshot["head_versions"]):
        print("数据库已纳入迁移管理，但当前版本未到 head。")
        print("建议步骤：")
        print("1. 备份数据库")
        print("2. 执行：python backend/migrate.py upgrade")
        print("3. 验证：python backend/migrate.py current")
        return

    if snapshot["auto_create_tables"]:
        print("数据库已纳入迁移管理，但仍启用了 AUTO_CREATE_TABLES。")
        print("建议步骤：")
        print("1. 将 AUTO_CREATE_TABLES 改为 false")
        print("2. 重启 backend / celery_worker")
        print("3. 验证 /api/system/info 中 auto_create_tables=false")
        return

    print("当前数据库已经处于推荐状态：已纳入迁移管理，且 AUTO_CREATE_TABLES 已关闭。")
    print("后续流程：修改模型 -> python backend/migrate.py migrate -m \"message\" -> upgrade")


def run_flask_db(subcommand: str, extra_args: list[str]):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(BACKEND_DIR)
    env["FLASK_APP"] = "manage:app"
    env.setdefault("AUTO_CREATE_TABLES", "false")

    command = [
        sys.executable,
        "-m",
        "flask",
        "db",
        subcommand,
        "--directory",
        str(MIGRATIONS_DIR),
        *extra_args,
    ]
    return subprocess.call(command, cwd=str(ROOT_DIR), env=env)


def parse_args(argv: Iterable[str] | None = None):
    parser = argparse.ArgumentParser(description="Migration workflow helper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("status", help="Show migration status for current database")
    subparsers.add_parser("guide", help="Show recommended cutover steps for current database")
    subparsers.add_parser("heads", help="Proxy to flask db heads")
    subparsers.add_parser("current", help="Proxy to flask db current")
    subparsers.add_parser("upgrade", help="Proxy to flask db upgrade")
    subparsers.add_parser("downgrade", help="Proxy to flask db downgrade")

    migrate_parser = subparsers.add_parser("migrate", help="Proxy to flask db migrate")
    migrate_parser.add_argument("-m", "--message", required=True, help="Migration message")

    stamp_parser = subparsers.add_parser("stamp-head", help="Mark current database as baseline head")
    stamp_parser.add_argument("--apply", action="store_true", help="Actually run stamp head")

    return parser.parse_args(list(argv) if argv is not None else None)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)

    if args.command == "status":
        print_status()
        return 0

    if args.command == "guide":
        print_guide()
        return 0

    if args.command == "heads":
        return run_flask_db("heads", [])

    if args.command == "current":
        return run_flask_db("current", [])

    if args.command == "upgrade":
        return run_flask_db("upgrade", [])

    if args.command == "downgrade":
        return run_flask_db("downgrade", [])

    if args.command == "migrate":
        return run_flask_db("migrate", ["-m", args.message])

    if args.command == "stamp-head":
        if not args.apply:
            print("Dry run only. This command would execute: python -m flask db stamp head")
            print("Run `python backend/migrate.py stamp-head --apply` after backing up the database.")
            return 0
        return run_flask_db("stamp", ["head"])

    raise ValueError(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
