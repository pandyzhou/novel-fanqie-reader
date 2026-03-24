# backend/app.py
import logging
import sys
import os
import re
import json
import math
import shutil
from datetime import datetime, timedelta
from functools import cmp_to_key
from typing import Optional
from urllib.parse import urlparse

from flask import Flask, request, jsonify, send_file, current_app, abort, Response
from flask_jwt_extended import (
    JWTManager,
    jwt_required,
    get_jwt_identity,
    verify_jwt_in_request,
)
from flask_jwt_extended.exceptions import JWTDecodeError, NoAuthorizationError
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
from flask_migrate import Migrate
from celery.result import AsyncResult
from sqlalchemy import desc, asc, text as sql_text, func, case, and_, or_, inspect as sa_inspect
from werkzeug.exceptions import HTTPException

from database import db as _db
from models import Novel, Chapter, WordStat, User, DownloadTask, TaskStatus, SearchCacheEntry, SearchQueryCacheEntry
from config import settings, get_downloader_config
from auth import auth_bp
from celery_init import celery_app, configure_celery

try:
    from novel_downloader.novel_src.base_system.context import GlobalContext
    from novel_downloader.novel_src.network_parser.network import NetworkClient

    DOWNLOADER_AVAILABLE = True
except ImportError as e:
    logging.getLogger("app.init").error(f"Failed novel_downloader import: {e}")
    DOWNLOADER_AVAILABLE = False

# --- Logging Setup ---
log_level_str = os.getenv("FLASK_LOG_LEVEL", "INFO").upper()
log_level = getattr(logging, log_level_str, logging.INFO)
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - [%(threadName)s] - %(message)s"
)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(log_level)
handler.setFormatter(formatter)

# --- Flask App Init ---
app = Flask(__name__)
app.config.from_object(settings)

app.logger.addHandler(handler)
app.logger.setLevel(log_level)
app.logger.propagate = False
app.logger.info(f"Flask application starting with log level {log_level_str}")
if settings.DATABASE_FALLBACK_ACTIVE:
    app.logger.warning(
        "Primary database unavailable; using fallback backend %s.",
        settings.ACTIVE_DATABASE_BACKEND,
    )
    if settings.DATABASE_FALLBACK_REASON:
        app.logger.warning("Database fallback reason: %s", settings.DATABASE_FALLBACK_REASON)
else:
    app.logger.info("Database backend active: %s", settings.ACTIVE_DATABASE_BACKEND)

# --- Extensions Init ---
_db.init_app(app)
migrate = Migrate(app, _db, directory=os.path.join(os.path.dirname(__file__), "migrations"))
jwt = JWTManager(app)
cors_allowed_origins = os.getenv(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174,http://localhost:26013,http://127.0.0.1:26013",
)
cors_allowed_origins = [origin.strip() for origin in cors_allowed_origins.split(",") if origin.strip()]

socketio = SocketIO(
    app,
    message_queue=settings.CELERY_BROKER_URL,
    async_mode="eventlet",
    cors_allowed_origins=cors_allowed_origins,
)
app.register_blueprint(auth_bp)
configure_celery(app)

INTERNAL_API_MODE = os.getenv("INTERNAL_API_MODE", "true").lower() == "true"
INTERNAL_API_USER_ID = int(os.getenv("INTERNAL_API_USER_ID", "1"))
AUTO_CREATE_TABLES = os.getenv("AUTO_CREATE_TABLES", "false").lower() == "true"
RUNNING_FLASK_DB_COMMAND = any(arg == "db" for arg in sys.argv[1:3])
SKIP_STARTUP_SCHEMA_PREPARATION = (
    os.getenv("SKIP_STARTUP_SCHEMA_PREPARATION", "false").lower() == "true"
)
RUN_LEGACY_RUNTIME_SCHEMA_PATCHES = (
    os.getenv("RUN_LEGACY_RUNTIME_SCHEMA_PATCHES", "false").lower() == "true"
)

# --- Database Creation ---
def _get_migration_runtime_info():
    try:
        inspector = sa_inspect(_db.engine)
        has_version_table = "alembic_version" in inspector.get_table_names()
        current_versions = []
        if has_version_table:
            current_versions = [
                value
                for value in _db.session.execute(sql_text("SELECT version_num FROM alembic_version")).scalars().all()
                if value
            ]
        return {
            "migration_version_table_present": has_version_table,
            "current_migration_versions": current_versions,
        }
    except Exception as migration_err:
        app.logger.warning(f"Unable to inspect migration runtime info: {migration_err}")
        return {
            "migration_version_table_present": False,
            "current_migration_versions": [],
        }


def _run_legacy_runtime_schema_patches():
    engine_name = _db.engine.url.get_backend_name()
    statements = []
    if engine_name.startswith("postgresql"):
        statements = [
            "ALTER TABLE search_cache_entry ADD COLUMN IF NOT EXISTS search_hits INTEGER DEFAULT 0 NOT NULL"
        ]
    elif engine_name.startswith("sqlite"):
        statements = [
            "ALTER TABLE search_cache_entry ADD COLUMN search_hits INTEGER DEFAULT 0 NOT NULL"
        ]

    for statement in statements:
        try:
            _db.session.execute(sql_text(statement))
            _db.session.commit()
        except Exception as schema_err:
            _db.session.rollback()
            if engine_name.startswith("sqlite") and "duplicate column name" in str(schema_err).lower():
                continue
            if engine_name.startswith("postgresql") and "already exists" in str(schema_err).lower():
                continue
            app.logger.warning(f"Runtime schema update skipped: {schema_err}")

try:
    with app.app_context():
        if RUNNING_FLASK_DB_COMMAND:
            app.logger.info("Detected Flask db command; skipping automatic create_all schema preparation.")
        elif SKIP_STARTUP_SCHEMA_PREPARATION:
            app.logger.info("SKIP_STARTUP_SCHEMA_PREPARATION enabled; skipping startup schema preparation.")
        elif AUTO_CREATE_TABLES:
            app.logger.info("Creating database tables if they don't exist...")
            _db.create_all()
            if RUN_LEGACY_RUNTIME_SCHEMA_PATCHES:
                app.logger.warning(
                    "RUN_LEGACY_RUNTIME_SCHEMA_PATCHES enabled; applying legacy runtime schema patches. "
                    "This path is for emergency compatibility only and should not replace Alembic migrations."
                )
                _run_legacy_runtime_schema_patches()
            app.logger.info("Database tables checked/created.")
        else:
            migration_info = _get_migration_runtime_info()
            if not migration_info["migration_version_table_present"]:
                app.logger.warning(
                    "AUTO_CREATE_TABLES disabled but alembic_version table is missing. "
                    "Run the migration workflow helper or `flask db stamp/upgrade` before starting the app."
                )
            else:
                app.logger.info("AUTO_CREATE_TABLES disabled; relying on Flask-Migrate/Alembic migrations.")
except Exception as e:
    app.logger.error(f"Error during startup schema preparation: {e}", exc_info=True)

@app.get("/healthz")
def healthz():
    try:
        _db.session.execute(sql_text("SELECT 1"))
        return jsonify(
            status="ok",
            database_backend=settings.ACTIVE_DATABASE_BACKEND,
            database_fallback_active=settings.DATABASE_FALLBACK_ACTIVE,
        )
    except Exception as exc:
        app.logger.warning(f"Health check failed: {exc}")
        return (
            jsonify(
                status="error",
                database_backend=settings.ACTIVE_DATABASE_BACKEND,
                database_fallback_active=settings.DATABASE_FALLBACK_ACTIVE,
                error="database_unavailable",
            ),
            503,
        )


@app.get("/api/system/info")
def system_info():
    migration_info = _get_migration_runtime_info()

    return jsonify(
        {
            "project_root": os.path.dirname(__file__),
            "data_base_path": settings.DATA_BASE_PATH,
            "novel_save_path": settings.NOVEL_SAVE_PATH,
            "novel_status_path": settings.NOVEL_STATUS_PATH,
            "wordcloud_save_path": settings.WORDCLOUD_SAVE_PATH,
            "search_cover_cache_path": settings.SEARCH_COVER_CACHE_PATH,
            "database_backend": settings.ACTIVE_DATABASE_BACKEND,
            "database_fallback_active": settings.DATABASE_FALLBACK_ACTIVE,
            "database_fallback_reason": settings.DATABASE_FALLBACK_REASON,
            "cache_enabled": True,
            "internal_api_mode": INTERNAL_API_MODE,
            "internal_api_user_id": INTERNAL_API_USER_ID,
            "auto_create_tables": AUTO_CREATE_TABLES,
            "run_legacy_runtime_schema_patches": RUN_LEGACY_RUNTIME_SCHEMA_PATCHES,
            "migration_directory": os.path.join(os.path.dirname(__file__), "migrations"),
            "migration_version_table_present": migration_info["migration_version_table_present"],
            "current_migration_versions": migration_info["current_migration_versions"],
        }
    )


# --- JWT Loaders ---
@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    try:
        user_id = int(identity)
        return User.query.get(user_id)
    except (ValueError, TypeError):
        app.logger.warning(f"Invalid user identity format in JWT: {identity}")
        return None


@jwt.user_lookup_error_loader
def custom_user_lookup_error(_jwt_header, jwt_data):
    identity = jwt_data.get("sub", "<unknown>")
    app.logger.warning(
        f"User lookup failed for identity: {identity}. User might not exist."
    )
    return jsonify(
        msg="用户不存在或令牌关联的用户已被删除", error="user_not_found"
    ), 401


@jwt.unauthorized_loader
def missing_token_callback(error_string):
    app.logger.debug(f"Unauthorized - Missing JWT: {error_string}")
    return jsonify(
        msg=f"需要提供授权令牌 ({error_string})", error="authorization_required"
    ), 401


@jwt.invalid_token_loader
def invalid_token_callback(error_string):
    app.logger.debug(f"Unauthorized - Invalid JWT: {error_string}")
    return jsonify(
        msg=f"无效或格式错误的令牌 ({error_string})", error="invalid_token"
    ), 401


@jwt.expired_token_loader
def expired_token_callback(_jwt_header, _jwt_payload):
    app.logger.debug("Unauthorized - Expired JWT")
    return jsonify(msg="令牌已过期，请重新登录", error="token_expired"), 401


@jwt.needs_fresh_token_loader
def token_not_fresh_callback(_jwt_header, _jwt_payload):
    app.logger.debug("Unauthorized - Fresh token required")
    return jsonify(msg="需要提供刷新令牌", error="fresh_token_required"), 401


@jwt.revoked_token_loader
def revoked_token_callback(_jwt_header, _jwt_payload):
    app.logger.debug("Unauthorized - Revoked token")
    return jsonify(msg="令牌已被撤销", error="token_revoked"), 401


# --- SocketIO Handlers ---
connected_users = {}


def _join_task_room(user_id: int, sid: str):
    room = f"user_{user_id}"
    join_room(room, sid=sid)
    connected_users.setdefault(user_id, set()).add(sid)
    app.logger.info(f"User {user_id} (SID: {sid}) joined room '{room}'.")


def _remove_connected_sid(sid: str):
    for user_id, sid_set in list(connected_users.items()):
        if sid in sid_set:
            sid_set.remove(sid)
            if not sid_set:
                connected_users.pop(user_id, None)
            app.logger.info(f"User {user_id} (SID: {sid}) disconnected.")
            return user_id
    return None


@socketio.on("connect")
def handle_connect():
    sid = request.sid
    app.logger.info(f"Client connected: {sid}")

    if INTERNAL_API_MODE:
        _join_task_room(INTERNAL_API_USER_ID, sid)
        emit(
            "auth_response",
            {
                "success": True,
                "message": "Connected in internal API mode.",
                "user_id": INTERNAL_API_USER_ID,
            },
        )
        return

    emit("request_auth", {"message": "Please authenticate with your JWT token."})


@socketio.on("authenticate")
def handle_authenticate(data):
    token = (data or {}).get("token")
    sid = request.sid

    if INTERNAL_API_MODE:
        _join_task_room(INTERNAL_API_USER_ID, sid)
        emit(
            "auth_response",
            {
                "success": True,
                "message": "Connected in internal API mode.",
                "user_id": INTERNAL_API_USER_ID,
            },
        )
        return

    if not token:
        app.logger.warning(f"Auth attempt failed for SID {sid}: No token.")
        emit(
            "auth_response",
            {"success": False, "message": "Authentication token required."},
        )
        disconnect(sid)
        return

    try:
        with app.app_context():
            original_headers = request.headers
            try:
                request.headers = {"Authorization": f"Bearer {token}"}
                verify_jwt_in_request(optional=False)
                user_identity = get_jwt_identity()
                user_id = int(user_identity)
                app.logger.info(
                    f"SID {sid} authenticated successfully for user_id {user_id}."
                )

                _join_task_room(user_id, sid)
                emit(
                    "auth_response",
                    {
                        "success": True,
                        "message": "Authentication successful.",
                        "user_id": user_id,
                    },
                )
            except (JWTDecodeError, NoAuthorizationError, Exception) as e:
                app.logger.error(f"WebSocket JWT Auth failed for SID {sid}: {e}")
                error_message = "Invalid or expired token."
                if isinstance(e, JWTDecodeError):
                    error_message = "Invalid token format."
                elif isinstance(e, NoAuthorizationError):
                    error_message = "Authorization header missing or invalid."
                emit("auth_response", {"success": False, "message": error_message})
                disconnect(sid)
            finally:
                request.headers = original_headers
    except Exception as e:
        app.logger.error(
            f"Error during WebSocket auth for SID {sid}: {e}", exc_info=True
        )
        emit(
            "auth_response",
            {"success": False, "message": "Internal authentication error."},
        )
        disconnect(sid)


@socketio.on("disconnect")
def handle_disconnect():
    sid = request.sid
    user_id = _remove_connected_sid(sid)
    if user_id is None:
        app.logger.info(f"Unauthenticated client disconnected: {sid}")


def emit_task_update(user_id: int, task_data: dict):
    socketio.emit("task_update", task_data, room=f"user_{user_id}")


def _safe_int(value):
    try:
        if value in (None, ""):
            return 0
        return int(value)
    except (TypeError, ValueError):
        return 0


def _safe_float(value):
    try:
        if value in (None, ""):
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _get_search_cover_cache_file(novel_id: str) -> str:
    return os.path.join(settings.SEARCH_COVER_CACHE_PATH, f"{novel_id}.jpg")


def _has_local_search_cover(cover_url: Optional[str], cache_entry: Optional[SearchCacheEntry]) -> bool:
    if cache_entry and cache_entry.local_cover_path:
        return True
    return bool(cover_url and cover_url.startswith("/api/search-cover/"))


def _is_locally_cached_search_result(novel_info: dict, cache_entry: Optional[SearchCacheEntry]) -> bool:
    chapters_in_db = _safe_int(novel_info.get("chapters_in_db"))
    cover_url = novel_info.get("cover_image_url")
    return chapters_in_db > 0 or _has_local_search_cover(cover_url, cache_entry)


def _compute_local_heat_score(
    *,
    bookshelf_count: int,
    heat_score: float,
    search_hits: int,
    chapters_in_db: int,
    is_ready: bool,
    is_cached: bool,
) -> int:
    effective_bookshelf = math.log1p(max(bookshelf_count, 0)) * 100
    effective_heat = math.log1p(max(heat_score, 0.0)) * 40
    effective_search_hits = min(max(search_hits, 0), 8) * 12
    effective_chapters = min(max(chapters_in_db, 0), 80) * 3
    readiness_bonus = 120 if is_ready else 0
    cache_bonus = 40 if is_cached else 0

    return round(
        effective_bookshelf
        + effective_heat
        + effective_search_hits
        + effective_chapters
        + readiness_bonus
        + cache_bonus
    )


_SEARCH_SORT_FIELDS = {
    "relevance",
    "local_heat_score",
    "bookshelf_count",
    "chapters_in_db",
    "is_cached",
    "is_ready",
    "title",
}


def _resolve_search_sort_value(item: dict, sort_field: str):
    if sort_field == "title":
        return (item.get("title") or "").strip().lower()
    if sort_field in {"is_cached", "is_ready"}:
        return 1 if item.get(sort_field) else 0
    return item.get(sort_field) or 0


def _sort_formatted_search_results(results, sort_field: str, sort_order: str):
    original_positions = {
        str(item.get("id")): index for index, item in enumerate(results)
    }
    direction = -1 if sort_order == "desc" else 1

    def compare(left: dict, right: dict):
        left_value = _resolve_search_sort_value(left, sort_field)
        right_value = _resolve_search_sort_value(right, sort_field)

        if isinstance(left_value, str) or isinstance(right_value, str):
            if left_value < right_value:
                primary = -1
            elif left_value > right_value:
                primary = 1
            else:
                primary = 0
        else:
            primary = (left_value > right_value) - (left_value < right_value)

        if primary != 0:
            return primary * direction

        ready_diff = int(bool(right.get("is_ready"))) - int(bool(left.get("is_ready")))
        if ready_diff != 0:
            return ready_diff

        chapter_diff = _safe_int(right.get("chapters_in_db")) - _safe_int(left.get("chapters_in_db"))
        if chapter_diff != 0:
            return chapter_diff

        return original_positions.get(str(left.get("id")), 0) - original_positions.get(str(right.get("id")), 0)

    return sorted(results, key=cmp_to_key(compare))


def _build_safe_novel_name(novel_title: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "_", novel_title or "")


def _build_novel_status_paths(novel_id: int, novel_title: Optional[str]):
    if not novel_title:
        return None, None

    safe_book_name = _build_safe_novel_name(novel_title)
    safe_book_id = re.sub(r"[^a-zA-Z0-9_]", "_", str(novel_id))
    status_path_base = current_app.config.get("NOVEL_STATUS_PATH")
    if not status_path_base:
        return None, None

    status_folder = os.path.abspath(os.path.join(status_path_base, f"{safe_book_id}_{safe_book_name}"))
    status_file = os.path.join(status_folder, f"chapter_status_{novel_id}.json")
    return status_folder, status_file


def _novel_status_has_errors(novel_id: int, novel_title: Optional[str]) -> bool:
    _, status_file = _build_novel_status_paths(novel_id, novel_title)
    if not status_file or not os.path.isfile(status_file):
        return False

    try:
        with open(status_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        downloaded = data.get("downloaded", {}) if isinstance(data, dict) else {}
        for chapter_data in downloaded.values():
            if (
                isinstance(chapter_data, list)
                and len(chapter_data) == 2
                and isinstance(chapter_data[1], str)
                and "Error" in chapter_data[1]
            ):
                return True
    except Exception as e:
        current_app.logger.warning(f"Failed to inspect chapter status file for novel {novel_id}: {e}")

    return False


def _cleanup_novel_related_files(novel_id: int, novel_title: Optional[str]):
    if not novel_title:
        return

    safe_book_name = _build_safe_novel_name(novel_title)
    safe_book_id = re.sub(r"[^a-zA-Z0-9_]", "_", str(novel_id))

    save_path_base = current_app.config.get("NOVEL_SAVE_PATH")
    if save_path_base:
        for extension in ("epub", "txt", "pdf"):
            file_path = os.path.abspath(os.path.join(save_path_base, f"{safe_book_name}.{extension}"))
            if file_path.startswith(os.path.abspath(save_path_base)) and os.path.isfile(file_path):
                os.remove(file_path)

    status_path_base = current_app.config.get("NOVEL_STATUS_PATH")
    if status_path_base:
        status_folder, _ = _build_novel_status_paths(novel_id, novel_title)
        if status_folder and status_folder.startswith(os.path.abspath(status_path_base)) and os.path.isdir(status_folder):
            shutil.rmtree(status_folder)

    wordcloud_path_base = current_app.config.get("WORDCLOUD_SAVE_PATH")
    if wordcloud_path_base:
        wordcloud_file = os.path.abspath(os.path.join(wordcloud_path_base, f"wordcloud_{novel_id}.png"))
        if wordcloud_file.startswith(os.path.abspath(wordcloud_path_base)) and os.path.isfile(wordcloud_file):
            os.remove(wordcloud_file)


def _sync_search_cache_entries(search_results):
    if not search_results:
        return {}

    cache_ids = []
    for result in search_results:
        try:
            cache_ids.append(int(result.get("book_id")))
        except (TypeError, ValueError):
            continue

    existing_entries = {}
    if cache_ids:
        existing_entries = {
            str(entry.novel_id): entry
            for entry in SearchCacheEntry.query.filter(SearchCacheEntry.novel_id.in_(cache_ids)).all()
        }

    for result in search_results:
        book_id = result.get("book_id")
        if not book_id:
            continue

        book_id_str = str(book_id)
        entry = existing_entries.get(book_id_str)
        if not entry:
            entry = SearchCacheEntry(novel_id=int(book_id))
            _db.session.add(entry)
            existing_entries[book_id_str] = entry

        remote_cover_url = result.get("audio_thumb_uri") or result.get("thumb_url")
        cache_file = _get_search_cover_cache_file(book_id_str)

        entry.title = result.get("title") or entry.title or f"Novel {book_id_str}"
        entry.author = result.get("author")
        entry.description = result.get("abstract")
        entry.category = result.get("category")
        entry.remote_cover_url = remote_cover_url
        entry.local_cover_path = cache_file if os.path.exists(cache_file) else entry.local_cover_path
        entry.score = _safe_float(result.get("score"))
        entry.bookshelf_count = _safe_int(result.get("add_bookshelf_count"))
        entry.heat_score = _safe_float(result.get("toutiao_click_rate"))
        entry.search_hits = (getattr(entry, 'search_hits', 0) or 0) + 1
        entry.last_seen_at = datetime.utcnow()

    try:
        _db.session.commit()
    except Exception as cache_err:
        current_app.logger.warning(f"Failed to sync search cache entries: {cache_err}")
        _db.session.rollback()

    return existing_entries


def _normalize_search_query(query: str) -> str:
    return re.sub(r"\s+", " ", (query or "").strip().lower())


def _load_query_cache(normalized_query: str, requested_count: int):
    cache_ttl_seconds = int(os.getenv("SEARCH_QUERY_CACHE_TTL_SECONDS", 1800))
    cache_entry = _db.session.query(SearchQueryCacheEntry).filter_by(query=normalized_query).first()
    if not cache_entry:
        return None

    if not cache_entry.updated_at or (datetime.utcnow() - cache_entry.updated_at).total_seconds() > cache_ttl_seconds:
        return None

    try:
        cached_ids = json.loads(cache_entry.result_ids_json or "[]")
        if not isinstance(cached_ids, list):
            return None
    except Exception:
        return None

    if requested_count > len(cached_ids) and cache_entry.has_more:
        return None

    if not cached_ids:
        return {"results": [], "has_more": False, "next_offset": None}

    cache_rows = {
        str(row.novel_id): row
        for row in SearchCacheEntry.query.filter(SearchCacheEntry.novel_id.in_(cached_ids)).all()
    }

    cached_results = []
    for novel_id in cached_ids[:requested_count]:
        row = cache_rows.get(str(novel_id))
        if not row:
            continue
        cached_results.append(
            {
                "book_id": str(row.novel_id),
                "title": row.title,
                "author": row.author,
                "abstract": row.description,
                "category": row.category,
                "score": row.score,
                "add_bookshelf_count": row.bookshelf_count,
                "toutiao_click_rate": row.heat_score,
                "audio_thumb_uri": row.remote_cover_url,
                "thumb_url": row.remote_cover_url,
            }
        )

    expected_count = min(requested_count, len(cached_ids))
    if len(cached_results) < expected_count:
        return None

    cache_entry.hits = (cache_entry.hits or 0) + 1
    _db.session.commit()
    return {
        "results": cached_results,
        "has_more": bool(cache_entry.has_more and cache_entry.next_offset is not None),
        "next_offset": cache_entry.next_offset,
    }


def _save_query_cache(normalized_query: str, aggregated_results, has_more: bool, next_offset: Optional[int]):
    valid_ids = []
    for result in aggregated_results:
        book_id = result.get("book_id")
        if not book_id:
            continue
        try:
            valid_ids.append(int(book_id))
        except (TypeError, ValueError):
            continue

    cache_entry = _db.session.query(SearchQueryCacheEntry).filter_by(query=normalized_query).first()
    if not cache_entry:
        cache_entry = SearchQueryCacheEntry(query=normalized_query, result_ids_json="[]")
        _db.session.add(cache_entry)

    cache_entry.result_ids_json = json.dumps(valid_ids, ensure_ascii=False)
    cache_entry.has_more = bool(has_more)
    cache_entry.next_offset = next_offset if has_more else None
    cache_entry.updated_at = datetime.utcnow()

    try:
        _db.session.commit()
    except Exception as cache_err:
        current_app.logger.warning(f"Failed to save query cache for '{normalized_query}': {cache_err}")
        _db.session.rollback()


# --- API Endpoints ---
def _download_cover_from_url(cover_url: str, novel_id: str, book_name: str) -> Optional[str]:
    """下载封面图片到本地
    
    Args:
        cover_url: 封面图片URL
        novel_id: 小说ID
        book_name: 小说名称
        
    Returns:
        本地封面URL或None
    """
    if not cover_url:
        return None
        
    try:
        import requests
        from pathlib import Path
        
        logger = current_app.logger
        cfg = GlobalContext.get_config()
        
        # 获取状态文件夹路径
        status_folder = cfg.status_folder_path(book_name, novel_id)
        status_folder.mkdir(parents=True, exist_ok=True)
        
        # 安全文件名
        safe_book_name = re.sub(r'[\\/*?:"<>|]', "_", book_name)
        cover_path = status_folder / f"{safe_book_name}.jpg"
        
        # 如果已存在，直接返回
        if cover_path.exists():
            return f"/api/novels/{novel_id}/cover"
        
        # 下载封面
        response = requests.get(cover_url, timeout=10, verify=False)
        response.raise_for_status()
        
        # 保存封面
        cover_path.write_bytes(response.content)
        logger.info(f"Downloaded cover for novel {novel_id} from {cover_url}")
        
        return f"/api/novels/{novel_id}/cover"
        
    except Exception as e:
        current_app.logger.warning(f"Failed to download cover for {novel_id}: {e}")
        return None


@app.get("/api/search-cover/<int:novel_id>")
def get_search_cover(novel_id):
    cache_entry = SearchCacheEntry.query.get(novel_id)
    if not cache_entry:
        return jsonify(error="Search cover not found"), 404

    local_cover_path = cache_entry.local_cover_path or _get_search_cover_cache_file(str(novel_id))
    if local_cover_path and os.path.isfile(local_cover_path):
        return send_file(local_cover_path, mimetype="image/jpeg")

    remote_cover_url = (cache_entry.remote_cover_url or "").strip()
    if not remote_cover_url:
        return jsonify(error="Remote search cover unavailable"), 404

    parsed_url = urlparse(remote_cover_url)
    if parsed_url.scheme not in {"http", "https"}:
        return jsonify(error="Invalid cover URL"), 400

    try:
        import requests

        response = requests.get(
            remote_cover_url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://fanqienovel.com/",
                "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
            },
            timeout=15,
            verify=False,
        )
        response.raise_for_status()

        os.makedirs(settings.SEARCH_COVER_CACHE_PATH, exist_ok=True)
        with open(local_cover_path, "wb") as f:
            f.write(response.content)

        cache_entry.local_cover_path = local_cover_path
        _db.session.commit()
        return send_file(local_cover_path, mimetype=response.headers.get("Content-Type", "image/jpeg"))
    except Exception as e:
        current_app.logger.warning(
            f"Failed to cache search cover for {novel_id} from {remote_cover_url}: {e}"
        )
        _db.session.rollback()
        return jsonify(error="Failed to load search cover"), 502


@app.route("/api/search", methods=["GET"])
def search_novels_api():
    logger = current_app.logger
    query = (request.args.get("query") or "").strip()
    if not query:
        return jsonify(error="Missing 'query' parameter"), 400

    try:
        page = max(1, int(request.args.get("page", 1)))
        per_page = max(1, min(50, int(request.args.get("per_page", 30))))
        offset_param = request.args.get("offset")
        search_offset = (
            int(offset_param)
            if offset_param is not None and str(offset_param).strip() != ""
            else None
        )
        if search_offset is not None and search_offset < 0:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify(error="Invalid 'page', 'per_page' or 'offset' parameter"), 400

    sort_field = (request.args.get("sort") or "relevance").strip() or "relevance"
    sort_order = (request.args.get("order") or "desc").strip().lower() or "desc"
    if sort_field not in _SEARCH_SORT_FIELDS:
        return jsonify(error="Invalid 'sort' parameter"), 400
    if sort_order not in {"asc", "desc"}:
        return jsonify(error="Invalid 'order' parameter"), 400

    use_backend_sort = sort_field != "relevance"
    if use_backend_sort:
        search_offset = None

    # 新参数: 是否预下载封面 (默认关闭以提升响应速度)
    preload_covers = request.args.get("preload_covers", "false").lower() == "true"
    
    normalized_query = _normalize_search_query(query)

    logger.info(
        f"Search request: '{query}' (page={page}, per_page={per_page}, offset={search_offset}, sort={sort_field}, order={sort_order}, preload_covers={preload_covers})"
    )

    if not DOWNLOADER_AVAILABLE:
        logger.error("Downloader components unavailable for search.")
        return jsonify(error="Search functionality unavailable"), 503

    try:
        if not GlobalContext.is_initialized():
            logger.warning(
                "Downloader context not initialized for search, attempting init..."
            )
            GlobalContext.initialize(get_downloader_config(), logger)

        network_client = NetworkClient()
        max_upstream_pages = 12

        def collect_search_results(start_offset: int, needed_count: int):
            aggregated_results = []
            seen_book_ids = set()
            current_offset = start_offset
            upstream_has_more = True
            next_offset = None
            fetch_rounds = 0

            while len(aggregated_results) < needed_count and fetch_rounds < max_upstream_pages:
                search_page = network_client.search_book(query, offset=current_offset)
                upstream_page_results = search_page.get("results", [])
                upstream_has_more = bool(search_page.get("has_more"))
                next_offset = search_page.get("next_offset")

                if not upstream_page_results:
                    break

                added_count = 0
                for res in upstream_page_results:
                    book_id = res.get("book_id")
                    if not book_id:
                        continue
                    book_id_str = str(book_id)
                    if book_id_str in seen_book_ids:
                        continue
                    seen_book_ids.add(book_id_str)
                    aggregated_results.append(res)
                    added_count += 1

                fetch_rounds += 1

                if (
                    not upstream_has_more
                    or next_offset is None
                    or next_offset == current_offset
                    or added_count == 0
                ):
                    break

                current_offset = next_offset

            return aggregated_results, upstream_has_more, next_offset, fetch_rounds

        cache_sync_source = []
        page_results = []
        aggregated_results = []
        has_more = False
        next_offset = None
        next_page = None
        fetch_rounds = 0

        if search_offset is not None:
            page_results, has_more, next_offset, fetch_rounds = collect_search_results(
                search_offset, per_page
            )
            cache_sync_source = page_results
            next_page = page + 1 if has_more else None
            logger.info(
                f"Search for '{query}' fetched {len(page_results)} unique results from offset {search_offset} across {fetch_rounds} upstream requests."
            )
        else:
            requested_result_count = page * per_page
            requested_cache_count = requested_result_count if not use_backend_sort else 10**9
            needed_count = requested_result_count if not use_backend_sort else 10**9
            cached_query_result = None
            if not preload_covers:
                cached_query_result = _load_query_cache(normalized_query, requested_cache_count)

            if cached_query_result is not None:
                aggregated_results = cached_query_result["results"]
                next_offset = cached_query_result["next_offset"]
                has_more = cached_query_result["has_more"]
                page_results = aggregated_results[(page - 1) * per_page : page * per_page]
                cache_sync_source = aggregated_results if use_backend_sort else page_results
                fetch_rounds = 0
                logger.info(
                    f"Search for '{query}' served from query cache with {len(page_results)} results."
                )
            else:
                aggregated_results, upstream_has_more, next_offset, fetch_rounds = collect_search_results(
                    0, needed_count
                )
                start_index = (page - 1) * per_page
                end_index = start_index + per_page
                page_results = aggregated_results[start_index:end_index]
                cache_sync_source = aggregated_results
                has_more = len(aggregated_results) > end_index or upstream_has_more
                if not preload_covers:
                    _save_query_cache(normalized_query, aggregated_results, upstream_has_more, next_offset)
                logger.info(
                    f"Search for '{query}' aggregated {len(aggregated_results)} unique results across {fetch_rounds} upstream requests; returning {len(page_results)} results for page {page}."
                )

            next_page = page + 1 if has_more else None

        search_cache_entries = _sync_search_cache_entries(cache_sync_source)

        # 获取本轮需要补充本地信息的搜索结果 ID
        search_ids = [res.get("book_id") for res in cache_sync_source if res.get("book_id")]
        db_search_ids = []
        for search_id in search_ids:
            try:
                db_search_ids.append(int(search_id))
            except (TypeError, ValueError):
                logger.warning(f"Skipping invalid book_id from search result: {search_id}")
        
        # 从数据库查询已存在的小说信息（封面、章节数、就绪状态）
        existing_novels = {}
        if db_search_ids:
            # 创建子查询统计章节数
            chapter_count_subq = (
                _db.session.query(
                    Chapter.novel_id,
                    func.count(Chapter.id).label('chapters_in_db')  # pylint: disable=not-callable
                )
                .filter(Chapter.novel_id.in_(db_search_ids))
                .group_by(Chapter.novel_id)
                .subquery()
            )
            
            # 计算 is_ready 状态
            # 就绪条件：已下载章节数 > 100 或 已下载章节数 > 总章节数 / 3
            is_ready_expr = case(
                (chapter_count_subq.c.chapters_in_db > 100, True),
                (
                    and_(
                        Novel.total_chapters.isnot(None),
                        Novel.total_chapters > 0,
                        chapter_count_subq.c.chapters_in_db > Novel.total_chapters / 3
                    ),
                    True
                ),
                else_=False
            )
            
            # 查询小说及其章节数和就绪状态
            novels_query = (
                _db.session.query(
                    Novel,
                    func.coalesce(chapter_count_subq.c.chapters_in_db, 0).label('chapters_in_db'),
                    is_ready_expr.label('is_ready')
                )
                .filter(Novel.id.in_(db_search_ids))
                .outerjoin(chapter_count_subq, Novel.id == chapter_count_subq.c.novel_id)
                .all()
            )
            
            existing_novels = {
                str(item[0].id): {
                    'cover_image_url': item[0].cover_image_url,
                    'chapters_in_db': int(item[1]),
                    'is_ready': bool(item[2]),
                    'total_chapters': item[0].total_chapters
                }
                for item in novels_query
            }
            logger.debug(f"Found {len(existing_novels)} novels in database")

        # 预下载当前页封面图片
        if preload_covers:
            downloaded_count = 0
            for res in page_results:
                book_id = res.get("book_id")
                book_id_str = str(book_id) if book_id else None
                
                # 跳过已有本地封面的小说
                if not book_id or (book_id_str in existing_novels and existing_novels[book_id_str].get('cover_image_url')):
                    continue
                
                thumb_url = res.get("thumb_url")
                if thumb_url:
                    title = res.get("title") or f"Novel {book_id}"
                    local_cover = _download_cover_from_url(thumb_url, str(book_id), title)
                    if local_cover:
                        # 更新或创建记录
                        if book_id_str in existing_novels:
                            existing_novels[book_id_str]['cover_image_url'] = local_cover
                        else:
                            existing_novels[book_id_str] = {
                                'cover_image_url': local_cover,
                                'chapters_in_db': 0,
                                'is_ready': False,
                                'total_chapters': None
                            }
                        downloaded_count += 1
                        
                        # 更新数据库（如果小说已存在）
                        try:
                            novel = Novel.query.get(int(book_id))
                            if novel:
                                novel.cover_image_url = local_cover
                                _db.session.commit()
                        except Exception as db_err:
                            logger.warning(f"Failed to update cover in DB for {book_id}: {db_err}")
                            _db.session.rollback()
            
            if downloaded_count > 0:
                logger.info(f"Pre-downloaded {downloaded_count} covers for current search page")

        format_source_results = cache_sync_source if use_backend_sort else page_results
        formatted_results = []
        for res in format_source_results:
            book_id = res.get("book_id")
            if book_id is None:
                continue
            
            book_id_str = str(book_id)
            novel_info = existing_novels.get(book_id_str, {})
            cache_entry = search_cache_entries.get(book_id_str)
            remote_cover = res.get("audio_thumb_uri") or res.get("thumb_url")
            cached_cover_url = (
                f"/api/search-cover/{book_id_str}"
                if cache_entry and (cache_entry.remote_cover_url or cache_entry.local_cover_path)
                else None
            )

            bookshelf_count = _safe_int(res.get("add_bookshelf_count"))
            heat_score = _safe_float(res.get("toutiao_click_rate"))
            chapters_in_db = _safe_int(novel_info.get('chapters_in_db', 0))
            is_ready = bool(novel_info.get('is_ready', False))
            is_cached = _is_locally_cached_search_result(novel_info, cache_entry)
            local_heat_score = _compute_local_heat_score(
                bookshelf_count=bookshelf_count,
                heat_score=heat_score,
                search_hits=(cache_entry.search_hits if cache_entry else 0),
                chapters_in_db=chapters_in_db,
                is_ready=is_ready,
                is_cached=is_cached,
            )

            result = {
                "id": book_id_str,
                "title": res.get("title"),
                "author": res.get("author"),
                "cover": novel_info.get('cover_image_url') or cached_cover_url or remote_cover,
                "description": res.get("abstract"),
                "category": res.get("category"),
                "score": _safe_float(res.get("score")),
                "bookshelf_count": bookshelf_count,
                "heat_score": heat_score,
                "local_heat_score": local_heat_score,
                "chapters_in_db": chapters_in_db,
                "is_ready": is_ready,
                "is_cached": is_cached,
                "total_chapters": novel_info.get('total_chapters'),
            }
            
            formatted_results.append(result)

        if use_backend_sort:
            sorted_results = _sort_formatted_search_results(formatted_results, sort_field, sort_order)
            start_index = (page - 1) * per_page
            end_index = start_index + per_page
            formatted_results = sorted_results[start_index:end_index]
            has_more = len(sorted_results) > end_index or has_more
            next_page = page + 1 if has_more else None
            next_offset = None

        return jsonify({
            "results": formatted_results,
            "page": page,
            "per_page": per_page,
            "has_more": has_more,
            "next_page": next_page,
            "next_offset": next_offset if (has_more and not use_backend_sort) else None,
            "sort": sort_field,
            "order": sort_order,
        }), 200
    except Exception as e:
        logger.error(f"Error during novel search for '{query}': {e}", exc_info=True)
        return jsonify(error="Internal server error during search"), 500


@app.route("/api/novels", methods=["POST"])
def add_novel_and_crawl():
    logger = current_app.logger
    user_id = 1  # Fixed user ID for internal API
    data = request.get_json()
    if not data or "novel_id" not in data:
        return jsonify(error="Missing 'novel_id' in request body"), 400

    try:
        novel_id_int = int(data["novel_id"])
    except (ValueError, TypeError):
        return jsonify(error="'novel_id' must be a valid integer"), 400

    # 可选参数: max_chapters 用于限制下载章节数量（如预览模式）
    max_chapters = data.get("max_chapters", None)
    if max_chapters is not None:
        try:
            max_chapters = int(max_chapters)
            if max_chapters < 1:
                return jsonify(error="'max_chapters' must be a positive integer"), 400
        except (ValueError, TypeError):
            return jsonify(error="'max_chapters' must be a valid integer"), 400

    logger.info(f"User {user_id} requested add/crawl for novel ID: {novel_id_int}" + 
                (f" (max_chapters: {max_chapters})" if max_chapters else ""))

    db_task_id = None
    try:
        internal_user = User.query.get(user_id)
        if not internal_user:
            logger.info(f"Internal API user {user_id} not found in DB, creating placeholder user.")
            internal_user = User(id=user_id, username="internal_api")
            internal_user.set_password(os.getenv("INTERNAL_API_PASSWORD", "internal-api-disabled"))
            _db.session.add(internal_user)

        # 检查 Novel 是否存在，如果不存在则创建基础记录
        novel = Novel.query.get(novel_id_int)
        if not novel:
            logger.info(f"Novel {novel_id_int} not found in DB, creating placeholder.")
            # 创建一个包含最少信息的 Novel 记录以满足外键约束
            novel = Novel(id=novel_id_int, title=f"Novel {novel_id_int}")
            _db.session.add(novel)
            # 注意：此时不 commit，让 User/Novel/DownloadTask 在同一个事务中提交

        # 检查是否已有进行中的任务
        existing_task = (
            DownloadTask.query.filter_by(user_id=user_id, novel_id=novel_id_int)
            .filter(
                DownloadTask.status.in_(
                    [TaskStatus.PENDING, TaskStatus.DOWNLOADING, TaskStatus.PROCESSING]
                )
            )
            .first()
        )
        if existing_task:
            logger.warning(
                f"User {user_id} task for novel {novel_id_int} already active (ID: {existing_task.id}, Status: {existing_task.status.name})"
            )
            return jsonify(
                error=f"Task is already active with status {existing_task.status.name}.",
                task=existing_task.to_dict(),
            ), 409  # Conflict

        # 创建 DownloadTask 记录
        new_db_task = DownloadTask(
            user_id=user_id,
            novel_id=novel_id_int,
            status=TaskStatus.PENDING,
            progress=0,
        )
        _db.session.add(new_db_task)

        # 在同一个事务中提交 Novel (如果是新建的) 和 DownloadTask
        _db.session.commit()
        db_task_id = new_db_task.id  # 在 commit 后获取 ID
        logger.info(
            f"Created DB task ID: {db_task_id} for novel {novel_id_int}, user {user_id}"
        )

    except Exception as db_err:
        _db.session.rollback()  # 出错时回滚
        logger.error(
            f"Failed to ensure Novel record or create DB task for novel {novel_id_int}: {db_err}",
            exc_info=True,
        )
        return jsonify(error="Failed to prepare task record in database"), 500

    try:
        # 准备任务参数
        task_kwargs = {
            "novel_id": novel_id_int,
            "user_id": user_id,
            "db_task_id": db_task_id,
        }
        if max_chapters is not None:
            task_kwargs["max_chapters"] = max_chapters

        celery_task = celery_app.send_task(
            "tasks.process_novel",
            kwargs=task_kwargs,
        )
        logger.info(f"Queued Celery task {celery_task.id} for DB Task {db_task_id}")

        new_db_task.celery_task_id = celery_task.id
        _db.session.commit()
        logger.info(f"Updated DB Task {db_task_id} with Celery ID {celery_task.id}")

        emit_task_update(user_id, new_db_task.to_dict())
        return jsonify(new_db_task.to_dict()), 202
    except Exception as e:
        logger.error(
            f"Failed to queue Celery task for DB Task {db_task_id}: {e}", exc_info=True
        )
        try:  # Cleanup preliminary DB task
            _db.session.delete(new_db_task)
            _db.session.commit()
        except:
            _db.session.rollback()
        return jsonify(error="Failed to queue background task"), 500


@app.route("/api/novels/<int:novel_id>", methods=["DELETE"])
def delete_novel(novel_id):
    logger = current_app.logger
    logger.info(f"Internal API requesting deletion for Novel ID: {novel_id}")

    try:
        novel = Novel.query.get(novel_id)
        if not novel:
            return jsonify(error="Novel not found"), 404

        active_tasks = (
            DownloadTask.query.filter_by(novel_id=novel_id)
            .filter(
                DownloadTask.status.in_(
                    [TaskStatus.PENDING, TaskStatus.DOWNLOADING, TaskStatus.PROCESSING]
                )
            )
            .all()
        )
        if active_tasks:
            return jsonify(error="该小说仍有进行中的任务，请先在任务管理中终止后再删除。"), 409

        related_tasks = DownloadTask.query.filter_by(novel_id=novel_id).all()
        deleted_task_ids = [task.id for task in related_tasks]
        related_user_ids = {task.user_id for task in related_tasks}
        for task in related_tasks:
            _db.session.delete(task)

        novel_title = novel.title
        _db.session.delete(novel)
        _db.session.commit()

        _cleanup_novel_related_files(novel_id, novel_title)

        for user_id in related_user_ids:
            for task_id in deleted_task_ids:
                emit_task_update(user_id, {"id": task_id, "deleted": True})

        logger.info(f"Deleted Novel {novel_id} and related tasks/resources.")
        return jsonify(message="Novel deleted successfully.")
    except Exception as e:
        _db.session.rollback()
        logger.error(f"Error deleting novel {novel_id}: {e}", exc_info=True)
        return jsonify(error="Failed to delete novel"), 500


@app.route("/api/novels", methods=["GET"])
def list_novels():
    """
    List novels with filtering, search and sorting.
    
    Query Parameters:
    - page: Page number (default: 1)
    - per_page: Items per page (default: 10, max: 50)
    - search: Search by title (partial match, case-insensitive)
    - tags: Filter by tags (comma-separated, e.g., "玄幻,都市")
    - status: Filter by status (e.g., "连载中", "已完结")
    - sort: Sort field (last_crawled_at, created_at, total_chapters, title, is_ready)
    - order: Sort order (asc, desc) - default: desc
    """
    logger = current_app.logger
    
    # Pagination parameters
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 10, type=int), 50)
    
    # Filter parameters
    search_query = request.args.get("search", "").strip()
    tags_filter = request.args.get("tags", "").strip()
    status_filter = request.args.get("status", "").strip()
    
    # Sort parameters
    sort_field = request.args.get("sort", "last_crawled_at").strip()
    sort_order = request.args.get("order", "desc").strip().lower()
    
    logger.info(
        f"Listing novels: page={page}, per_page={per_page}, "
        f"search='{search_query}', tags='{tags_filter}', status='{status_filter}', "
        f"sort={sort_field}, order={sort_order}"
    )
    
    try:
        # Create subquery to count chapters for each novel
        chapter_count_subq = (
            _db.session.query(
                Chapter.novel_id,
                func.count(Chapter.id).label('chapters_in_db')  # pylint: disable=not-callable
            )
            .group_by(Chapter.novel_id)
            .subquery()
        )
        
        # Calculate is_ready status:
        # 就绪条件：已下载章节数 > 100 或 已下载章节数 > 总章节数 / 3
        is_ready_expr = case(
            (chapter_count_subq.c.chapters_in_db > 100, True),
            (
                and_(
                    Novel.total_chapters.isnot(None),
                    Novel.total_chapters > 0,
                    chapter_count_subq.c.chapters_in_db > Novel.total_chapters / 3
                ),
                True
            ),
            else_=False
        ).label('is_ready')
        
        # Build main query with Novel, chapters_in_db, and is_ready
        query = (
            _db.session.query(
                Novel,
                func.coalesce(chapter_count_subq.c.chapters_in_db, 0).label('chapters_in_db'),
                is_ready_expr
            )
            .outerjoin(chapter_count_subq, Novel.id == chapter_count_subq.c.novel_id)
        )
        
        # Apply title search filter
        if search_query:
            query = query.filter(Novel.title.ilike(f"%{search_query}%"))
        
        # Apply tags filter (match any of the provided tags)
        if tags_filter:
            tags_list = [tag.strip() for tag in tags_filter.split(",") if tag.strip()]
            if tags_list:
                # Match novels that contain ANY of the specified tags
                tag_filters = [Novel.tags.ilike(f"%{tag}%") for tag in tags_list]
                query = query.filter(or_(*tag_filters))
        
        # Apply status filter
        if status_filter:
            query = query.filter(Novel.status == status_filter)
        
        # Apply sorting
        valid_sort_fields = {
            "last_crawled_at": Novel.last_crawled_at,
            "created_at": Novel.created_at,
            "total_chapters": Novel.total_chapters,
            "title": Novel.title,
            "is_ready": is_ready_expr,
        }
        
        if sort_field in valid_sort_fields:
            sort_column = valid_sort_fields[sort_field]
            
            # Handle NULL values for date fields - put them at the end
            if sort_field in ["last_crawled_at", "created_at"]:
                if sort_order == "asc":
                    query = query.order_by(
                        sort_column.is_(None),  # NULLs last
                        sort_column.asc()
                    )
                else:  # desc
                    query = query.order_by(
                        sort_column.is_(None),  # NULLs last
                        sort_column.desc()
                    )
            else:
                # For other fields, simple sorting
                if sort_order == "asc":
                    query = query.order_by(sort_column.asc())
                else:
                    query = query.order_by(sort_column.desc())
        else:
            # Default sorting if invalid sort field provided
            query = query.order_by(
                Novel.last_crawled_at.is_(None),
                Novel.last_crawled_at.desc(),
                Novel.created_at.desc(),
            )
        
        # Execute pagination
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Build response data with is_ready and chapters_in_db fields
        novels_data = [
            {
                "id": str(item[0].id),
                "title": item[0].title,
                "author": item[0].author,
                "status": item[0].status,
                "tags": item[0].tags,
                "total_chapters": item[0].total_chapters,
                "chapters_in_db": int(item[1]),
                "is_ready": bool(item[2]),
                "last_crawled_at": item[0].last_crawled_at.isoformat()
                if item[0].last_crawled_at
                else None,
                "created_at": item[0].created_at.isoformat() if item[0].created_at else None,
                "cover_image_url": item[0].cover_image_url,
                "description": item[0].description,
            }
            for item in pagination.items
        ]
        
        return jsonify(
            {
                "novels": novels_data,
                "total": pagination.total,
                "page": pagination.page,
                "pages": pagination.pages,
                "per_page": pagination.per_page,
                "filters": {
                    "search": search_query,
                    "tags": tags_filter,
                    "status": status_filter,
                    "sort": sort_field,
                    "order": sort_order,
                },
            }
        )
    except Exception as e:
        logger.error(f"Error listing novels: {e}", exc_info=True)
        return jsonify(error="Database error fetching novels"), 500


@app.route("/api/novels/<int:novel_id>", methods=["GET"])
def get_novel_details(novel_id):
    logger = current_app.logger
    logger.info(f"Fetching details for novel ID: {novel_id}")
    try:
        novel = Novel.query.get_or_404(novel_id)
        chapter_count = Chapter.query.filter_by(novel_id=novel.id).count()
        
        # Calculate is_ready status
        # 就绪条件：已下载章节数 > 100 或 已下载章节数 > 总章节数 / 3
        is_ready = False
        if chapter_count > 100:
            is_ready = True
        elif novel.total_chapters and novel.total_chapters > 0 and chapter_count > novel.total_chapters / 3:
            is_ready = True
        
        return jsonify(
            {
                "id": str(novel.id),
                "title": novel.title,
                "author": novel.author,
                "description": novel.description,
                "status": novel.status,
                "tags": novel.tags,
                "total_chapters": novel.total_chapters,
                "chapters_in_db": chapter_count,
                "is_ready": is_ready,
                "last_crawled_at": novel.last_crawled_at.isoformat()
                if novel.last_crawled_at
                else None,
                "created_at": novel.created_at.isoformat()
                if novel.created_at
                else None,
                "cover_image_url": novel.cover_image_url,
            }
        )
    except HTTPException as e:
        if e.code == 404:
            return jsonify(error=f"Novel with ID {novel_id} not found"), 404
        raise e
    except Exception as e:
        logger.error(f"Error fetching novel details {novel_id}: {e}", exc_info=True)
        return jsonify(error="Database error fetching novel details"), 500


@app.route("/api/novels/<int:novel_id>/ready", methods=["GET"])
def check_novel_ready(novel_id):
    """
    Check if a novel is ready for reading.
    
    A novel is considered ready if:
    - Total chapters > 100, OR
    - Downloaded chapters > total_chapters / 3
    
    Returns:
        {
            "novel_id": "123456",
            "is_ready": true,
            "chapters_in_db": 150,
            "total_chapters": 200,
            "ready_reason": "Has more than 100 chapters"
        }
    """
    logger = current_app.logger
    logger.info(f"Checking ready status for novel ID: {novel_id}")
    
    try:
        novel = Novel.query.get_or_404(novel_id)
        chapter_count = Chapter.query.filter_by(novel_id=novel.id).count()
        
        # Calculate is_ready status and reason
        # 就绪条件：已下载章节数 > 100 或 已下载章节数 > 总章节数 / 3
        is_ready = False
        ready_reason = "Not ready"
        
        if chapter_count == 0:
            ready_reason = "No chapters downloaded yet"
        elif chapter_count > 100:
            is_ready = True
            ready_reason = f"Downloaded more than 100 chapters ({chapter_count} chapters)"
        elif novel.total_chapters and novel.total_chapters > 0 and chapter_count > novel.total_chapters / 3:
            is_ready = True
            ready_reason = f"Downloaded {chapter_count} of {novel.total_chapters} chapters (>{novel.total_chapters/3:.0f} required)"
        else:
            if novel.total_chapters:
                ready_reason = f"Only {chapter_count} of {novel.total_chapters} chapters downloaded (need >100 or >{novel.total_chapters/3:.0f})"
            else:
                ready_reason = f"Only {chapter_count} chapters downloaded (need >100 chapters)"
        
        return jsonify(
            {
                "novel_id": str(novel.id),
                "title": novel.title,
                "is_ready": is_ready,
                "chapters_in_db": chapter_count,
                "total_chapters": novel.total_chapters,
                "ready_reason": ready_reason,
            }
        )
    except HTTPException as e:
        if e.code == 404:
            return jsonify(error=f"Novel with ID {novel_id} not found"), 404
        raise e
    except Exception as e:
        logger.error(f"Error checking ready status for novel {novel_id}: {e}", exc_info=True)
        return jsonify(error="Database error checking novel ready status"), 500


@app.route("/api/novels/<int:novel_id>/chapters", methods=["GET"])
def get_novel_chapters(novel_id):
    logger = current_app.logger
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 50, type=int), 200)
    logger.info(
        f"Fetching chapters for novel {novel_id}: page={page}, per_page={per_page}"
    )
    try:
        if not _db.session.query(Novel.id).filter_by(id=novel_id).scalar():
            abort(404, description=f"Novel with ID {novel_id} not found.")

        pagination = (
            Chapter.query.filter_by(novel_id=novel_id)
            .order_by(Chapter.chapter_index)
            .paginate(page=page, per_page=per_page, error_out=False)
        )
        chapters_data = [
            {
                "id": str(c.id),
                "index": c.chapter_index,
                "title": c.title,
                "fetched_at": c.fetched_at.isoformat() if c.fetched_at else None,
            }
            for c in pagination.items
        ]
        return jsonify(
            {
                "chapters": chapters_data,
                "total": pagination.total,
                "page": pagination.page,
                "pages": pagination.pages,
                "per_page": pagination.per_page,
                "novel_id": str(novel_id),
            }
        )
    except HTTPException as e:
        if e.code == 404:
            return jsonify(error=getattr(e, "description", "Not Found")), 404
        raise e
    except Exception as e:
        logger.error(
            f"Error fetching chapters for novel {novel_id}: {e}", exc_info=True
        )
        return jsonify(error="Database error fetching chapters"), 500


@app.route("/api/novels/<int:novel_id>/chapters/<int:chapter_id>", methods=["GET"])
def get_chapter_content(novel_id, chapter_id):
    logger = current_app.logger
    logger.info(f"Fetching content for novel {novel_id}, chapter {chapter_id}")
    try:
        chapter = Chapter.query.filter_by(
            novel_id=novel_id, id=chapter_id
        ).first_or_404()
        prev_chapter = (
            Chapter.query.filter(
                Chapter.novel_id == novel_id,
                Chapter.chapter_index < chapter.chapter_index,
            )
            .order_by(Chapter.chapter_index.desc())
            .first()
        )
        next_chapter = (
            Chapter.query.filter(
                Chapter.novel_id == novel_id,
                Chapter.chapter_index > chapter.chapter_index,
            )
            .order_by(Chapter.chapter_index.asc())
            .first()
        )
        return jsonify(
            {
                "id": str(chapter.id),
                "novel_id": str(chapter.novel_id),
                "index": chapter.chapter_index,
                "title": chapter.title,
                "content": chapter.content,
                "prev_chapter_id": str(prev_chapter.id) if prev_chapter else None,
                "prev_chapter_title": prev_chapter.title if prev_chapter else None,
                "next_chapter_id": str(next_chapter.id) if next_chapter else None,
                "next_chapter_title": next_chapter.title if next_chapter else None,
            }
        )
    except HTTPException as e:
        if e.code == 404:
            return jsonify(
                error=f"Chapter {chapter_id} for novel {novel_id} not found"
            ), 404
        raise e
    except Exception as e:
        logger.error(
            f"Error fetching chapter content {novel_id}/{chapter_id}: {e}",
            exc_info=True,
        )
        return jsonify(error="Database error fetching chapter content"), 500


@app.route("/api/novels/<int:novel_id>/cover", methods=["GET"])
def get_novel_cover(novel_id):
    logger = current_app.logger
    novel = Novel.query.get(novel_id)
    if not novel or not novel.title:
        abort(404, description="Novel not found or missing title")

    if not DOWNLOADER_AVAILABLE:
        abort(503, description="Cover functionality unavailable (downloader missing)")

    try:
        if not GlobalContext.is_initialized():
            GlobalContext.initialize(get_downloader_config(), logger)

        cfg = GlobalContext.get_config()
        status_folder = cfg.status_folder_path(novel.title, str(novel.id))
        safe_book_name = re.sub(r'[\\/*?:"<>|]', "_", novel.title)
        cover_path = status_folder / f"{safe_book_name}.jpg"

        if cover_path.is_file():
            return send_file(str(cover_path), mimetype="image/jpeg")
        else:
            abort(404, description="Cover image not found locally")
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error serving cover for novel {novel_id}: {e}", exc_info=True)
        abort(500, description="Error serving cover image")


@app.route("/api/tasks/list", methods=["GET"])
def list_user_tasks():
    logger = current_app.logger
    logger.info("Fetching all tasks (internal API)")
    try:
        tasks = (
            DownloadTask.query
            .options(_db.joinedload(DownloadTask.novel))
            .order_by(DownloadTask.created_at.desc())
            .all()
        )
        return jsonify(tasks=[task.to_dict() for task in tasks])
    except Exception as e:
        logger.error(f"Error fetching all tasks: {e}", exc_info=True)
        return jsonify(error="Database error fetching task list"), 500


@app.route("/api/tasks/<int:db_task_id>/terminate", methods=["POST"])
def terminate_task(db_task_id):
    logger = current_app.logger
    logger.info(f"Internal API requesting termination for DB Task ID: {db_task_id}")
    try:
        task = DownloadTask.query.filter_by(id=db_task_id).first()
        if not task:
            return jsonify(error="Task not found"), 404
        
        user_id = task.user_id  # Get the real user_id for WebSocket notifications

        if not task.celery_task_id and task.status in [
            TaskStatus.PENDING,
            TaskStatus.DOWNLOADING,
            TaskStatus.PROCESSING,
        ]:
            task.status = TaskStatus.FAILED
            task.message = "No Celery task ID found to terminate."
            _db.session.commit()
            emit_task_update(user_id, task.to_dict())
            return jsonify(error="Task has no associated process ID"), 400

        if task.status in [
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.TERMINATED,
        ]:
            return jsonify(
                message="Task is already finished.", task=task.to_dict()
            ), 200

        logger.info(
            f"Terminating Celery task {task.celery_task_id} for DB Task {db_task_id}"
        )
        celery_app.control.revoke(task.celery_task_id, terminate=True, signal="SIGTERM")
        task.status = TaskStatus.TERMINATED
        task.progress = 0
        task.message = "Task terminated by user."
        _db.session.commit()
        logger.info(f"DB Task {db_task_id} status updated to TERMINATED.")
        emit_task_update(user_id, task.to_dict())
        return jsonify(message="Task termination signal sent.", task=task.to_dict())
    except Exception as e:
        _db.session.rollback()
        logger.error(f"Error terminating task {db_task_id}: {e}", exc_info=True)
        return jsonify(error="Failed to terminate task"), 500


@app.route("/api/tasks/<int:db_task_id>", methods=["DELETE"])
def delete_task(db_task_id):
    logger = current_app.logger
    logger.info(f"Internal API requesting deletion for DB Task ID: {db_task_id}")
    try:
        task = DownloadTask.query.filter_by(id=db_task_id).first()
        if not task:
            return jsonify(error="Task not found"), 404
        
        user_id = task.user_id  # Get the real user_id for WebSocket notifications
        novel_id = task.novel_id
        novel = task.novel

        celery_id_to_forget = task.celery_task_id
        _db.session.delete(task)
        _db.session.commit()
        logger.info(f"Deleted DB Task {db_task_id} for user {user_id}.")

        if celery_id_to_forget:
            try:
                AsyncResult(celery_id_to_forget, app=celery_app).forget()
            except Exception as forget_err:
                logger.warning(
                    f"Could not forget Celery result {celery_id_to_forget}: {forget_err}"
                )

        # Clean up chapter status files
        if novel and novel.title:
            try:
                status_folder_base = current_app.config.get("NOVEL_STATUS_PATH")
                if status_folder_base:
                    safe_book_name = re.sub(r'[\\/*?:"<>|]', "_", novel.title)
                    safe_book_id = re.sub(r"[^a-zA-Z0-9_]", "_", str(novel_id))
                    status_folder = os.path.join(status_folder_base, f"{safe_book_id}_{safe_book_name}")
                    
                    if os.path.exists(status_folder):
                        shutil.rmtree(status_folder)
                        logger.info(f"Deleted status folder for Novel {novel_id}: {status_folder}")
            except Exception as cleanup_err:
                logger.warning(f"Failed to clean up status folder for Novel {novel_id}: {cleanup_err}")

        emit_task_update(user_id, {"id": db_task_id, "deleted": True})
        return jsonify(message="Task deleted successfully.")
    except Exception as e:
        _db.session.rollback()
        logger.error(f"Error deleting task {db_task_id}: {e}", exc_info=True)
        return jsonify(error="Failed to delete task"), 500


@app.route("/api/tasks/<int:db_task_id>/redownload", methods=["POST"])
def redownload_task(db_task_id):
    logger = current_app.logger
    logger.info(f"Internal API requesting re-download for DB Task ID: {db_task_id}")
    try:
        task = DownloadTask.query.filter_by(id=db_task_id).first()
        if not task:
            return jsonify(error="Task not found"), 404
        
        user_id = task.user_id  # Get the real user_id for notifications

        if task.status in [
            TaskStatus.DOWNLOADING,
            TaskStatus.PROCESSING,
            TaskStatus.PENDING,
        ]:
            return jsonify(
                error=f"Cannot re-download active task ({task.status.name})."
            ), 409

        novel_id_to_redownload = task.novel_id
        novel = task.novel
        logger.info(
            f"Re-downloading Novel {novel_id_to_redownload} for User {user_id} (Task {db_task_id})"
        )

        # Clean up chapter status files to allow fresh download
        if novel and novel.title:
            try:
                status_folder_base = current_app.config.get("NOVEL_STATUS_PATH")
                if status_folder_base:
                    safe_book_name = re.sub(r'[\\/*?:"<>|]', "_", novel.title)
                    safe_book_id = re.sub(r"[^a-zA-Z0-9_]", "_", str(novel_id_to_redownload))
                    status_folder = os.path.join(status_folder_base, f"{safe_book_id}_{safe_book_name}")
                    
                    if os.path.exists(status_folder):
                        shutil.rmtree(status_folder)
                        logger.info(f"Cleared status folder for re-download of Novel {novel_id_to_redownload}: {status_folder}")
            except Exception as cleanup_err:
                logger.warning(f"Failed to clean up status folder for Novel {novel_id_to_redownload}: {cleanup_err}")

        task.status = TaskStatus.PENDING
        task.progress = 0
        task.message = "Re-download requested."
        task.celery_task_id = None
        _db.session.commit()
        logger.info(f"Reset DB Task {db_task_id} to PENDING.")
        emit_task_update(user_id, task.to_dict())

        try:
            celery_task = celery_app.send_task(
                "tasks.process_novel",
                kwargs={
                    "novel_id": novel_id_to_redownload,
                    "user_id": user_id,
                    "db_task_id": db_task_id,
                },
            )
            logger.info(
                f"Queued new Celery task {celery_task.id} for re-download (DB Task {db_task_id})"
            )
            task.celery_task_id = celery_task.id
            _db.session.commit()
            logger.info(
                f"Updated DB Task {db_task_id} with new Celery ID {celery_task.id}"
            )
            return jsonify(message="Re-download task queued.", task=task.to_dict()), 202
        except Exception as queue_err:
            logger.error(
                f"Failed queue Celery re-download (DB Task {db_task_id}): {queue_err}",
                exc_info=True,
            )
            task.status = TaskStatus.FAILED
            task.message = f"Failed to queue re-download: {queue_err}"
            _db.session.commit()
            emit_task_update(user_id, task.to_dict())
            return jsonify(error="Failed to queue background task"), 500
    except Exception as e:
        _db.session.rollback()
        logger.error(
            f"Error during re-download for task {db_task_id}: {e}", exc_info=True
        )
        return jsonify(error="Failed to initiate re-download"), 500


@app.route("/api/tasks/status/<string:task_id>", methods=["GET"])
def get_task_status(task_id):
    if not task_id or len(task_id) > 64 or not task_id.replace("-", "").isalnum():
        return jsonify(error="Invalid Celery task ID format"), 400
    task_result = AsyncResult(task_id, app=celery_app)
    status = task_result.status
    result = task_result.result
    response = {"task_id": task_id, "status": status, "result": None, "meta": None}
    status_map = {
        "PENDING": "Task is waiting.",
        "STARTED": "Task started.",
        "PROGRESS": "Task in progress.",
        "SUCCESS": "Task completed.",
        "FAILURE": "Task failed.",
        "REVOKED": "Task terminated.",
    }
    response["result"] = status_map.get(status, f"Unknown state: {status}")
    if isinstance(result, dict):
        response["meta"] = result
    elif isinstance(result, Exception):
        response["meta"] = {
            "exc_type": type(result).__name__,
            "exc_message": str(result),
        }
    else:
        response["meta"] = task_result.info
    if (
        status == "FAILURE"
        and response["meta"] is None
        and hasattr(task_result, "traceback")
    ):
        response["traceback"] = task_result.traceback
    return jsonify(response)


# --- Stats Endpoints ---
@app.get("/api/stats/upload")
def upload_stats():
    start_date = datetime.utcnow().date() - timedelta(days=29)
    try:
        date_expr = func.date(Novel.created_at)
        rows = (
            _db.session.query(date_expr.label("d"), func.count(Novel.id).label("c"))
            .filter(Novel.created_at >= start_date)
            .group_by(date_expr)
            .order_by(date_expr)
            .all()
        )
        return jsonify([{"date": str(r[0]), "count": r[1]} for r in rows])
    except Exception as e:
        current_app.logger.error(f"Error fetching upload stats: {e}", exc_info=True)
        _db.session.rollback()
        return jsonify(error="Database error fetching upload stats"), 500


@app.get("/api/stats/genre")
def genre_stats():
    sql = "SELECT tags, COUNT(*) as c FROM novel GROUP BY tags;"
    try:
        rows = _db.session.execute(sql_text(sql)).fetchall()
        tag_counts = {}
        for tags_str, count in rows:
            primary_tag = (tags_str.split("|")[0].strip() if tags_str else "") or "未知"
            tag_counts[primary_tag] = tag_counts.get(primary_tag, 0) + count
        return jsonify(
            [{"name": tag, "value": value} for tag, value in tag_counts.items()]
        )
    except Exception as e:
        current_app.logger.error(f"Error fetching genre stats: {e}", exc_info=True)
        _db.session.rollback()
        return jsonify(error="Database error fetching genre stats"), 500


@app.get("/api/stats/wordcloud/<int:novel_id>")
def wordcloud_img(novel_id):
    wordcloud_dir = current_app.config.get("WORDCLOUD_SAVE_PATH")
    if not wordcloud_dir:
        return jsonify(error="Server configuration error"), 500
    safe_filename = f"wordcloud_{novel_id}.png"
    path = os.path.abspath(os.path.join(wordcloud_dir, safe_filename))
    if not path.startswith(os.path.abspath(wordcloud_dir)):
        return jsonify(error="Invalid file path"), 400
    if os.path.isfile(path):
        try:
            return send_file(path, mimetype="image/png")
        except Exception as send_err:
            current_app.logger.error(
                f"Error sending file {path}: {send_err}", exc_info=True
            )
            return jsonify(error="Error sending file"), 500
    else:
        novel_exists = Novel.query.get(novel_id) is not None
        error_msg = (
            "Wordcloud not found. Analysis incomplete or failed."
            if novel_exists
            else f"Novel with ID {novel_id} not found."
        )
        return jsonify(error=error_msg), 404


@app.route("/api/novels/<int:novel_id>/download", methods=["GET"])
def download_novel_file(novel_id):
    logger = current_app.logger
    try:
        novel = Novel.query.get(novel_id)
        if not novel or not novel.title:
            abort(404, description="Novel not found or missing title")

        save_path_base = current_app.config.get("NOVEL_SAVE_PATH")
        novel_format = current_app.config.get("NOVEL_NOVEL_FORMAT", "epub")
        if not save_path_base:
            abort(500, description="Server configuration error: Save path not set.")

        safe_book_name = re.sub(r'[\\/*?:"<>|]', "_", novel.title)
        filename = f"{safe_book_name}.{novel_format}"
        full_path = os.path.abspath(os.path.join(save_path_base, filename))
        if not full_path.startswith(os.path.abspath(save_path_base)):
            abort(400, description="Invalid file path.")

        if os.path.isfile(full_path):
            if _novel_status_has_errors(novel_id, novel.title):
                try:
                    os.remove(full_path)
                    logger.warning(f"Removed stale exported file with failed chapters: {full_path}")
                except OSError as cleanup_err:
                    logger.warning(f"Failed to remove stale exported file {full_path}: {cleanup_err}")
                abort(409, description="小说下载未完成，存在失败章节，请重新更新或重试下载任务后再导出。")

            mime_type = (
                "application/epub+zip" if novel_format == "epub" else "text/plain"
            )
            logger.info(f"Sending file: {filename} (MIME: {mime_type})")
            return send_file(
                full_path,
                mimetype=mime_type,
                as_attachment=True,
                download_name=filename,
            )
        else:
            task = (
                DownloadTask.query.filter_by(novel_id=novel_id)
                .order_by(DownloadTask.created_at.desc())
                .first()
            )
            status_msg = (
                f"Task status: {task.status.name}."
                if task
                else "No download task found."
            )
            description = f"Generated novel file ({filename}) not found. {status_msg}"
            abort(404, description=description)
    except HTTPException as e:
        logger.warning(
            f"HTTP Exception during download for novel {novel_id}: {e.code} - {e.description}"
        )
        return jsonify(error=e.description), e.code
    except Exception as e:
        logger.error(f"Error during novel download {novel_id}: {e}", exc_info=True)
        abort(500, description="Error serving novel file.")


# --- Error Handlers ---
@app.errorhandler(404)
def not_found_error(error):
    app.logger.warning(
        f"Not Found (404): {request.path} - {getattr(error, 'description', 'No description')}"
    )
    return jsonify(error=getattr(error, "description", "Resource not found")), 404


@app.errorhandler(500)
def internal_error(error):
    original_exception = getattr(error, "original_exception", error)
    app.logger.error(
        f"Internal Server Error (500): {request.path} - {original_exception}",
        exc_info=original_exception,
    )
    try:
        _db.session.rollback()
    except Exception as rb_err:
        app.logger.error(f"Error rolling back session during 500 handler: {rb_err}")
    return jsonify(error="内部服务器错误"), 500


@app.errorhandler(Exception)
def unhandled_exception(e):
    if isinstance(e, HTTPException):
        return jsonify(error=getattr(e, "description", "An error occurred")), e.code
    app.logger.error(f"Unhandled exception caught: {request.path} - {e}", exc_info=True)
    try:
        _db.session.rollback()
    except Exception as rb_err:
        app.logger.error(f"Error rolling back session: {rb_err}")
    return jsonify(error="发生意外错误"), 500


# --- Main ---
if __name__ == "__main__":
    app.logger.info("Starting Flask application directly (dev mode)")
    host = os.getenv("FLASK_RUN_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_RUN_PORT", 5000))
    debug_mode = os.getenv("FLASK_ENV") == "development"
    app.logger.info(f"Running on http://{host}:{port}/ with debug={debug_mode}")
    socketio.run(app, host=host, port=port, debug=debug_mode, use_reloader=debug_mode)
