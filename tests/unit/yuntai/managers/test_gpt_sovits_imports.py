from pathlib import Path
import importlib
import sys
import types


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


def test_gpt_sovits_custom_init_success_and_import_error(monkeypatch):
    pkg = "yuntai.managers.gpt_sovits_custom"
    dep = "yuntai.managers.gpt_sovits_custom.inference_webui"

    ok_dep = types.ModuleType(dep)
    ok_dep.get_tts_wav = object()
    ok_dep.change_gpt_weights = object()
    ok_dep.change_sovits_weights = object()
    ok_dep.I18nAuto = object()

    monkeypatch.setitem(sys.modules, dep, ok_dep)
    monkeypatch.delitem(sys.modules, pkg, raising=False)
    mod = importlib.import_module(pkg)
    assert mod.get_tts_wav is ok_dep.get_tts_wav
    assert "I18nAuto" in mod.__all__

    bad_dep = types.ModuleType(dep)
    monkeypatch.setitem(sys.modules, dep, bad_dep)
    monkeypatch.delitem(sys.modules, pkg, raising=False)
    mod2 = importlib.import_module(pkg)
    assert mod2.get_tts_wav is None
    assert mod2.change_gpt_weights is None
    assert mod2.change_sovits_weights is None
    assert mod2.I18nAuto is None
