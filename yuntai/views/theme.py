"""
ThemeColors - UI主题颜色定义
浅色米白色现代化主题
"""


class ThemeColors:
    """现代化浅色UI主题颜色类 - 米白色风格"""
    # 主色调 - 柔和的蓝色系
    PRIMARY = "#5B8DEE"          # 主按钮色 - 柔和蓝
    PRIMARY_HOVER = "#4A7BD4"    # 主按钮悬停色
    SECONDARY = "#9B7ED9"        # 次要按钮色 - 淡紫
    SECONDARY_HOVER = "#8A6BC8"  # 次要按钮悬停色
    ACCENT = "#FF8C69"           # 强调色 - 珊瑚橙
    ACCENT_HOVER = "#F27A56"     # 强调色悬停
    
    # 功能色
    SUCCESS = "#6BCB77"          # 成功 - 柔和绿
    SUCCESS_HOVER = "#5AB866"    # 成功悬停
    WARNING = "#FFB84D"          # 警告 - 暖黄
    WARNING_HOVER = "#F0A93C"    # 警告悬停
    DANGER = "#FF6B6B"           # 危险 - 柔和红
    DANGER_HOVER = "#E85A5A"     # 危险悬停
    
    # 背景色 - 米白色系
    BG_MAIN = "#FAF8F5"          # 主背景 - 暖白
    BG_NAV = "#FFFFFF"           # 导航栏背景 - 纯白
    BG_CARD = "#FFFFFF"          # 卡片背景 - 纯白
    BG_CARD_ALT = "#F5F3F0"      # 卡片背景替代 - 浅灰米白
    BG_HOVER = "#F0EDE8"         # 悬停背景 - 浅米色
    BG_INPUT = "#FFFFFF"         # 输入框背景
    BG_SCROLLBAR = "#E0DDD8"     # 滚动条背景
    
    # 边框色
    BORDER_LIGHT = "#E8E5E0"     # 浅色边框
    BORDER_MEDIUM = "#D8D5D0"    # 中等边框
    BORDER_FOCUS = "#5B8DEE"     # 聚焦边框
    
    # 文字色
    TEXT_PRIMARY = "#2C3E50"     # 主文字 - 深蓝灰
    TEXT_SECONDARY = "#6B7280"   # 次要文字 - 中灰
    TEXT_DISABLED = "#A0A0A0"    # 禁用文字 - 浅灰
    TEXT_LIGHT = "#FFFFFF"       # 浅色文字（用于深色背景按钮）
    
    # 阴影色（用于卡片效果）
    SHADOW = "#00000010"         # 微弱阴影
    SHADOW_MEDIUM = "#0000001A"  # 中等阴影
    
    # 保留旧颜色名称以兼容现有代码（映射到新颜色）
    BG_DARK = BG_MAIN            # 兼容旧代码
