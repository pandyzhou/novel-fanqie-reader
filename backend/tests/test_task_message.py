import os
import sys
import unittest

BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from models import DownloadTask, Novel, TaskStatus, parse_task_message  # noqa: E402


class TaskMessageParsingTests(unittest.TestCase):
    def test_parse_task_message_extracts_stage_and_error_code(self):
        parsed = parse_task_message('[stage:download][code:chapter_list_fetch_failed] 获取章节目录失败。')

        self.assertEqual(parsed['task_stage'], 'download')
        self.assertEqual(parsed['error_code'], 'chapter_list_fetch_failed')
        self.assertEqual(parsed['message'], '获取章节目录失败。')
        self.assertIn('[stage:download]', parsed['raw_message'])

    def test_parse_task_message_handles_plain_text(self):
        parsed = parse_task_message('普通提示信息')

        self.assertIsNone(parsed['task_stage'])
        self.assertIsNone(parsed['error_code'])
        self.assertEqual(parsed['message'], '普通提示信息')

    def test_download_task_to_dict_exposes_structured_message_fields(self):
        novel = Novel(id=123456789, title='测试小说', author='测试作者')
        task = DownloadTask(
            id=1,
            user_id=1,
            novel_id=novel.id,
            status=TaskStatus.FAILED,
            progress=95,
            message='[stage:finalize][code:export_incomplete] 下载未完成：成功保存 10/12 章，仍有 2 章失败或缺失，未生成导出文件。',
        )
        task.novel = novel

        payload = task.to_dict()

        self.assertEqual(payload['status'], 'FAILED')
        self.assertEqual(payload['task_stage'], 'finalize')
        self.assertEqual(payload['error_code'], 'export_incomplete')
        self.assertEqual(payload['message'], '下载未完成：成功保存 10/12 章，仍有 2 章失败或缺失，未生成导出文件。')
        self.assertIn('[code:export_incomplete]', payload['raw_message'])


if __name__ == '__main__':
    unittest.main()
