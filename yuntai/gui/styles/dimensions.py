"""
dimensions.py - 尺寸与间距常量定义
===================================

定义UI布局中使用的各种尺寸常量。

主要组件:
    - ThemeSpacing: 间距常量
    - ThemeCorner: 圆角常量
    - ThemeHeight: 高度常量
    - ThemeShadow: 阴影常量
    - DialogStyle: 弹窗样式常量
"""


class ThemeSpacing:
    """
    间距常量

    定义UI布局中使用的各种间距值（单位：像素）。
    """
    XS = 4   # 超小间距
    SM = 8   # 小间距
    MD = 16  # 中等间距
    LG = 24  # 大间距
    XL = 32  # 超大间距


class ThemeCorner:
    """
    圆角常量

    定义UI组件边框圆角半径值（单位：像素）。
    """
    SM = 8   # 小圆角（按钮、输入框等）
    MD = 12  # 中等圆角（卡片、对话框等）
    LG = 16  # 大圆角（遮罩层卡片等）


class ThemeHeight:
    """
    高度常量

    定义UI组件的标准高度值（单位：像素）。
    """
    BUTTON_SM = 32  # 小按钮高度
    BUTTON_MD = 40  # 中等按钮高度
    BUTTON_LG = 48  # 大按钮高度
    INPUT_SM = 36   # 小输入框高度
    INPUT_MD = 42   # 中等输入框高度


class ThemeShadow:
    """
    阴影常量 - 用于卡片立体感

    定义UI组件的阴影效果参数。
    每个阴影配置为元组: (x_offset, y_offset, blur_radius, color_rgba)

    浅色主题阴影使用较低的透明度，深色主题使用较高的透明度。
    """
    # 浅色主题阴影 (使用rgba格式，alpha值为0-255)
    LIGHT_SM = (0, 1, 3, (0, 0, 0, 20))      # 小阴影 (0.08 * 255 ≈ 20)
    LIGHT_MD = (0, 2, 8, (0, 0, 0, 26))      # 中等阴影 (0.10 * 255 ≈ 26)
    LIGHT_LG = (0, 4, 12, (0, 0, 0, 31))     # 大阴影 (0.12 * 255 ≈ 31)

    # 深色主题阴影
    DARK_SM = (0, 1, 3, (0, 0, 0, 64))       # (0.25 * 255 ≈ 64)
    DARK_MD = (0, 2, 8, (0, 0, 0, 77))       # (0.30 * 255 ≈ 77)
    DARK_LG = (0, 4, 12, (0, 0, 0, 89))      # (0.35 * 255 ≈ 89)


class DialogStyle:
    """弹窗样式常量"""
    # 弹窗尺寸
    DIALOG_WIDTH_SMALL = 400
    DIALOG_HEIGHT_SMALL = 350
    DIALOG_WIDTH_MEDIUM = 500
    DIALOG_HEIGHT_MEDIUM = 450
    DIALOG_WIDTH_LARGE = 600
    DIALOG_HEIGHT_LARGE = 500

    # 弹窗内边距
    DIALOG_MARGIN = 20
    DIALOG_SPACING = 12

    # 按钮尺寸
    BUTTON_HEIGHT = 40
    BUTTON_WIDTH = 120
    BUTTON_HEIGHT_SMALL = 36
    BUTTON_WIDTH_SMALL = 100

    # ==================== 连接处理器 GUI 常量 ====================
    # 对话框内容区域边距（像素）
    CONTENT_MARGIN: int = 15

    # 设备布局间距（像素）
    DEVICE_LAYOUT_SPACING: int = 8

    # 文本框分隔线长度（字符数）
    TEXT_SEPARATOR_LENGTH: int = 50

    # 按钮额外宽度偏移量（像素）
    BUTTON_WIDTH_OFFSET: int = 20

    # 状态指示器内边距（CSS 格式）
    STATUS_INDICATOR_PADDING: str = "4px 8px"

    # 连接状态标签字体大小（像素）
    CONNECTION_STATUS_FONT_SIZE: int = 24
