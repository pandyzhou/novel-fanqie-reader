import os
import sys
import tempfile
import unittest

_TEMP_DB = tempfile.NamedTemporaryFile(prefix='fanqie_task_classify_', suffix='.db', delete=False)
_TEMP_DB.close()

os.environ['DATABASE_URL'] = f'sqlite:///{_TEMP_DB.name}'
os.environ['CELERY_BROKER_URL'] = 'memory://'
os.environ['CELERY_RESULT_BACKEND'] = 'cache+memory://'
os.environ['INTERNAL_API_MODE'] = 'true'
os.environ['INTERNAL_API_USER_ID'] = '1'
os.environ.setdefault('JWT_SECRET_KEY', 'task-classify-jwt-secret-key-1234')
os.environ.setdefault('FLASK_SECRET_KEY', 'task-classify-flask-secret-key-1234')

BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from app import app  # noqa: E402
from database import db  # noqa: E402
from tasks import _build_task_message, _classify_task_error  # noqa: E402


class TaskClassificationTests(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        with app.app_context():
            db.session.remove()
            db.engine.dispose()
        if os.path.exists(_TEMP_DB.name):
            os.remove(_TEMP_DB.name)

    def test_build_task_message_with_stage_and_code(self):
        message = _build_task_message('获取章节目录失败。', stage='chapter_list', error_code='chapter_list_fetch_failed')
        self.assertEqual(message, '[stage:chapter_list][code:chapter_list_fetch_failed] 获取章节目录失败。')

    def test_build_task_message_without_metadata(self):
        message = _build_task_message('普通提示信息')
        self.assertEqual(message, '普通提示信息')

    def test_classify_book_info_error(self):
        stage, error_code, user_message = _classify_task_error(ValueError('Failed to fetch book info for ID 1.'))
        self.assertEqual(stage, 'metadata')
        self.assertEqual(error_code, 'book_info_fetch_failed')
        self.assertEqual(user_message, '获取小说元数据失败。')

    def test_classify_chapter_list_error(self):
        stage, error_code, user_message = _classify_task_error(RuntimeError('Failed to fetch chapter list for ID 1.'))
        self.assertEqual(stage, 'chapter_list')
        self.assertEqual(error_code, 'chapter_list_fetch_failed')
        self.assertEqual(user_message, '获取章节目录失败。')

    def test_classify_finalize_error(self):
        stage, error_code, user_message = _classify_task_error(RuntimeError('Error finalizing book manager: disk full'))
        self.assertEqual(stage, 'finalize')
        self.assertEqual(error_code, 'export_finalize_failed')
        self.assertEqual(user_message, '生成导出文件或状态文件失败。')

    def test_classify_analysis_error(self):
        stage, error_code, user_message = _classify_task_error(RuntimeError('Analysis failed: no text data'))
        self.assertEqual(stage, 'analysis')
        self.assertEqual(error_code, 'analysis_failed')
        self.assertEqual(user_message, '文本分析或词云生成失败。')

    def test_classify_unknown_error(self):
        stage, error_code, user_message = _classify_task_error(RuntimeError('totally unexpected failure'))
        self.assertEqual(stage, 'finalize')
        self.assertEqual(error_code, 'unexpected_exception')
        self.assertEqual(user_message, '任务执行失败：RuntimeError')


if __name__ == '__main__':
    unittest.main()
