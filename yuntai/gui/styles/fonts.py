"""
fonts.py - 字体常量定义
=======================

定义UI组件使用的字体族和字体大小。
主要使用微软雅黑作为主字体，Consolas作为代码字体。

主要组件:
    - ThemeFonts: 字体常量类
"""

from PyQt6.QtGui import QFont


class ThemeFonts:
    """
    字体常量

    定义UI组件使用的字体族和字体大小。
    主要使用微软雅黑作为主字体，Consolas作为代码字体。

    字体分类:
        - 主字体: Microsoft YaHei
        - Emoji字体: Segoe UI Emoji
        - 代码字体: Consolas
        - 标题字体: TITLE_LARGE, TITLE_MEDIUM, TITLE_SMALL
        - 正文字体: BODY_LARGE, BODY_MEDIUM, BODY_SMALL等
    """
    # 主字体
    FONT_FAMILY = "Microsoft YaHei"
    FONT_FAMILY_EMOJI = "Segoe UI Emoji"
    FONT_FAMILY_CODE = "Consolas"

    # 标题字体
    TITLE_LARGE = QFont(FONT_FAMILY, 28, QFont.Weight.Bold)
    TITLE_MEDIUM = QFont(FONT_FAMILY, 24, QFont.Weight.Bold)
    TITLE_SMALL = QFont(FONT_FAMILY, 18, QFont.Weight.Bold)

    # 常用别名
    TITLE = QFont(FONT_FAMILY, 20, QFont.Weight.Bold)  # 标题
    SUBTITLE = QFont(FONT_FAMILY, 16, QFont.Weight.Bold)  # 副标题

    # 正文字体
    BODY_LARGE = QFont(FONT_FAMILY, 16)
    BODY_MEDIUM = QFont(FONT_FAMILY, 14)
    BODY_SMALL = QFont(FONT_FAMILY, 13)
    BODY_XSMALL = QFont(FONT_FAMILY, 12)
    BODY_TINY = QFont(FONT_FAMILY, 11)
    BODY_MINI = QFont(FONT_FAMILY, 10)

    # 常用别名
    BODY = QFont(FONT_FAMILY, 14)  # 正文

    # 代码字体
    CODE_MEDIUM = QFont(FONT_FAMILY_CODE, 13)
    CODE_SMALL = QFont(FONT_FAMILY_CODE, 12)

    # Emoji字体
    EMOJI_LARGE = QFont(FONT_FAMILY_EMOJI, 40)
    EMOJI_MEDIUM = QFont(FONT_FAMILY_EMOJI, 14)
    EMOJI_SMALL = QFont(FONT_FAMILY_EMOJI, 12)
