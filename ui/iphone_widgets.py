"""
iOS-style Custom Widgets - Rounded cards, blur effects, smooth animations
"""

from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QScrollArea, QFrame, QGraphicsBlurEffect, QGraphicsOpacityEffect
)
from PyQt6.QtCore import (
    Qt, pyqtSignal, QPropertyAnimation, QEasingCurve,
    QPoint, QRect, QTimer, QSize, QEvent, pyqtProperty
)
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush, QLinearGradient,
    QPainterPath, QFont, QPixmap, QPalette
)


class RoundedCardWidget(QFrame):
    """iOS-style rounded card with shadow and hover effects"""

    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self._hover = False
        self._pressed = False
        self._corner_radius = 16

        # Animation properties
        self._shadow_opacity = 0.1
        self._scale = 1.0

        # Setup animations
        self._shadow_anim = QPropertyAnimation(self, b"shadowOpacity")
        self._shadow_anim.setDuration(200)
        self._shadow_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

    def setShadowOpacity(self, opacity: float):
        """Set shadow opacity (animated property)"""
        self._shadow_opacity = opacity
        self.update()

    def getShadowOpacity(self) -> float:
        """Get shadow opacity"""
        return self._shadow_opacity

    shadowOpacity = pyqtProperty(float, getShadowOpacity, setShadowOpacity)

    def enterEvent(self, event: QEvent):
        """Handle mouse enter"""
        super().enterEvent(event)
        self._hover = True
        self._shadow_anim.setStartValue(self._shadow_opacity)
        self._shadow_anim.setEndValue(0.2)
        self._shadow_anim.start()
        self.update()

    def leaveEvent(self, event: QEvent):
        """Handle mouse leave"""
        super().leaveEvent(event)
        self._hover = False
        self._shadow_anim.setStartValue(self._shadow_opacity)
        self._shadow_anim.setEndValue(0.1)
        self._shadow_anim.start()
        self.update()

    def mousePressEvent(self, event):
        """Handle mouse press"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._pressed = True
            self.update()

    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._pressed = False
            if self.rect().contains(event.pos()):
                self.clicked.emit()
            self.update()

    def paintEvent(self, event):
        """Custom paint with rounded corners and shadow"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw shadow
        shadow_color = QColor(0, 0, 0, int(255 * self._shadow_opacity))
        shadow_offset = 2 if not self._pressed else 1

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(shadow_color))

        shadow_rect = self.rect().adjusted(
            shadow_offset, shadow_offset,
            shadow_offset, shadow_offset
        )
        painter.drawRoundedRect(shadow_rect, self._corner_radius, self._corner_radius)

        # Draw card background
        card_rect = self.rect().adjusted(0, 0, 0, -shadow_offset * 2)

        # Get background color from palette
        bg_color = self.palette().color(QPalette.ColorRole.Base)
        if self._pressed:
            bg_color = bg_color.darker(105)

        painter.setBrush(QBrush(bg_color))
        painter.drawRoundedRect(card_rect, self._corner_radius, self._corner_radius)

        # Draw border if hover
        if self._hover:
            border_color = self.palette().color(QPalette.ColorRole.Highlight)
            border_color.setAlpha(100)
            painter.setPen(QPen(border_color, 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(
                card_rect.adjusted(1, 1, -1, -1),
                self._corner_radius - 1,
                self._corner_radius - 1
            )


class CategoryIconWidget(QLabel):
    """iOS-style category icon with background"""

    # Category color schemes
    CATEGORY_COLORS = {
        'Imágenes': QColor(0, 122, 255),      # iOS Blue
        'Videos': QColor(255, 149, 0),        # iOS Orange
        'Audio': QColor(255, 59, 48),         # iOS Red
        'Documentos': QColor(0, 199, 190),    # iOS Teal
        'Código': QColor(175, 82, 222),       # iOS Purple
        'Comprimidos': QColor(255, 204, 0),   # iOS Yellow
        'Ejecutables': QColor(88, 86, 214),   # iOS Indigo
        'Datos': QColor(90, 200, 250),        # iOS Light Blue
        'Otros': QColor(142, 142, 147),       # iOS Gray
    }

    # Category icons (emoji or unicode)
    CATEGORY_ICONS = {
        'Imágenes': '🖼',
        'Videos': '🎬',
        'Audio': '🎵',
        'Documentos': '📄',
        'Código': '💻',
        'Comprimidos': '📦',
        'Ejecutables': '⚙',
        'Datos': '💾',
        'Otros': '📁',
    }

    def __init__(self, category: str, size: int = 64, parent=None):
        super().__init__(parent)
        self.category = category
        self.icon_size = size

        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Get icon and color
        icon = self.CATEGORY_ICONS.get(category, '📁')
        self.setText(icon)

        # Set font size
        font = self.font()
        font.setPointSize(int(size * 0.4))
        self.setFont(font)

    def paintEvent(self, event):
        """Custom paint with rounded background"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Get category color
        color = self.CATEGORY_COLORS.get(self.category, QColor(142, 142, 147))

        # Draw gradient background
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, color.lighter(110))
        gradient.setColorAt(1, color)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(gradient))
        painter.drawRoundedRect(self.rect(), self.icon_size // 4, self.icon_size // 4)

        # Draw icon (emoji)
        super().paintEvent(event)


class iOSToggleSwitch(QWidget):
    """iOS-style toggle switch"""

    toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._checked = False
        self._handle_position = 0

        self.setFixedSize(50, 30)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Animation
        self._animation = QPropertyAnimation(self, b"handlePosition")
        self._animation.setDuration(200)
        self._animation.setEasingCurve(QEasingCurve.Type.InOutCubic)

    def setHandlePosition(self, pos: int):
        """Set handle position (animated property)"""
        self._handle_position = pos
        self.update()

    def getHandlePosition(self) -> int:
        """Get handle position"""
        return self._handle_position

    handlePosition = pyqtProperty(int, getHandlePosition, setHandlePosition)

    def isChecked(self) -> bool:
        """Get checked state"""
        return self._checked

    def setChecked(self, checked: bool):
        """Set checked state"""
        if self._checked != checked:
            self._checked = checked

            # Animate handle
            start_pos = 0 if not checked else 20
            end_pos = 20 if checked else 0

            self._animation.setStartValue(start_pos)
            self._animation.setEndValue(end_pos)
            self._animation.start()

            self.toggled.emit(checked)

    def mousePressEvent(self, event):
        """Toggle on click"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.setChecked(not self._checked)

    def paintEvent(self, event):
        """Custom paint"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw track
        track_color = QColor(52, 199, 89) if self._checked else QColor(142, 142, 147)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(track_color))
        painter.drawRoundedRect(self.rect(), 15, 15)

        # Draw handle
        handle_rect = QRect(
            self._handle_position + 2,
            2,
            26,
            26
        )
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.drawEllipse(handle_rect)


class BlurBackgroundWidget(QWidget):
    """Widget with blur background effect"""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Setup blur effect
        self._blur = QGraphicsBlurEffect()
        self._blur.setBlurRadius(20)

        self._opacity = QGraphicsOpacityEffect()
        self._opacity.setOpacity(0.95)

        self.setGraphicsEffect(self._opacity)

    def paintEvent(self, event):
        """Custom paint with translucent background"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Semi-transparent background
        bg_color = self.palette().color(QPalette.ColorRole.Base)
        bg_color.setAlpha(240)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(bg_color))
        painter.drawRoundedRect(self.rect(), 12, 12)


class SmoothScrollArea(QScrollArea):
    """Scroll area with smooth scrolling"""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Enable kinetic scrolling
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setWidgetResizable(True)

        # Smooth scrolling properties
        self._target_scroll = 0
        self._current_scroll = 0

        self._scroll_timer = QTimer(self)
        self._scroll_timer.timeout.connect(self._smooth_scroll_step)
        self._scroll_timer.setInterval(16)  # ~60 FPS

    def wheelEvent(self, event):
        """Handle wheel with smooth scrolling"""
        delta = event.angleDelta().y()
        self._target_scroll = self.verticalScrollBar().value() - delta

        # Clamp to valid range
        self._target_scroll = max(
            self.verticalScrollBar().minimum(),
            min(self._target_scroll, self.verticalScrollBar().maximum())
        )

        if not self._scroll_timer.isActive():
            self._current_scroll = self.verticalScrollBar().value()
            self._scroll_timer.start()

        event.accept()

    def _smooth_scroll_step(self):
        """Animate scroll step"""
        diff = self._target_scroll - self._current_scroll

        if abs(diff) < 1:
            self._current_scroll = self._target_scroll
            self._scroll_timer.stop()
        else:
            self._current_scroll += diff * 0.3

        self.verticalScrollBar().setValue(int(self._current_scroll))


class PullToRefreshWidget(QWidget):
    """Pull-to-refresh gesture widget"""

    refreshRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._pull_distance = 0
        self._is_refreshing = False
        self._threshold = 60

        self.setFixedHeight(80)
        self.hide()

        # Spinner animation
        self._rotation = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate_spinner)
        self._timer.setInterval(50)

    def startRefresh(self):
        """Start refresh animation"""
        self._is_refreshing = True
        self._timer.start()
        self.show()

    def stopRefresh(self):
        """Stop refresh animation"""
        self._is_refreshing = False
        self._timer.stop()
        self.hide()

    def updatePullDistance(self, distance: int):
        """Update pull distance"""
        self._pull_distance = min(distance, self._threshold * 1.5)
        self.update()

    def _animate_spinner(self):
        """Animate spinner rotation"""
        self._rotation = (self._rotation + 10) % 360
        self.update()

    def paintEvent(self, event):
        """Draw pull indicator"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        center = QPoint(self.width() // 2, self.height() // 2)

        if self._is_refreshing:
            # Draw spinning indicator
            painter.setPen(QPen(self.palette().color(QPalette.ColorRole.Highlight), 3))
            painter.drawArc(
                center.x() - 15, center.y() - 15, 30, 30,
                self._rotation * 16, 120 * 16
            )
        else:
            # Draw pull progress
            progress = min(self._pull_distance / self._threshold, 1.0)
            painter.setPen(QPen(self.palette().color(QPalette.ColorRole.Highlight), 3))
            painter.drawArc(
                center.x() - 15, center.y() - 15, 30, 30,
                90 * 16, int(360 * progress * 16)
            )


class CategoryCardWidget(RoundedCardWidget):
    """iOS-style category card with icon, title, and stats"""

    def __init__(self, category: str, count: int = 0, size: str = "0 B", parent=None):
        super().__init__(parent)

        self.category = category
        self.file_count = count
        self.total_size = size

        self.setMinimumSize(160, 140)
        self.setMaximumSize(200, 160)

        self._setup_ui()

    def _setup_ui(self):
        """Setup card UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Icon
        self.icon_widget = CategoryIconWidget(self.category, size=56)
        layout.addWidget(self.icon_widget, alignment=Qt.AlignmentFlag.AlignCenter)

        # Category name
        self.name_label = QLabel(self.category)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = self.name_label.font()
        font.setPointSize(11)
        font.setBold(True)
        self.name_label.setFont(font)
        layout.addWidget(self.name_label)

        # File count
        self.count_label = QLabel(f"{self.file_count} files")
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.count_label.setStyleSheet("color: #8E8E93;")
        layout.addWidget(self.count_label)

        # Total size
        self.size_label = QLabel(self.total_size)
        self.size_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.size_label.setStyleSheet("color: #8E8E93; font-size: 9pt;")
        layout.addWidget(self.size_label)

    def updateData(self, count: int, size: str):
        """Update card data"""
        self.file_count = count
        self.total_size = size
        self.count_label.setText(f"{count} files")
        self.size_label.setText(size)


if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication, QMainWindow, QGridLayout
    import sys

    app = QApplication(sys.argv)

    # Test window
    window = QMainWindow()
    window.setWindowTitle("iOS Widgets Test")
    window.resize(800, 600)

    central = QWidget()
    window.setCentralWidget(central)

    grid = QGridLayout(central)
    grid.setSpacing(16)
    grid.setContentsMargins(20, 20, 20, 20)

    # Test category cards
    categories = ['Imágenes', 'Videos', 'Audio', 'Documentos',
                  'Código', 'Comprimidos', 'Ejecutables', 'Datos']

    for i, category in enumerate(categories):
        card = CategoryCardWidget(category, count=100 + i * 50, size=f"{i + 1} GB")
        card.clicked.connect(lambda c=category: print(f"Clicked: {c}"))
        grid.addWidget(card, i // 4, i % 4)

    window.show()
    sys.exit(app.exec())
