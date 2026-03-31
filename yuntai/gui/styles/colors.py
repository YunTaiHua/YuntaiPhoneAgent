"""
colors.py - 主题颜色定义
========================

定义浅色和深色主题的颜色常量。

主要组件:
    - ThemeColors: 浅色主题颜色常量
    - DarkThemeColors: 深色主题颜色常量
    - get_theme_colors: 获取当前主题颜色
"""


class ThemeColors:
    """
    现代化浅色UI主题颜色类 - 米白色风格

    定义浅色主题下所有UI组件使用的颜色常量。
    采用柔和的蓝色系作为主色调，米白色作为背景色。

    颜色分类:
        - 主色调: PRIMARY, SECONDARY, ACCENT
        - 功能色: SUCCESS, WARNING, DANGER
        - 状态色: STATUS_ACTIVE, STATUS_INACTIVE
        - 背景色: BG_MAIN, BG_NAV, BG_CARD等
        - 边框色: BORDER_LIGHT, BORDER_MEDIUM, BORDER_FOCUS
        - 文字色: TEXT_PRIMARY, TEXT_SECONDARY, TEXT_DISABLED
    """
    # 主色调 - 柔和的蓝色系
    PRIMARY = "#5B8DEE"          # 主按钮色 - 柔和蓝
    PRIMARY_HOVER = "#4A7BDD"     # 主按钮悬停色（稍深提升对比度）
    SECONDARY = "#A78BFA"        # 次要按钮色 - 亮紫色
    SECONDARY_HOVER = "#8B5CF6"   # 次要按钮悬停色
    ACCENT = "#F97316"           # 强调色 - 活力橙
    ACCENT_HOVER = "#EA580C"      # 强调色悬停

    # 功能色
    SUCCESS = "#22C55E"          # 成功 - 标准绿
    SUCCESS_HOVER = "#16A34A"     # 成功悬停
    WARNING = "#F59E0B"          # 警告 - 琥珀色
    WARNING_HOVER = "#D97706"     # 警告悬停
    DANGER = "#EF4444"           # 危险 - 标准红
    DANGER_HOVER = "#DC2626"      # 危险悬停

    # 状态指示色 - 浅蓝色系（用于导航栏状态和toast）
    STATUS_ACTIVE = "#64D2FF"     # 激活状态 - 清新透亮的天蓝色
    STATUS_INACTIVE = "#9CA3AF"   # 未激活状态 - 灰色

    # 背景色 - 更纯净的米白色系
    BG_MAIN = "#FDFCFA"          # 主背景 - 暖白
    BG_NAV = "#FFFFFF"           # 导航栏背景 - 纯白
    BG_CARD = "#FFFFFF"          # 卡片背景 - 纯白
    BG_CARD_ALT = "#F8F7F5"      # 卡片背景替代 - 浅灰米白
    BG_HOVER = "#F0EFE9"         # 悬停背景 - 浅米色
    BG_INPUT = "#FFFFFF"         # 输入框背景
    BG_SCROLLBAR = "#E0DDD8"     # 滚动条背景

    # 边框色
    BORDER_LIGHT = "#E5E3E0"     # 浅色边框
    BORDER_MEDIUM = "#D0CDC7"    # 中等边框
    BORDER_FOCUS = "#5B8DEE"     # 聚焦边框

    # 文字色
    TEXT_PRIMARY = "#2C3E50"     # 主文字 - 深蓝灰
    TEXT_SECONDARY = "#6B7280"   # 次要文字 - 中灰
    TEXT_DISABLED = "#9CA3AF"    # 禁用文字 - 浅灰
    TEXT_LIGHT = "#FFFFFF"       # 浅色文字（用于深色背景按钮）

    # 特殊颜色
    NAV_HIGHLIGHT_BG = "#EFF3FF"
    NAV_HIGHLIGHT_HOVER = "#E0E7FF"
    OPTION_BUTTON_COLOR = "#C4C9D0"
    OPTION_BUTTON_HOVER = "#A8AEB5"


class DarkThemeColors:
    """
    深色主题颜色类

    定义深色主题下所有UI组件使用的颜色常量。
    采用深蓝色系作为背景色，保持与浅色主题一致的功能色。

    颜色分类:
        - 主色调: PRIMARY, SECONDARY, ACCENT
        - 功能色: SUCCESS, WARNING, DANGER
        - 状态色: STATUS_ACTIVE, STATUS_INACTIVE
        - 背景色: BG_MAIN, BG_NAV, BG_CARD等
        - 边框色: BORDER_LIGHT, BORDER_MEDIUM, BORDER_FOCUS
        - 文字色: TEXT_PRIMARY, TEXT_SECONDARY, TEXT_DISABLED
    """
    # 主色调
    PRIMARY = "#60A5FA"
    PRIMARY_HOVER = "#3B82F6"
    SECONDARY = "#A78BFA"
    SECONDARY_HOVER = "#8B5CF6"
    ACCENT = "#FB923C"
    ACCENT_HOVER = "#F97316"

    # 功能色
    SUCCESS = "#22C55E"
    SUCCESS_HOVER = "#16A34A"
    WARNING = "#F59E0B"
    WARNING_HOVER = "#D97706"
    DANGER = "#EF4444"
    DANGER_HOVER = "#DC2626"

    # 状态指示色 - 浅蓝色系（用于导航栏状态和toast）
    STATUS_ACTIVE = "#64D2FF"     # 激活状态 - 清新透亮的天蓝色
    STATUS_INACTIVE = "#6B7280"   # 未激活状态 - 灰色

    # 背景色
    BG_MAIN = "#1A1A2E"
    BG_NAV = "#16213E"
    BG_CARD = "#1F2937"
    BG_CARD_ALT = "#374151"
    BG_HOVER = "#2D3748"
    BG_INPUT = "#1F2937"
    BG_SCROLLBAR = "#4B5563"

    # 边框色
    BORDER_LIGHT = "#374151"
    BORDER_MEDIUM = "#4B5563"
    BORDER_FOCUS = "#60A5FA"

    # 文字色
    TEXT_PRIMARY = "#F3F4F6"
    TEXT_SECONDARY = "#9CA3AF"
    TEXT_DISABLED = "#6B7280"
    TEXT_LIGHT = "#FFFFFF"

    # 特殊颜色
    NAV_HIGHLIGHT_BG = "#1E3A5F"      # 导航高光背景 - 深蓝色，与PRIMARY文字形成对比
    NAV_HIGHLIGHT_HOVER = "#2D4A6F"   # 导航高光悬停 - 稍浅的深蓝色
    OPTION_BUTTON_COLOR = "#4B5563"
    OPTION_BUTTON_HOVER = "#6B7280"


def get_theme_colors(is_dark=False):
    """
    获取当前主题颜色

    Args:
        is_dark: 是否使用深色主题，默认False

    Returns:
        ThemeColors或DarkThemeColors类
    """
    return DarkThemeColors if is_dark else ThemeColors
