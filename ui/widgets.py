"""
Custom Widgets - Reusable UI components
"""

from typing import List, Optional
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QPushButton, QLabel, QHBoxLayout, QVBoxLayout,
    QProgressBar, QFrame, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QIcon, QPainter, QColor, QPen, QBrush, QLinearGradient, QFont


class FilterChip(QWidget):
    """Modern filter chip button"""
    clicked = pyqtSignal()
    removed = pyqtSignal()

    def __init__(self, text: str, removable: bool = True, parent=None):
        super().__init__(parent)
        self.text = text
        self.removable = removable
        self._active = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(4)

        # Text label
        self.label = QLabel(text)
        self.label.setStyleSheet("background: transparent; padding: 2px;")
        layout.addWidget(self.label)

        # Remove button
        if removable:
            self.remove_btn = QPushButton("×")
            self.remove_btn.setFixedSize(16, 16)
            self.remove_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    color: #605E5C;
                    font-size: 14pt;
                    font-weight: bold;
                    padding: 0;
                }
                QPushButton:hover {
                    color: #000000;
                }
            """)
            self.remove_btn.clicked.connect(self.removed.emit)
            layout.addWidget(self.remove_btn)

        self._update_style()

    def setActive(self, active: bool):
        """Set active state"""
        self._active = active
        self._update_style()

    def isActive(self) -> bool:
        """Get active state"""
        return self._active

    def _update_style(self):
        """Update visual style"""
        if self._active:
            bg_color = "#0078D4"
            text_color = "#FFFFFF"
        else:
            bg_color = "#F3F3F3"
            text_color = "#000000"

        self.setStyleSheet(f"""
            FilterChip {{
                background-color: {bg_color};
                border-radius: 12px;
                border: 1px solid #E1DFDD;
            }}
            FilterChip:hover {{
                background-color: {"#106EBE" if self._active else "#E1DFDD"};
            }}
        """)
        self.label.setStyleSheet(f"background: transparent; color: {text_color}; padding: 2px;")

    def mousePressEvent(self, event):
        """Handle click"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class SpeedGraph(QWidget):
    """Real-time speed graph widget"""

    def __init__(self, max_points: int = 50, parent=None):
        super().__init__(parent)
        self.setMinimumSize(200, 60)
        self.max_points = max_points
        self.data_points: List[float] = []
        self.max_value = 1.0

    def add_data_point(self, value: float):
        """Add new data point"""
        self.data_points.append(value)
        if len(self.data_points) > self.max_points:
            self.data_points.pop(0)

        # Update max value for scaling
        if self.data_points:
            self.max_value = max(max(self.data_points), 1.0)

        self.update()

    def clear(self):
        """Clear all data"""
        self.data_points.clear()
        self.max_value = 1.0
        self.update()

    def paintEvent(self, event):
        """Paint the graph"""
        if not self.data_points:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw background
        painter.fillRect(self.rect(), QColor("#F9F9F9"))

        # Calculate dimensions
        width = self.width()
        height = self.height()
        point_spacing = width / max(len(self.data_points) - 1, 1)

        # Draw grid lines
        painter.setPen(QPen(QColor("#E1DFDD"), 1))
        for i in range(5):
            y = height * i / 4
            painter.drawLine(0, int(y), width, int(y))

        # Draw gradient area under line
        if len(self.data_points) > 1:
            gradient = QLinearGradient(0, 0, 0, height)
            gradient.setColorAt(0, QColor(0, 120, 212, 100))
            gradient.setColorAt(1, QColor(0, 120, 212, 10))

            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.PenStyle.NoPen)

            # Create polygon for area
            from PyQt6.QtGui import QPolygon
            from PyQt6.QtCore import QPoint

            polygon = QPolygon()
            polygon.append(QPoint(0, height))

            for i, value in enumerate(self.data_points):
                x = int(i * point_spacing)
                y = int(height - (value / self.max_value * height))
                polygon.append(QPoint(x, y))

            polygon.append(QPoint(width, height))
            painter.drawPolygon(polygon)

        # Draw line
        painter.setPen(QPen(QColor("#0078D4"), 2))
        for i in range(len(self.data_points) - 1):
            x1 = int(i * point_spacing)
            y1 = int(height - (self.data_points[i] / self.max_value * height))
            x2 = int((i + 1) * point_spacing)
            y2 = int(height - (self.data_points[i + 1] / self.max_value * height))
            painter.drawLine(x1, y1, x2, y2)


class BreadcrumbBar(QWidget):
    """Breadcrumb navigation bar"""
    path_clicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(4, 4, 4, 4)
        self.layout.setSpacing(4)
        self.layout.addStretch()

        self.current_path = ""

    def set_path(self, path: str):
        """Set current path and update breadcrumbs"""
        self.current_path = path

        # Clear existing widgets
        while self.layout.count() > 1:
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not path:
            return

        # Split path into parts
        parts = Path(path).parts

        for i, part in enumerate(parts):
            # Create button for each part
            btn = QPushButton(part)
            btn.setFlat(True)
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    padding: 4px 8px;
                    text-align: left;
                }
                QPushButton:hover {
                    background-color: #E1DFDD;
                    border-radius: 4px;
                }
            """)

            # Build full path up to this part
            full_path = str(Path(*parts[:i+1]))
            btn.clicked.connect(lambda checked, p=full_path: self.path_clicked.emit(p))

            self.layout.insertWidget(i * 2, btn)

            # Add separator (except after last item)
            if i < len(parts) - 1:
                separator = QLabel(">")
                separator.setStyleSheet("color: #8A8886; background: transparent;")
                self.layout.insertWidget(i * 2 + 1, separator)


class ProgressCard(QWidget):
    """Progress card for file operations"""
    cancel_clicked = pyqtSignal()
    pause_clicked = pyqtSignal()

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(300)

        # Add shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        # Title row
        title_row = QHBoxLayout()
        self.title_label = QLabel(title)
        self.title_label.setProperty("subheading", True)
        title_row.addWidget(self.title_label)
        title_row.addStretch()

        # Pause button
        self.pause_btn = QPushButton("⏸")
        self.pause_btn.setFixedSize(24, 24)
        self.pause_btn.setProperty("secondary", True)
        self.pause_btn.clicked.connect(self.pause_clicked.emit)
        title_row.addWidget(self.pause_btn)

        # Cancel button
        self.cancel_btn = QPushButton("✕")
        self.cancel_btn.setFixedSize(24, 24)
        self.cancel_btn.setProperty("secondary", True)
        self.cancel_btn.clicked.connect(self.cancel_clicked.emit)
        title_row.addWidget(self.cancel_btn)

        layout.addLayout(title_row)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        layout.addWidget(self.progress_bar)

        # Status row
        status_row = QHBoxLayout()
        self.status_label = QLabel("Preparing...")
        self.status_label.setStyleSheet("color: #605E5C;")
        status_row.addWidget(self.status_label)
        status_row.addStretch()

        self.speed_label = QLabel("")
        self.speed_label.setStyleSheet("color: #605E5C;")
        status_row.addWidget(self.speed_label)

        layout.addLayout(status_row)

        # Details label
        self.details_label = QLabel("")
        self.details_label.setStyleSheet("color: #8A8886; font-size: 8pt;")
        self.details_label.setWordWrap(True)
        layout.addWidget(self.details_label)

        self.setStyleSheet("""
            ProgressCard {
                background-color: white;
                border: 1px solid #E1DFDD;
                border-radius: 8px;
            }
        """)

    def set_progress(self, value: int):
        """Set progress value (0-100)"""
        self.progress_bar.setValue(value)

    def set_status(self, text: str):
        """Set status text"""
        self.status_label.setText(text)

    def set_speed(self, speed: str):
        """Set speed text"""
        self.speed_label.setText(speed)

    def set_details(self, text: str):
        """Set details text"""
        self.details_label.setText(text)

    def set_paused(self, paused: bool):
        """Update pause button state"""
        self.pause_btn.setText("▶" if paused else "⏸")


class FileIcon(QLabel):
    """File icon with type-based coloring"""

    # File type to color mapping
    COLORS = {
        '.pdf': '#D13438',
        '.doc': '#185ABD',
        '.docx': '#185ABD',
        '.xls': '#107C10',
        '.xlsx': '#107C10',
        '.ppt': '#D24726',
        '.pptx': '#D24726',
        '.zip': '#FFC83D',
        '.rar': '#FFC83D',
        '.7z': '#FFC83D',
        '.png': '#0078D4',
        '.jpg': '#0078D4',
        '.jpeg': '#0078D4',
        '.gif': '#0078D4',
        '.mp4': '#8764B8',
        '.avi': '#8764B8',
        '.mkv': '#8764B8',
        '.mp3': '#EF6950',
        '.wav': '#EF6950',
        '.py': '#FFD43B',
        '.js': '#F7DF1E',
        '.ts': '#3178C6',
        '.html': '#E34C26',
        '.css': '#264DE4',
        '.java': '#5382A1',
        '.cpp': '#00599C',
        '.cs': '#68217A',
        '.exe': '#525252',
    }

    # File type to emoji mapping
    ICONS = {
        '.pdf': '📄',
        '.doc': '📘',
        '.docx': '📘',
        '.xls': '📊',
        '.xlsx': '📊',
        '.ppt': '📽',
        '.pptx': '📽',
        '.txt': '📝',
        '.zip': '📦',
        '.rar': '📦',
        '.7z': '📦',
        '.png': '🖼',
        '.jpg': '🖼',
        '.jpeg': '🖼',
        '.gif': '🖼',
        '.svg': '🎨',
        '.mp4': '🎬',
        '.avi': '🎬',
        '.mkv': '🎬',
        '.mp3': '🎵',
        '.wav': '🎵',
        '.py': '🐍',
        '.js': '📜',
        '.ts': '📜',
        '.html': '🌐',
        '.css': '🎨',
        '.json': '📋',
        '.xml': '📋',
        '.exe': '⚙',
        '.msi': '⚙',
    }

    def __init__(self, filename: str, size: int = 24, parent=None):
        super().__init__(parent)
        self.filename = filename
        self.icon_size = size

        ext = Path(filename).suffix.lower()

        # Get icon and color
        icon = self.ICONS.get(ext, '📄')
        color = self.COLORS.get(ext, '#605E5C')

        # Set up label
        self.setText(icon)
        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {color}22;
                border-radius: {size // 4}px;
                font-size: {int(size * 0.6)}pt;
            }}
        """)
        self.setToolTip(ext.upper() if ext else "FILE")


class SearchHistoryPopup(QWidget):
    """Search history popup widget"""
    item_clicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        self.setStyleSheet("""
            SearchHistoryPopup {
                background-color: white;
                border: 1px solid #E1DFDD;
                border-radius: 6px;
            }
        """)

        self.history_items = []

    def set_history(self, items: List[str]):
        """Set history items"""
        # Clear existing
        while self.layout().count():
            item = self.layout().takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.history_items = items

        # Add items
        for item in items[:10]:  # Limit to 10
            btn = QPushButton(item)
            btn.setFlat(True)
            btn.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding: 6px 12px;
                    border: none;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #F3F3F3;
                }
            """)
            btn.clicked.connect(lambda checked, text=item: self._on_item_clicked(text))
            self.layout().addWidget(btn)

        # Adjust size
        self.adjustSize()

    def _on_item_clicked(self, text: str):
        """Handle item click"""
        self.item_clicked.emit(text)
        self.hide()


class AnimatedButton(QPushButton):
    """Button with hover animation"""

    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self._animation = QPropertyAnimation(self, b"geometry")
        self._animation.setDuration(200)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    def enterEvent(self, event):
        """Animate on hover"""
        super().enterEvent(event)
        # Add subtle scale effect if needed

    def leaveEvent(self, event):
        """Animate on leave"""
        super().leaveEvent(event)


class EmptyStateWidget(QWidget):
    """Empty state placeholder"""

    def __init__(self, icon: str, title: str, message: str, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)

        # Icon
        icon_label = QLabel(icon)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("font-size: 48pt; color: #8A8886;")
        layout.addWidget(icon_label)

        # Title
        title_label = QLabel(title)
        title_label.setProperty("heading", True)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #605E5C;")
        layout.addWidget(title_label)

        # Message
        message_label = QLabel(message)
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setWordWrap(True)
        message_label.setStyleSheet("color: #8A8886;")
        layout.addWidget(message_label)


class LoadingSpinner(QWidget):
    """Animated loading spinner"""

    def __init__(self, size: int = 32, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.angle = 0

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._rotate)
        self.timer.setInterval(50)  # 20 FPS

    def start(self):
        """Start animation"""
        self.timer.start()
        self.show()

    def stop(self):
        """Stop animation"""
        self.timer.stop()
        self.hide()

    def _rotate(self):
        """Rotate spinner"""
        self.angle = (self.angle + 10) % 360
        self.update()

    def paintEvent(self, event):
        """Paint spinner"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw spinning arc
        painter.setPen(QPen(QColor("#0078D4"), 3))
        size = self.width()
        rect = self.rect().adjusted(2, 2, -2, -2)

        painter.drawArc(rect, self.angle * 16, 120 * 16)
