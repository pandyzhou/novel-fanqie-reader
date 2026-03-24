#!/usr/bin/env python3
"""后端 API 冒烟测试。

默认使用隔离环境（临时 SQLite + 内存 Celery）验证主链路，
避免外部 Redis / 数据库 / 上游接口影响结果。

可选使用当前环境模式，验证已配置环境下的接口可达性：
    python backend/tests/smoke_api.py --mode current
    python backend/tests/smoke_api.py --mode isolated
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from dataclasses import dataclass
from typing import Any, Iterable, Optional

BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@dataclass
class CheckResult:
    name: str
    passed: bool
    category: str
    detail: str


class SmokeSuite:
    def __init__(self) -> None:
        self.results: list[CheckResult] = []

    def add(self, name: str, passed: bool, category: str = "required", detail: str = "") -> None:
        self.results.append(CheckResult(name=name, passed=passed, category=category, detail=detail))

    def fail_required_count(self) -> int:
        return sum(1 for item in self.results if item.category == "required" and not item.passed)

    def external_fail_count(self) -> int:
        return sum(1 for item in self.results if item.category == "external" and not item.passed)

    def print_summary(self) -> None:
        print("\n=== Smoke Test Summary ===")
        for item in self.results:
            status = "PASS" if item.passed else "FAIL"
            detail = f" | {item.detail}" if item.detail else ""
            print(f"[{status}] ({item.category}) {item.name}{detail}")

        print("\nRequired failures:", self.fail_required_count())
        print("External-dependent failures:", self.external_fail_count())


def configure_environment(mode: str) -> Optional[str]:
    temp_db_path: Optional[str] = None
    if mode == "isolated":
        fd, temp_db_path = tempfile.mkstemp(prefix="fanqie_smoke_", suffix=".db")
        os.close(fd)
        os.environ["DATABASE_URL"] = f"sqlite:///{temp_db_path}"
        os.environ["CELERY_BROKER_URL"] = "memory://"
        os.environ["CELERY_RESULT_BACKEND"] = "cache+memory://"
        os.environ["INTERNAL_API_MODE"] = "true"
        os.environ["INTERNAL_API_USER_ID"] = "1"
        os.environ["AUTO_CREATE_TABLES"] = "true"
        os.environ["RUN_LEGACY_RUNTIME_SCHEMA_PATCHES"] = "false"
        os.environ.setdefault("JWT_SECRET_KEY", "dev-jwt-secret-key-please-change-1234")
        os.environ.setdefault("FLASK_SECRET_KEY", "dev-flask-secret-key-please-change-1234")
    return temp_db_path


def import_app_modules():
    if BACKEND_ROOT not in sys.path:
        sys.path.insert(0, BACKEND_ROOT)

    from app import app  # pylint: disable=import-outside-toplevel
    from models import Chapter, DownloadTask, Novel  # pylint: disable=import-outside-toplevel

    return app, Novel, Chapter, DownloadTask


def response_json(response) -> Any:
    try:
        return response.get_json()
    except Exception:
        return None


def run_common_checks(client, suite: SmokeSuite) -> None:
    healthz = client.get("/healthz")
    suite.add("GET /healthz", healthz.status_code == 200, detail=f"status={healthz.status_code}")

    system_info = client.get("/api/system/info")
    system_json = response_json(system_info) or {}
    suite.add(
        "GET /api/system/info",
        system_info.status_code == 200
        and "database_backend" in system_json
        and "internal_api_mode" in system_json
        and "auto_create_tables" in system_json
        and "run_legacy_runtime_schema_patches" in system_json
        and "migration_directory" in system_json
        and "migration_version_table_present" in system_json
        and "current_migration_versions" in system_json,
        detail=f"status={system_info.status_code}",
    )

    novels = client.get("/api/novels?page=1&per_page=5")
    novels_json = response_json(novels) or {}
    suite.add(
        "GET /api/novels?page=1&per_page=5",
        novels.status_code == 200 and isinstance(novels_json.get("novels"), list),
        detail=f"status={novels.status_code}",
    )

    tasks = client.get("/api/tasks/list")
    tasks_json = response_json(tasks) or {}
    suite.add(
        "GET /api/tasks/list",
        tasks.status_code == 200 and isinstance(tasks_json.get("tasks"), list),
        detail=f"status={tasks.status_code}",
    )


def run_isolated_checks(app, Novel, Chapter, DownloadTask, suite: SmokeSuite) -> None:
    with app.app_context():
        client = app.test_client()
        run_common_checks(client, suite)

        username = "smoke_user"
        password = "password123"

        register = client.post("/api/auth/register", json={"username": username, "password": password})
        suite.add("POST /api/auth/register", register.status_code == 200, detail=f"status={register.status_code}")

        login = client.post("/api/auth/login", json={"username": username, "password": password})
        login_json = response_json(login) or {}
        token = login_json.get("access_token")
        suite.add(
            "POST /api/auth/login",
            login.status_code == 200 and isinstance(token, str) and len(token) > 20,
            detail=f"status={login.status_code}",
        )

        me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"}) if token else None
        me_json = response_json(me) if me is not None else None
        suite.add(
            "GET /api/auth/me",
            me is not None and me.status_code == 200 and me_json.get("username") == username,
            detail=f"status={me.status_code if me is not None else 'n/a'}",
        )

        novel_id = "999123456789"
        add_novel = client.post("/api/novels", json={"novel_id": novel_id})
        add_json = response_json(add_novel) or {}
        suite.add(
            "POST /api/novels",
            add_novel.status_code == 202 and isinstance(add_json.get("celery_task_id"), str),
            detail=f"status={add_novel.status_code}",
        )

        task_list = client.get("/api/tasks/list")
        task_list_json = response_json(task_list) or {}
        tasks = task_list_json.get("tasks", [])
        suite.add(
            "GET /api/tasks/list after queue",
            task_list.status_code == 200
            and len(tasks) == 1
            and isinstance(tasks[0].get("status"), str)
            and "task_stage" in tasks[0]
            and "error_code" in tasks[0]
            and "raw_message" in tasks[0],
            detail=f"status={task_list.status_code}, count={len(tasks)}",
        )

        novel_detail = client.get(f"/api/novels/{novel_id}")
        novel_json = response_json(novel_detail) or {}
        suite.add(
            "GET /api/novels/<id>",
            novel_detail.status_code == 200 and novel_json.get("id") == novel_id,
            detail=f"status={novel_detail.status_code}",
        )

        chapters = client.get(f"/api/novels/{novel_id}/chapters?page=1&per_page=5")
        chapters_json = response_json(chapters) or {}
        suite.add(
            "GET /api/novels/<id>/chapters",
            chapters.status_code == 200 and isinstance(chapters_json.get("chapters"), list),
            detail=f"status={chapters.status_code}",
        )

        wordcloud = client.get(f"/api/stats/wordcloud/{novel_id}")
        suite.add(
            "GET /api/stats/wordcloud/<id> (missing)",
            wordcloud.status_code == 404,
            detail=f"status={wordcloud.status_code}",
        )

        download = client.get(f"/api/novels/{novel_id}/download")
        suite.add(
            "GET /api/novels/<id>/download (missing)",
            download.status_code == 404,
            detail=f"status={download.status_code}",
        )

        task_id = tasks[0]["id"] if tasks else None
        if task_id is not None:
            terminate = client.post(f"/api/tasks/{task_id}/terminate")
            terminate_json = response_json(terminate) or {}
            suite.add(
                "POST /api/tasks/<id>/terminate",
                terminate.status_code == 200 and terminate_json.get("task", {}).get("status") == "TERMINATED",
                detail=f"status={terminate.status_code}",
            )

            delete_task = client.delete(f"/api/tasks/{task_id}")
            suite.add(
                "DELETE /api/tasks/<id>",
                delete_task.status_code == 200,
                detail=f"status={delete_task.status_code}",
            )

        suite.add(
            "Isolated DB task count",
            DownloadTask.query.count() == 0,
            detail=f"count={DownloadTask.query.count()}",
        )
        suite.add(
            "Isolated DB novel placeholder exists",
            Novel.query.count() == 1 and Chapter.query.count() == 0,
            detail=f"novels={Novel.query.count()}, chapters={Chapter.query.count()}",
        )


def run_current_checks(app, Novel, Chapter, _DownloadTask, suite: SmokeSuite) -> None:
    with app.app_context():
        client = app.test_client()
        run_common_checks(client, suite)

        search = client.get("/api/search?query=斗罗&per_page=1")
        suite.add(
            "GET /api/search?query=斗罗&per_page=1",
            search.status_code == 200,
            category="external",
            detail=f"status={search.status_code}",
        )

        latest_novel = Novel.query.order_by(Novel.created_at.desc()).first()
        if not latest_novel:
            suite.add("Existing novel resource checks", True, category="optional", detail="no existing novel data")
            return

        novel_id = latest_novel.id
        detail = client.get(f"/api/novels/{novel_id}")
        suite.add(
            "GET /api/novels/<existing-id>",
            detail.status_code == 200,
            detail=f"status={detail.status_code}",
        )

        chapters = client.get(f"/api/novels/{novel_id}/chapters?page=1&per_page=5")
        suite.add(
            "GET /api/novels/<existing-id>/chapters",
            chapters.status_code == 200,
            detail=f"status={chapters.status_code}",
        )

        cover = client.get(f"/api/novels/{novel_id}/cover")
        suite.add(
            "GET /api/novels/<existing-id>/cover",
            cover.status_code in {200, 404},
            detail=f"status={cover.status_code}",
        )

        wordcloud = client.get(f"/api/stats/wordcloud/{novel_id}")
        suite.add(
            "GET /api/stats/wordcloud/<existing-id>",
            wordcloud.status_code in {200, 404},
            detail=f"status={wordcloud.status_code}",
        )

        first_chapter = Chapter.query.filter_by(novel_id=novel_id).order_by(Chapter.chapter_index.asc()).first()
        if first_chapter:
            chapter_detail = client.get(f"/api/novels/{novel_id}/chapters/{first_chapter.id}")
            suite.add(
                "GET /api/novels/<existing-id>/chapters/<chapter-id>",
                chapter_detail.status_code == 200,
                detail=f"status={chapter_detail.status_code}",
            )
        else:
            suite.add(
                "Existing chapter detail check",
                True,
                category="optional",
                detail="selected novel has no chapters in DB",
            )


def parse_args(argv: Optional[Iterable[str]] = None):
    parser = argparse.ArgumentParser(description="Run backend smoke tests")
    parser.add_argument(
        "--mode",
        choices=["isolated", "current"],
        default="isolated",
        help="isolated 使用临时 SQLite 与内存 Celery；current 使用当前环境配置。",
    )
    return parser.parse_args(list(argv) if argv is not None else None)


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = parse_args(argv)
    temp_db_path = configure_environment(args.mode)
    suite = SmokeSuite()

    try:
        app, Novel, Chapter, DownloadTask = import_app_modules()
        if args.mode == "isolated":
            run_isolated_checks(app, Novel, Chapter, DownloadTask, suite)
        else:
            run_current_checks(app, Novel, Chapter, DownloadTask, suite)
    finally:
        if temp_db_path and os.path.exists(temp_db_path):
            try:
                from database import db  # pylint: disable=import-outside-toplevel

                db.session.remove()
                db.engine.dispose()
            except Exception:
                pass
            try:
                os.remove(temp_db_path)
            except PermissionError:
                print(f"[WARN] 临时数据库文件仍被占用，已保留：{temp_db_path}")

    suite.print_summary()
    return 1 if suite.fail_required_count() > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
