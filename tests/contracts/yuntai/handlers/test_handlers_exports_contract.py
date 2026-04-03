from yuntai import handlers


def test_handlers_module_exports_expected_symbols():
    expected = {"ConnectionHandler", "TTSHandler", "DynamicHandler", "SystemHandler"}
    assert set(handlers.__all__) == expected
    for name in expected:
        assert hasattr(handlers, name)
