# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for FOR-BAZI backend.
Produces a single-folder distribution with all dependencies.
"""

import os
import sys
from pathlib import Path

block_cipher = None

PROJECT_ROOT = Path(SPECPATH)

a = Analysis(
    [str(PROJECT_ROOT / "backend" / "main.py")],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=[
        (str(PROJECT_ROOT / "prompts"), "prompts"),
        (str(PROJECT_ROOT / "data" / "classical_texts"), os.path.join("data", "classical_texts")),
    ],
    hiddenimports=[
        "engine",
        "engine.bazi_engine",
        "engine.shensha",
        "tools",
        "tools.bazi_tools",
        "tools.wuxing_calculator",
        "tools.geju_analyzer",
        "agent",
        "agent.react_agent",
        "agent.api_adapter",
        "agent.scholar_agent",
        "agent.context_manager",
        "prompts",
        "prompts.system_prompts",
        "prompts.ancient_texts",
        "backend",
        "backend.main",
        "backend.config",
        "backend.api.chart",
        "backend.api.chat",
        "backend.api.texts",
        "backend.api.compatibility",
        "backend.api.entertainment",
        "backend.schemas.common",
        "backend.schemas.chart",
        "backend.schemas.chat",
        "backend.services.bazi_service",
        "backend.services.agent_service",
        "backend.services.text_service",
        "data.rag_service",
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
        "sse_starlette",
        "lunar_python",
        "pydantic",
        "pydantic_settings",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "matplotlib", "tkinter", "scipy", "numpy.f2py",
        "IPython", "notebook", "jupyterlab",
        "transformers", "torch", "tensorflow",
        "chromadb", "sentence_transformers",
        "PyQt5", "PySide6", "PyQt6", "PySide2",
        "playwright", "numba", "llvmlite",
        "bokeh", "panel", "holoviews", "datashader",
        "jieba", "lac", "LAC",
        "win32com", "win32ui", "win32gui",
        "wx", "winsound",
        "PIL", "Pillow",
        "selenium", "requests_oauthlib",
        "grpc", "protobuf",
        "huggingface_hub", "hf_xet",
        "tokenizers", "tqdm",
        "sympy", "lxml", "cssselect",
        "pyarrow", "arrow",
        "lief",
        "psutil",
        "boto3", "botocore", "boto",
        "h5py", "hdf5",
        "azure", "google", "aws",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="bazi-backend",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name="bazi-backend",
)
