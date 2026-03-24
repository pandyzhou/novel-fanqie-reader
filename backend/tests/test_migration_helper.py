import io
import os
import sys
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

import migrate  # noqa: E402


class MigrationHelperTests(unittest.TestCase):
    def test_parse_args_for_stamp_head_apply(self):
        args = migrate.parse_args(['stamp-head', '--apply'])

        self.assertEqual(args.command, 'stamp-head')
        self.assertTrue(args.apply)

    def test_main_stamp_head_dry_run_does_not_call_flask(self):
        output = io.StringIO()
        with redirect_stdout(output), patch.object(migrate, 'run_flask_db') as mocked_run:
            exit_code = migrate.main(['stamp-head'])

        self.assertEqual(exit_code, 0)
        mocked_run.assert_not_called()
        self.assertIn('Dry run only', output.getvalue())

    def test_main_upgrade_proxies_to_flask_db(self):
        with patch.object(migrate, 'run_flask_db', return_value=0) as mocked_run:
            exit_code = migrate.main(['upgrade'])

        self.assertEqual(exit_code, 0)
        mocked_run.assert_called_once_with('upgrade', [])

    def test_print_status_contains_key_runtime_fields(self):
        snapshot = {
            'database_backend': 'postgresql',
            'database_url': 'postgresql+psycopg://user:pass@host/db',
            'migration_directory': 'backend/migrations',
            'auto_create_tables': False,
            'run_legacy_runtime_schema_patches': False,
            'head_versions': ['855f02a5fd92'],
            'current_versions': ['855f02a5fd92'],
            'has_alembic_version': True,
            'table_count': 8,
            'table_names': ['novel', 'chapter', 'alembic_version'],
        }
        output = io.StringIO()

        with redirect_stdout(output), patch.object(migrate, 'get_status_snapshot', return_value=snapshot):
            migrate.print_status()

        text = output.getvalue()
        self.assertIn('Database backend      : postgresql', text)
        self.assertIn('AUTO_CREATE_TABLES    : False', text)
        self.assertIn('Legacy schema patches : False', text)
        self.assertIn('855f02a5fd92', text)

    def test_print_guide_for_existing_database_without_migration_table(self):
        snapshot = {
            'table_count': 7,
            'has_alembic_version': False,
            'current_versions': [],
            'head_versions': ['855f02a5fd92'],
            'auto_create_tables': True,
            'run_legacy_runtime_schema_patches': False,
        }
        output = io.StringIO()

        with redirect_stdout(output), patch.object(migrate, 'get_status_snapshot', return_value=snapshot):
            migrate.print_guide()

        text = output.getvalue()
        self.assertIn('还没有 alembic_version 记录', text)
        self.assertIn('stamp-head --apply', text)

    def test_print_guide_for_recommended_state(self):
        snapshot = {
            'table_count': 8,
            'has_alembic_version': True,
            'current_versions': ['855f02a5fd92'],
            'head_versions': ['855f02a5fd92'],
            'auto_create_tables': False,
            'run_legacy_runtime_schema_patches': False,
        }
        output = io.StringIO()

        with redirect_stdout(output), patch.object(migrate, 'get_status_snapshot', return_value=snapshot):
            migrate.print_guide()

        text = output.getvalue()
        self.assertIn('推荐状态', text)
        self.assertIn('python backend/migrate.py migrate -m', text)


if __name__ == '__main__':
    unittest.main()
