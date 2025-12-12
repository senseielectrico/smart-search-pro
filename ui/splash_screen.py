"""
Splash screen for application startup.

Displays loading progress while initializing heavy components.
"""

from PyQt6.QtWidgets import QSplashScreen, QLabel, QProgressBar, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont, QLinearGradient
from typing import Optional


class ModernSplashScreen(QSplashScreen):
    """Modern splash screen with progress bar and status messages"""

    progress_updated = pyqtSignal(int, str)

    def __init__(self, width: int = 500, height: int = 300):
        # Create custom pixmap
        pixmap = self._create_splash_pixmap(width, height)
        super().__init__(pixmap, Qt.WindowType.WindowStaysOnTopHint)

        # Remove window frame
        self.setWindowFlags(
            Qt.WindowType.SplashScreen |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )

        self._current_progress = 0
        self._current_message = "Initializing..."

        # Setup auto-close timer (safety fallback)
        self._timeout_timer = QTimer(self)
        self._timeout_timer.timeout.connect(self.close)
        self._timeout_timer.setSingleShot(True)
        self._timeout_timer.start(10000)  # 10 second max

    def _create_splash_pixmap(self, width: int, height: int) -> QPixmap:
        """Create modern splash screen design"""
        pixmap = QPixmap(width, height)
        pixmap.fill(QColor(30, 30, 30))  # Dark background

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Gradient background
        gradient = QLinearGradient(0, 0, 0, height)
        gradient.setColorAt(0, QColor(40, 40, 50))
        gradient.setColorAt(1, QColor(20, 20, 30))
        painter.fillRect(0, 0, width, height, gradient)

        # Draw logo/icon area
        logo_size = 80
        logo_x = (width - logo_size) // 2
        logo_y = 60

        # Search icon (magnifying glass)
        painter.setBrush(QColor(0, 120, 212))  # Windows blue
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(logo_x, logo_y, logo_size, logo_size)

        # Inner circle (lens)
        painter.setBrush(QColor(255, 255, 255, 200))
        painter.drawEllipse(logo_x + 15, logo_y + 15, 35, 35)

        # Handle
        painter.setPen(QColor(255, 255, 255))
        painter.setBrush(QColor(255, 255, 255))
        from PyQt6.QtCore import QPoint
        painter.drawEllipse(QPoint(logo_x + 60, logo_y + 60), 8, 8)

        # Title
        title_font = QFont("Segoe UI", 24, QFont.Weight.Bold)
        painter.setFont(title_font)
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(0, logo_y + logo_size + 30, width, 40,
                        Qt.AlignmentFlag.AlignCenter, "Smart Search Pro")

        # Version
        version_font = QFont("Segoe UI", 10)
        painter.setFont(version_font)
        painter.setPen(QColor(180, 180, 180))
        painter.drawText(0, logo_y + logo_size + 65, width, 20,
                        Qt.AlignmentFlag.AlignCenter, "Version 2.0.0")

        painter.end()
        return pixmap

    def show_progress(self, progress: int, message: str = ""):
        """
        Update progress and message.

        Args:
            progress: Progress percentage (0-100)
            message: Status message
        """
        self._current_progress = max(0, min(100, progress))
        if message:
            self._current_message = message

        self.showMessage(
            f"{self._current_message}\n{self._current_progress}%",
            Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
            QColor(255, 255, 255)
        )

        # Process events to update display
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()

    def finish_loading(self, main_window):
        """
        Finish splash screen and show main window.

        Args:
            main_window: Main application window
        """
        self.show_progress(100, "Ready!")
        self.finish(main_window)

    def drawContents(self, painter: QPainter):
        """Custom draw for progress bar"""
        super().drawContents(painter)

        # Draw progress bar
        bar_width = self.width() - 100
        bar_height = 4
        bar_x = 50
        bar_y = self.height() - 50

        # Background
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(60, 60, 60))
        painter.drawRoundedRect(bar_x, bar_y, bar_width, bar_height, 2, 2)

        # Progress
        if self._current_progress > 0:
            progress_width = int(bar_width * (self._current_progress / 100))
            painter.setBrush(QColor(0, 120, 212))
            painter.drawRoundedRect(bar_x, bar_y, progress_width, bar_height, 2, 2)


class SplashScreenManager:
    """
    Manager for splash screen lifecycle.

    Provides convenient methods for showing progress during startup.
    """

    def __init__(self):
        self.splash: Optional[ModernSplashScreen] = None
        self._total_steps = 100
        self._current_step = 0

    def show(self, total_steps: int = 10):
        """
        Show splash screen.

        Args:
            total_steps: Total number of initialization steps
        """
        self.splash = ModernSplashScreen()
        self.splash.show()
        self._total_steps = max(1, total_steps)
        self._current_step = 0

        # Initial message
        self.splash.show_progress(0, "Starting Smart Search Pro...")

    def update(self, message: str):
        """
        Update progress with message.

        Args:
            message: Status message
        """
        if not self.splash:
            return

        self._current_step += 1
        progress = int((self._current_step / self._total_steps) * 100)
        self.splash.show_progress(progress, message)

    def set_progress(self, progress: int, message: str):
        """
        Set explicit progress value.

        Args:
            progress: Progress percentage (0-100)
            message: Status message
        """
        if self.splash:
            self.splash.show_progress(progress, message)

    def finish(self, main_window):
        """
        Finish splash and show main window.

        Args:
            main_window: Main application window
        """
        if self.splash:
            self.splash.finish_loading(main_window)
            self.splash = None

    def close(self):
        """Close splash screen immediately"""
        if self.splash:
            self.splash.close()
            self.splash = None
