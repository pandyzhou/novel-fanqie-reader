# backend/config.py
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()  # Load .env file


def _install_mysql_driver_if_needed(database_uri: str | None) -> None:
    if database_uri and database_uri.startswith("mysql"):
        import pymysql

        pymysql.install_as_MySQLdb()


def _build_legacy_mysql_database_uri() -> str | None:
    required_keys = ("DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT", "DB_NAME")
    if not all(os.getenv(key) for key in required_keys):
        return None

    return (
        f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}?charset=utf8mb4"
    )


def _default_sqlite_database_uri() -> str:
    data_base_path = Path(
        os.getenv("DATA_BASE_PATH", os.path.join(os.path.dirname(__file__), "data"))
    ).expanduser()
    sqlite_path = data_base_path.resolve() / "fanqie.db"
    return f"sqlite:///{sqlite_path.as_posix()}"


def _detect_database_backend(database_uri: str | None) -> str:
    if not database_uri:
        return "unknown"
    if database_uri.startswith("postgresql"):
        return "postgresql"
    if database_uri.startswith("sqlite"):
        return "sqlite"
    if database_uri.startswith("mysql"):
        return "mysql"
    return "unknown"


def _probe_database_uri(database_uri: str) -> tuple[bool, str | None]:
    connect_args = {}
    if database_uri.startswith("postgresql"):
        connect_args["connect_timeout"] = 2
    elif database_uri.startswith("mysql"):
        connect_args["connect_timeout"] = 2

    engine = create_engine(database_uri, pool_pre_ping=True, connect_args=connect_args)
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True, None
    except Exception as exc:  # pragma: no cover - depends on runtime environment
        return False, str(exc)
    finally:
        engine.dispose()


PRIMARY_DATABASE_URL = os.getenv("DATABASE_URL") or _build_legacy_mysql_database_uri()
DATABASE_FALLBACK_URL = os.getenv("DATABASE_FALLBACK_URL") or _default_sqlite_database_uri()
DATABASE_FALLBACK_ON_FAILURE = (
    os.getenv("DATABASE_FALLBACK_ON_FAILURE", "true").lower() == "true"
)

_install_mysql_driver_if_needed(PRIMARY_DATABASE_URL)
_install_mysql_driver_if_needed(DATABASE_FALLBACK_URL)

DATABASE_FALLBACK_REASON = None
ACTIVE_DATABASE_URL = PRIMARY_DATABASE_URL or DATABASE_FALLBACK_URL

if not PRIMARY_DATABASE_URL:
    DATABASE_FALLBACK_REASON = "DATABASE_URL 未配置，已使用本地 SQLite 回退数据库。"
elif (
    DATABASE_FALLBACK_ON_FAILURE
    and DATABASE_FALLBACK_URL
    and not PRIMARY_DATABASE_URL.startswith("sqlite")
):
    is_available, error_message = _probe_database_uri(PRIMARY_DATABASE_URL)
    if not is_available:
        ACTIVE_DATABASE_URL = DATABASE_FALLBACK_URL
        DATABASE_FALLBACK_REASON = error_message or "主数据库连接失败，已切换到本地 SQLite。"
        print(
            "Warning: Primary DATABASE_URL is unavailable; "
            "falling back to DATABASE_FALLBACK_URL (SQLite)."
        )

ACTIVE_DATABASE_BACKEND = _detect_database_backend(ACTIVE_DATABASE_URL)
DATABASE_FALLBACK_ACTIVE = (
    bool(DATABASE_FALLBACK_REASON) and ACTIVE_DATABASE_URL == DATABASE_FALLBACK_URL
)


class Settings:
    # --- Database Settings ---
    PRIMARY_DATABASE_URL = PRIMARY_DATABASE_URL
    ACTIVE_DATABASE_URL = ACTIVE_DATABASE_URL
    ACTIVE_DATABASE_BACKEND = ACTIVE_DATABASE_BACKEND
    DATABASE_FALLBACK_URL = DATABASE_FALLBACK_URL
    DATABASE_FALLBACK_ACTIVE = DATABASE_FALLBACK_ACTIVE
    DATABASE_FALLBACK_REASON = DATABASE_FALLBACK_REASON

    SQLALCHEMY_DATABASE_URI = ACTIVE_DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = (
        os.getenv("SQLALCHEMY_ECHO", "False").lower() == "true"
    )  # For debugging DB queries
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": int(os.getenv("SQLALCHEMY_POOL_RECYCLE", "1800")),
    }

    # --- JWT Settings ---
    JWT_SECRET_KEY = os.getenv(
        "JWT_SECRET_KEY", "a-very-secret-key-please-change"
    )  # Use a strong, unique secret
    JWT_ACCESS_TOKEN_EXPIRES = (
        int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", 60)) * 60
    )  # In seconds

    # --- Celery Settings ---
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1")
    CELERY_TASK_SERIALIZER = "json"
    CELERY_RESULT_SERIALIZER = "json"
    CELERY_ACCEPT_CONTENT = ["json"]
    CELERY_TIMEZONE = (
        "Asia/Shanghai"  # Or your preferred timezone e.g., 'Asia/Shanghai'
    )
    CELERY_ENABLE_UTC = True
    CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True  # Good practice

    # --- File Storage Paths ---
    # Base path for generated data
    DATA_BASE_PATH = os.getenv(
        "DATA_BASE_PATH", os.path.join(os.path.dirname(__file__), "data")
    )

    # Word Cloud Image Save Path
    WORDCLOUD_SAVE_SUBDIR = "wordclouds"
    WORDCLOUD_SAVE_PATH = os.path.join(DATA_BASE_PATH, WORDCLOUD_SAVE_SUBDIR)

    SEARCH_COVER_CACHE_SUBDIR = "search_covers"
    SEARCH_COVER_CACHE_PATH = os.path.join(DATA_BASE_PATH, SEARCH_COVER_CACHE_SUBDIR)

    # --- novel_downloader Configuration Mapping ---
    # These keys should match the fields expected by novel_downloader's Config class
    # We'll construct a dict from these to pass to GlobalContext.initialize

    # Paths (required)
    NOVEL_SAVE_PATH = os.getenv(
        "NOVEL_SAVE_PATH", os.path.join(DATA_BASE_PATH, "novel_downloads")
    )
    NOVEL_STATUS_PATH = os.getenv(
        "NOVEL_STATUS_PATH", os.path.join(DATA_BASE_PATH, "novel_status")
    )

    # Core Settings
    NOVEL_MAX_WORKERS = int(
        os.getenv("NOVEL_MAX_WORKERS", 5)
    )  # Increased default slightly
    NOVEL_REQUEST_TIMEOUT = int(
        os.getenv("NOVEL_REQUEST_TIMEOUT", 20)
    )  # Increased default slightly
    NOVEL_MAX_RETRIES = int(os.getenv("NOVEL_MAX_RETRIES", 3))
    NOVEL_MIN_WAIT_TIME = int(
        os.getenv("NOVEL_MIN_WAIT_TIME", 800)
    )  # Adjusted defaults
    NOVEL_MAX_WAIT_TIME = int(
        os.getenv("NOVEL_MAX_WAIT_TIME", 1500)
    )  # Adjusted defaults
    NOVEL_MIN_CONNECT_TIMEOUT = float(os.getenv("NOVEL_MIN_CONNECT_TIMEOUT", 3.1))
    NOVEL_NOVEL_FORMAT = os.getenv("NOVEL_FORMAT", "txt").lower()
    NOVEL_BULK_FILES = os.getenv("NOVEL_BULK_FILES", "False").lower() == "true"
    NOVEL_AUTO_CLEAR_DUMP = os.getenv("NOVEL_AUTO_CLEAR", "True").lower() == "true"
    # Proxy API Mode (推荐使用)
    NOVEL_USE_PROXY_API = (
        os.getenv("NOVEL_USE_PROXY_API", "False").lower() == "true"
    )

    # Third-party API (cenguigui) 开关，默认开启
    NOVEL_USE_THIRDPARTY_API = (
        os.getenv("NOVEL_USE_THIRDPARTY_API", "True").lower() == "true"
    )

    # Custom Content API（通过配置启用，而非默认第一通道）
    NOVEL_USE_CUSTOM_CONTENT_API = (
        os.getenv("NOVEL_USE_CUSTOM_CONTENT_API", "True").lower() == "true"
    )
    NOVEL_CUSTOM_CONTENT_API_BASE = os.getenv(
        "NOVEL_CUSTOM_CONTENT_API_BASE",
        "http://117.24.4.119:11451/fqy/api_v2.php",
    )
    # 从 .env 读取密钥变量（Docker Compose 会自动注入 .env）
    NOVEL_CUSTOM_CONTENT_API_KEY = os.getenv("FQ_API_KEY", "")

    # Official API (保留开关但默认关闭)
    NOVEL_USE_OFFICIAL_API = (
        os.getenv("NOVEL_USE_OFFICIAL_API", "False").lower() == "true"
    )
    NOVEL_IID = os.getenv("NOVEL_IID", "")  # Allow setting via env if needed
    NOVEL_IID_SPAWN_TIME = os.getenv("NOVEL_IID_SPAWN_TIME", "")

    # API Endpoints (allow comma-separated list from env)
    NOVEL_API_ENDPOINTS_STR = os.getenv(
        "NOVEL_API_ENDPOINTS", "https://api.cenguigui.cn/api/tomato"
    )
    NOVEL_API_ENDPOINTS = [
        url.strip() for url in NOVEL_API_ENDPOINTS_STR.split(",") if url.strip()
    ]
    # --- End novel_downloader Configuration Mapping ---

    # --- General App Settings ---
    DEBUG = os.getenv("FLASK_ENV", "production") == "development"
    SECRET_KEY = os.getenv(
        "FLASK_SECRET_KEY", "another-secret-key-please-change"
    )  # For Flask session etc.

    # --- Ensure directories exist ---
    @staticmethod
    def _ensure_dir(path):
        try:
            os.makedirs(path, exist_ok=True)
        except OSError as e:
            print(f"Warning: Could not create directory {path}: {e}")

    _ensure_dir(DATA_BASE_PATH)
    _ensure_dir(WORDCLOUD_SAVE_PATH)
    _ensure_dir(SEARCH_COVER_CACHE_PATH)
    _ensure_dir(NOVEL_SAVE_PATH)
    _ensure_dir(NOVEL_STATUS_PATH)


settings = Settings()


# Helper function to get downloader config as dict
def get_downloader_config():
    return {
        "save_path": settings.NOVEL_SAVE_PATH,
        "status_folder_path_base": settings.NOVEL_STATUS_PATH,
        "max_workers": settings.NOVEL_MAX_WORKERS,
        "request_timeout": settings.NOVEL_REQUEST_TIMEOUT,
        "max_retries": settings.NOVEL_MAX_RETRIES,
        "max_wait_time": settings.NOVEL_MAX_WAIT_TIME,
        "min_wait_time": settings.NOVEL_MIN_WAIT_TIME,
        "min_connect_timeout": settings.NOVEL_MIN_CONNECT_TIMEOUT,
        "novel_format": settings.NOVEL_NOVEL_FORMAT,
        "bulk_files": settings.NOVEL_BULK_FILES,
        "auto_clear_dump": settings.NOVEL_AUTO_CLEAR_DUMP,
        "use_proxy_api": settings.NOVEL_USE_PROXY_API,  # 代理模式
        "use_thirdparty_api": settings.NOVEL_USE_THIRDPARTY_API,  # 第三方番茄API（cenguigui）
        "use_custom_content_api": settings.NOVEL_USE_CUSTOM_CONTENT_API,
        "custom_content_api_base": settings.NOVEL_CUSTOM_CONTENT_API_BASE,
        "custom_content_api_key": settings.NOVEL_CUSTOM_CONTENT_API_KEY,
        "use_official_api": settings.NOVEL_USE_OFFICIAL_API,
        "api_endpoints": settings.NOVEL_API_ENDPOINTS,
        "iid": settings.NOVEL_IID,  # Pass these through
        "iid_spawn_time": settings.NOVEL_IID_SPAWN_TIME,
        # Add other fields from novel_downloader's Config if needed
    }
