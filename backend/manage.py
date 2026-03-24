"""Flask CLI entrypoint for database migrations and shell helpers.

Usage examples (run from repository root):

    PYTHONPATH=backend FLASK_APP=manage:app python -m flask db heads --directory backend/migrations
    PYTHONPATH=backend FLASK_APP=manage:app python -m flask db upgrade --directory backend/migrations
"""

from app import app
from database import db
from models import Chapter, DownloadTask, Novel, SearchCacheEntry, SearchQueryCacheEntry, User, WordStat


@app.shell_context_processor
def _make_shell_context():
    return {
        "db": db,
        "User": User,
        "Novel": Novel,
        "Chapter": Chapter,
        "DownloadTask": DownloadTask,
        "WordStat": WordStat,
        "SearchCacheEntry": SearchCacheEntry,
        "SearchQueryCacheEntry": SearchQueryCacheEntry,
    }
