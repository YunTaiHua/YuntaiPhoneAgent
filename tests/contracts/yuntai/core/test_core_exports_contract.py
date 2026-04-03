from yuntai import core


def test_core_module_contract_exports_are_present():
    for name in ["Utils", "MainApp", "AgentExecutor", "validate_config", "print_config_summary"]:
        assert hasattr(core, name)
    assert "MainApp" in core.__all__
