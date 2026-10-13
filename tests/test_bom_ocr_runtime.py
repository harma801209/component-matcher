import io
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import bom_image_ocr_runtime as runtime


class IsolatedImageOCRTests(unittest.TestCase):
    def test_clipboard_is_user_initiated_scoped_and_reuses_file_uploader(self):
        from bom_image_clipboard import build_bom_image_clipboard_html
        html = build_bom_image_clipboard_html()
        for expected in ('Ctrl+V', 'clipboardData', '上传 BOM Excel/CSV/图片',
                         'input[type="file"]', 'new host.DataTransfer()',
                         "new host.Event('change'", 'previous.dispose()',
                         "removeEventListener('paste'", 'textarea', 'contenteditable',
                         'if (!files.length) return;', 'files.length !== 1',
                         '不会自动开始匹配', 'role="status"'):
            self.assertIn(expected, html)
        for forbidden in ('navigator.clipboard.read', 'fetch(', 'XMLHttpRequest',
                          'localStorage', 'readText(', 'setInterval(', 'image/svg+xml'):
            self.assertNotIn(forbidden, html)

    def test_character_confidence_uses_ctc_peak_not_weak_boundary(self):
        from bom_image_ocr_worker import recognize_strips
        alphabet = ['', 'A', '0', 'O']
        predictions = np.array([[[.1, .55, .2, .15], [.01, .97, .01, .01],
                                 [.9, .05, .03, .02], [.05, .01, .50, .44]]], dtype=np.float32)
        recognizer = SimpleNamespace(rec_batch_num=1, rec_image_shape=[3,48,320],
                                     postprocess_op=SimpleNamespace(character=alphabet),
                                     resize_norm_img=lambda crop, ratio: np.zeros((3,48,320)),
                                     session=lambda batch: [predictions])
        text, score, detail = recognize_strips(recognizer, [np.full((24,100,3),255,dtype=np.uint8)])[0]
        self.assertEqual(text, 'A0')
        self.assertGreater(score, .3)
        self.assertEqual(len(detail['uncertain']), 1)
        self.assertEqual(detail['uncertain'][0]['char'], '0')
        self.assertEqual(detail['uncertain'][0]['alternative'], 'O')
        self.assertEqual(detail['uncertain'][0]['index'], 1)

    def test_install_is_scoped_to_ocr_cache_and_uses_explicit_wheels(self):
        with tempfile.TemporaryDirectory(prefix='ocr-runtime-test-') as folder, patch.object(runtime, 'ROOT', Path(folder)):
            with patch.object(runtime.subprocess, 'run', side_effect=[
                    SimpleNamespace(returncode=0, stdout=b'', stderr=b''),
                    SimpleNamespace(returncode=0, stdout=b'{"ready":true}', stderr=b'')]) as run:
                directory = runtime.ensure_runtime()
            self.assertEqual(directory.parent, Path(folder)/'cache')
            command = run.call_args_list[0].args[0]
            self.assertEqual(command[command.index('--target')+1], str(directory))
            self.assertIn('--no-deps', command)
            self.assertIn('--only-binary=:all:', command)
            self.assertNotIn('--force-reinstall', command)
            self.assertIn('opencv-python-headless>=4.10,<5', command)
            self.assertFalse(run.call_args_list[0].kwargs.get('shell', False))

    def test_existing_healthy_environment_is_reused_without_install(self):
        with tempfile.TemporaryDirectory(prefix='ocr-runtime-test-') as folder, patch.object(runtime, 'ROOT', Path(folder)):
            directory = runtime.runtime_directory()
            (directory/'rapidocr_onnxruntime').mkdir(parents=True)
            with patch.object(runtime.subprocess, 'run', return_value=SimpleNamespace(returncode=0, stdout=b'{"ready":true}')) as run:
                self.assertEqual(runtime.ensure_runtime(), directory)
            self.assertEqual(run.call_count, 1)
            self.assertIn('--health', run.call_args.args[0])
            self.assertIn('-I', run.call_args.args[0])

    def test_failed_setup_has_no_success_marker_and_is_retryable(self):
        with tempfile.TemporaryDirectory(prefix='ocr-runtime-test-') as folder, patch.object(runtime, 'ROOT', Path(folder)):
            with patch.object(runtime.subprocess, 'run', return_value=SimpleNamespace(returncode=1, stdout=b'', stderr=b'install failed')):
                with self.assertRaises(runtime.ImageOCRRuntimeError):
                    runtime.ensure_runtime()
            self.assertTrue(runtime.runtime_directory().exists())
            with patch.object(runtime.subprocess, 'run', side_effect=[
                    SimpleNamespace(returncode=0, stdout=b'', stderr=b''),
                    SimpleNamespace(returncode=0, stdout=b'{"ready":true}', stderr=b'')]):
                self.assertEqual(runtime.ensure_runtime(), runtime.runtime_directory())

    def test_image_transport_is_numeric_and_checks_result_count(self):
        engine = runtime.IsolatedRecognizer.__new__(runtime.IsolatedRecognizer)
        engine.directory = Path('isolated-ocr-test')
        crops = [np.zeros((12, 30, 3), dtype=np.uint8), np.ones((14, 80, 3), dtype=np.uint8)]
        with patch.object(runtime.subprocess, 'run', return_value=SimpleNamespace(returncode=0, stdout=json.dumps([['ABC123',.9],['0402 1K',.8]]).encode())) as run:
            self.assertEqual(len(engine.recognize_strips(crops)), 2)
            with np.load(io.BytesIO(run.call_args.kwargs['input']), allow_pickle=False) as payload:
                self.assertTrue(np.array_equal(payload['0'], crops[0]))
                self.assertEqual(payload['1'].dtype, np.uint8)
        with patch.object(runtime.subprocess, 'run', return_value=SimpleNamespace(returncode=0, stdout=b'[]')):
            with self.assertRaises(runtime.ImageOCRRuntimeError):
                engine.recognize_strips(crops)


if __name__ == '__main__':
    unittest.main()
