# src/utils/responsive.py
from enum import Enum
import flet as ft


class DeviceType(str, Enum):
    MOBILE = "mobile"
    TABLET = "tablet"
    DESKTOP = "desktop"


class ResponsiveLayout:
    """Helper class evaluating viewport breakpoints and adaptive dimensions."""

    @staticmethod
    def get_device_type(page: ft.Page) -> DeviceType:
        width = page.width if page and page.width else 1024
        if width < 600:
            return DeviceType.MOBILE
        elif width < 1024:
            return DeviceType.TABLET
        return DeviceType.DESKTOP

    @staticmethod
    def get_target_circle_size(page: ft.Page) -> float:
        width = page.width if page and page.width else 1024
        if width < 400:
            return 220.0
        elif width < 600:
            return 270.0
        elif width < 1024:
            return 320.0
        return 360.0

    @staticmethod
    def is_mobile(page: ft.Page) -> bool:
        return ResponsiveLayout.get_device_type(page) == DeviceType.MOBILE
