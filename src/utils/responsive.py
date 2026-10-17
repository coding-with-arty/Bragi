from enum import Enum
import flet as ft


class DeviceType(Enum):
    MOBILE = "Mobile"      # Screen width < 600px
    TABLET = "Tablet"      # Screen width 600px - 1024px
    DESKTOP = "Desktop"    # Screen width > 1024px


class ResponsiveLayout:
    """
    Evaluates viewport window breakpoints and provides dynamic dimension
    calculations for responsive UI rendering.
    """

    @staticmethod
    def get_device_type(page: ft.Page) -> DeviceType:
        """Determines current device category based on page width."""
        width = page.width if page and page.width else 1024.0

        if width < 600:
            return DeviceType.MOBILE
        elif width <= 1024:
            return DeviceType.TABLET
        else:
            return DeviceType.DESKTOP

    @staticmethod
    def get_target_display_size(page: ft.Page) -> float:
        """Calculates adaptive target display circle diameter."""
        device = ResponsiveLayout.get_device_type(page)

        if device == DeviceType.MOBILE:
            return 220.0
        elif device == DeviceType.TABLET:
            return 280.0
        else:
            return 340.0

    @staticmethod
    def get_sidebar_width(page: ft.Page) -> float:
        """Returns adaptive width for drawer and sidebar panels."""
        device = ResponsiveLayout.get_device_type(page)

        if device == DeviceType.MOBILE:
            return page.width * 0.90 if page and page.width else 300.0
        elif device == DeviceType.TABLET:
            return 280.0
        else:
            return 320.0
