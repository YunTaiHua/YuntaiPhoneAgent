from types import SimpleNamespace

import pytest


class TestDashboardCoverageGaps:
    def test_input_text_changed_no_widget(self):
        from yuntai.views.dashboard import DashboardBuilder
        builder = DashboardBuilder.__new__(DashboardBuilder)
        builder.components = {}
        builder._on_input_text_changed()

    def test_input_text_changed_same_line_count(self):
        from yuntai.views.dashboard import DashboardBuilder
        builder = DashboardBuilder.__new__(DashboardBuilder)
        builder._last_line_count = 3
        widget = SimpleNamespace(toPlainText=lambda: "line1\nline2\nline3")
        builder.components = {"command_input": widget}
        builder._on_input_text_changed()

    def test_input_text_changed_attribute_error(self):
        from yuntai.views.dashboard import DashboardBuilder
        builder = DashboardBuilder.__new__(DashboardBuilder)
        builder._last_line_count = 1

        class BadWidget:
            def toPlainText(self):
                raise AttributeError("no such method")

        builder.components = {"command_input": BadWidget()}
        builder._on_input_text_changed()

    def test_input_text_changed_runtime_error(self):
        from yuntai.views.dashboard import DashboardBuilder
        builder = DashboardBuilder.__new__(DashboardBuilder)
        builder._last_line_count = 1

        class BadWidget:
            def toPlainText(self):
                raise RuntimeError("C++ object deleted")

        builder.components = {"command_input": BadWidget()}
        builder._on_input_text_changed()

    def test_input_text_changed_generic_exception(self):
        from yuntai.views.dashboard import DashboardBuilder
        builder = DashboardBuilder.__new__(DashboardBuilder)
        builder._last_line_count = 1

        class BadWidget:
            def toPlainText(self):
                raise ValueError("unexpected")

        builder.components = {"command_input": BadWidget()}
        builder._on_input_text_changed()

    def test_input_text_changed_height_below_minimum(self):
        from yuntai.views.dashboard import DashboardBuilder
        builder = DashboardBuilder.__new__(DashboardBuilder)
        builder._last_line_count = 3
        heights = []
        widget = SimpleNamespace(
            toPlainText=lambda: "x",
            setFixedHeight=lambda h: heights.append(h),
        )
        builder.components = {"command_input": widget}
        builder._on_input_text_changed()
        assert 42 in heights
