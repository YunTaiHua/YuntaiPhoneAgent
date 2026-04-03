from pathlib import Path


def _gpt_sovits_dir() -> Path:
    return Path(__file__).resolve().parents[4] / "yuntai" / "managers" / "gpt_sovits_custom"


def _has_python_syntax(path: Path) -> bool:
    source = path.read_text(encoding="utf-8")
    compile(source, str(path), "exec")
    return True


def test_gpt_sovits_package_file_has_valid_syntax():
    path = _gpt_sovits_dir() / "__init__.py"
    assert path.exists()
    assert _has_python_syntax(path)


def test_gpt_sovits_t2s_model_file_has_valid_syntax():
    path = _gpt_sovits_dir() / "t2s_model.py"
    assert path.exists()
    assert _has_python_syntax(path)


def test_gpt_sovits_t2s_lightning_file_has_valid_syntax():
    path = _gpt_sovits_dir() / "t2s_lightning_module.py"
    assert path.exists()
    assert _has_python_syntax(path)


def test_gpt_sovits_inference_webui_file_has_valid_syntax():
    path = _gpt_sovits_dir() / "inference_webui.py"
    assert path.exists()
    assert _has_python_syntax(path)
