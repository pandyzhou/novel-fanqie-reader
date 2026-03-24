import os
import sys
import tempfile
import unittest

_TEMP_DB = tempfile.NamedTemporaryFile(prefix='fanqie_auth_test_', suffix='.db', delete=False)
_TEMP_DB.close()

os.environ['DATABASE_URL'] = f'sqlite:///{_TEMP_DB.name}'
os.environ['CELERY_BROKER_URL'] = 'memory://'
os.environ['CELERY_RESULT_BACKEND'] = 'cache+memory://'
os.environ['INTERNAL_API_MODE'] = 'true'
os.environ['INTERNAL_API_USER_ID'] = '1'
os.environ['AUTO_CREATE_TABLES'] = 'true'
os.environ['RUN_LEGACY_RUNTIME_SCHEMA_PATCHES'] = 'false'
os.environ.setdefault('JWT_SECRET_KEY', 'test-jwt-secret-key-please-change-1234')
os.environ.setdefault('FLASK_SECRET_KEY', 'test-flask-secret-key-please-change-1234')

BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from app import app  # noqa: E402
from database import db  # noqa: E402
from models import Novel  # noqa: E402


class AuthContractTests(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        with app.app_context():
            db.session.remove()
            db.engine.dispose()
        if os.path.exists(_TEMP_DB.name):
            os.remove(_TEMP_DB.name)

    def setUp(self):
        self.client = app.test_client()

    def test_register_success_response_contains_message_and_msg(self):
        response = self.client.post(
            '/api/auth/register',
            json={'username': 'contract_user', 'password': 'password123'},
        )
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload['msg'], '注册成功')
        self.assertEqual(payload['message'], '注册成功')

    def test_register_validation_error_contains_error_and_msg(self):
        response = self.client.post('/api/auth/register', json={'username': '', 'password': ''})
        payload = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(payload['error'], '用户名和密码不能为空')
        self.assertEqual(payload['msg'], '用户名和密码不能为空')

    def test_system_info_includes_internal_api_and_migration_fields(self):
        response = self.client.get('/api/system/info')
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertIn('database_backend', payload)
        self.assertIn('internal_api_mode', payload)
        self.assertIn('internal_api_user_id', payload)
        self.assertIn('auto_create_tables', payload)
        self.assertIn('run_legacy_runtime_schema_patches', payload)
        self.assertIn('migration_directory', payload)
        self.assertIn('migration_version_table_present', payload)
        self.assertIn('current_migration_versions', payload)
        self.assertTrue(payload['internal_api_mode'])
        self.assertEqual(payload['internal_api_user_id'], 1)
        self.assertIsInstance(payload['auto_create_tables'], bool)
        self.assertIsInstance(payload['run_legacy_runtime_schema_patches'], bool)
        self.assertIsInstance(payload['migration_version_table_present'], bool)
        self.assertIsInstance(payload['current_migration_versions'], list)

    def test_existing_novel_without_wordcloud_returns_404(self):
        with app.app_context():
            novel = Novel(id=987654321001, title='词云缺失测试小说')
            db.session.merge(novel)
            db.session.commit()

        response = self.client.get('/api/stats/wordcloud/987654321001')
        payload = response.get_json()

        self.assertEqual(response.status_code, 404)
        self.assertEqual(payload['error'], 'Wordcloud not found. Analysis incomplete or failed.')

    def test_existing_novel_without_export_returns_404(self):
        with app.app_context():
            novel = Novel(id=987654321002, title='导出缺失测试小说')
            db.session.merge(novel)
            db.session.commit()

        response = self.client.get('/api/novels/987654321002/download')
        payload = response.get_json()

        self.assertEqual(response.status_code, 404)
        self.assertIn('Generated novel file', payload['error'])


if __name__ == '__main__':
    unittest.main()
