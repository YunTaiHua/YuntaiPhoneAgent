"""
ThemeColors - UI主题颜色定义
浅色米白色现代化主题
"""


class ThemeColors:
    """现代化浅色UI主题颜色类 - 米白色风格"""
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


class ThemeSpacing:
    """间距常量"""
    XS = 4
    SM = 8
    MD = 16
    LG = 24
    XL = 32


class ThemeCorner:
    """圆角常量"""
    SM = 8
    MD = 12
    LG = 16


class ThemeHeight:
    """高度常量"""
    BUTTON_SM = 32
    BUTTON_MD = 40
    BUTTON_LG = 48
    INPUT_SM = 36
    INPUT_MD = 42


class DarkThemeColors:
    """深色主题颜色类"""
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
    NAV_HIGHLIGHT_BG = "#60A5FA"
    NAV_HIGHLIGHT_HOVER = "#3B82F6"
    OPTION_BUTTON_COLOR = "#4B5563"
    OPTION_BUTTON_HOVER = "#6B7280"


def get_theme_colors(is_dark=False):
    """获取当前主题颜色"""
    return DarkThemeColors if is_dark else ThemeColors
