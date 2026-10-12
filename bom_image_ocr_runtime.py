"""App-scoped CPU OCR environment for hosts that miss deployment dependencies."""
from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import threading


ROOT = Path(__file__).resolve().parent
PACKAGES = (
    'rapidocr-onnxruntime==1.2.3', 'onnxruntime>=1.18,<2',
    'opencv-python-headless>=4.10,<5', 'numpy>=1.26,<3',
    'Pillow>=10.4,<12', 'pyclipper>=1.3,<2', 'Shapely>=2,<3',
    'PyYAML>=6,<7', 'six>=1.15,<2', 'flatbuffers>=24',
    'packaging>=21', 'protobuf>=3.20,<6', 'sympy>=1.12,<2', 'mpmath>=1.1,<2',
    'coloredlogs>=15,<16', 'humanfriendly>=9,<11',
)
LOCK = threading.Lock()


class ImageOCRRuntimeError(RuntimeError):
    pass


def runtime_directory():
    signature = hashlib.sha256('|'.join(PACKAGES).encode()).hexdigest()[:12]
    folder = ROOT / 'cache' / f'bom-image-ocr-py{sys.version_info.major}{sys.version_info.minor}-{signature}'
    resolved = folder.resolve()
    if resolved.parent != (ROOT / 'cache').resolve() or not resolved.name.startswith('bom-image-ocr-'):
        raise RuntimeError('Invalid OCR runtime directory')
    return resolved


def worker_command(directory, *, health=False):
    args = [sys.executable, '-I', str(ROOT/'bom_image_ocr_worker.py'), '--packages', str(directory)]
    return args + (['--health'] if health else [])


def probe(directory):
    try:
        result = subprocess.run(worker_command(directory, health=True), capture_output=True,
                                timeout=45, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return False
    if result.returncode != 0:
        return False
    try:
        return json.loads(result.stdout)['ready'] is True
    except (ValueError, KeyError):
        return False


def ensure_runtime():
    directory = runtime_directory()
    with LOCK:
        if (directory/'rapidocr_onnxruntime').exists() and probe(directory):
            return directory
        directory.mkdir(parents=True, exist_ok=True)
        # Install only this feature's libraries into its dedicated directory;
        # --no-deps plus the explicit list avoids adding GUI OpenCV or updating
        # the web application's environment. Wheels/models come from PyPI.
        pip_entry = ['-m', 'pip']
        if os.name == 'nt' and sys.version_info >= (3,14):
            pip_entry = ['-c', 'import platform; platform._wmi=None; from pip._internal.cli.main import main; raise SystemExit(main())']
        command = [sys.executable, *pip_entry, 'install', '--disable-pip-version-check',
                   '--no-input', '--only-binary=:all:', '--no-deps', '--upgrade',
                   '--index-url', 'https://pypi.org/simple', '--target', str(directory), *PACKAGES]
        env = os.environ.copy()
        env['PIP_CONFIG_FILE'] = os.devnull
        try:
            result = subprocess.run(command, env=env, capture_output=True, timeout=180, check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ImageOCRRuntimeError('图片识别服务尚未就绪，请稍后重新上传图片。') from exc
        if result.returncode != 0 or not probe(directory):
            raise ImageOCRRuntimeError('图片识别服务尚未就绪，请稍后重新上传图片。')
    return directory


class IsolatedRecognizer:
    def __init__(self):
        self.directory = ensure_runtime()

    def recognize_strips(self, crops):
        import numpy as np
        payload = io.BytesIO()
        np.savez_compressed(payload, **{str(idx): crop for idx, crop in enumerate(crops)})
        try:
            result = subprocess.run(worker_command(self.directory), input=payload.getvalue(),
                                    capture_output=True, timeout=120, check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ImageOCRRuntimeError('图片识别未完成，请重新上传图片。') from exc
        if result.returncode != 0:
            raise ImageOCRRuntimeError('图片识别未完成，请重新上传图片。')
        try:
            records = json.loads(result.stdout)
        except ValueError as exc:
            raise ImageOCRRuntimeError('图片识别未完成，请重新上传图片。') from exc
        if len(records) != len(crops):
            raise ImageOCRRuntimeError('图片识别结果不完整，请重新上传图片。')
        return records
