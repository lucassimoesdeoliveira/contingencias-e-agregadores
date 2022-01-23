from PyQt5.QtCore import (
    Qt, QSize, QPoint, QPointF, QRectF, pyqtSignal
    )

from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import QColor, QBrush, QPaintEvent, QPen, QPainter


class RangeSlider(QWidget):

    valueChanged = pyqtSignal(tuple)

    _transparent_pen = QPen(Qt.transparent)
    _light_grey_pen = QPen(Qt.lightGray)

    def __init__(self, parent, minimum=0, maximum=100):
        super().__init__(parent)

        self.minimum = minimum
        self.maximum = maximum

        self._range = self.maximum - self.minimum

        self._handle_min = minimum
        self._handle_max = maximum

        self._bar_brush = QBrush(Qt.lightGray)
        self._highlight_brush = QBrush(QColor("#00B0FF"))
        self._handle_brush = QBrush(Qt.white)

        # Setup the rest of the widget.
        self.setContentsMargins(8, 0, 8, 0)

    def sizeHint(self):
        return QSize(150, 45)

    def mousePressEvent(self, e):
        """
        Handle a click and move the appropriate slider, left or right.
        """

        # Transform click position to a range value. Calculate whether
        # that position is < > each slider and the < > of their midpoint
        # and move them appropriately.

        x = e.x()

        width = self.contentsRect().width()
        minh = self._minimum_handle()
        maxh = self._maximum_handle()

        midpoint = (minh + maxh) / 2

        if x < midpoint:
            # Minimum handle control.
            self._handle_min += (x - minh) / width * self._range

        if x > midpoint:
            # Maximum handle control.
            self._handle_max -= (maxh - x) / width * self._range

        self._constrain()
        self.update()
        self.valueChanged.emit(self.value())

    def mouseMoveEvent(self, e):
        """
        If the mouse is in the slider nobble, drag it.
        """
        x = e.x()
        radius = round(0.24 * self.contentsRect().height())

        width = self.contentsRect().width()
        minh = self._minimum_handle()
        maxh = self._maximum_handle()

        midpoint = (minh + maxh) / 2

        if x > minh-radius and x < minh+radius:
            # In the left toggle.
            self._handle_min += (x - minh) / width * self._range

        if x > maxh-radius and x < maxh+radius:
            # In the right toggle.
            self._handle_max -= (maxh - x) / width * self._range

        self._constrain()
        self.update()
        self.valueChanged.emit(self.value())

    def _constrain(self):

        self._handle_min = max(self._handle_min, self.minimum)
        self._handle_min = min(self._handle_max, self._handle_min, self.maximum)

        self._handle_max = min(self._handle_max, self.maximum)
        self._handle_max = max(self._handle_max, self._handle_min, self.minimum)

    def _minimum_handle(self):
        contRect = self.contentsRect()
        handleRadius = round(0.24 * contRect.height())
        trailLength = contRect.width() - 2 * handleRadius
        return contRect.x() + handleRadius + trailLength * (self._handle_min / self._range)

    def _maximum_handle(self):
        contRect = self.contentsRect()
        handleRadius = round(0.24 * contRect.height())
        trailLength = contRect.width() - 2 * handleRadius
        return contRect.x() + handleRadius + trailLength * (self._handle_max / self._range)

    def paintEvent(self, e: QPaintEvent):

        contRect = self.contentsRect()
        handleRadius = round(0.24 * contRect.height())

        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        barRect = QRectF(
            0, 0,
            contRect.width() - handleRadius, 0.40 * contRect.height()
        )
        barRect.moveCenter(contRect.center())
        rounding = barRect.height() / 2

        # the handle will move along this line
        trailLength = contRect.width() - 2 * handleRadius

        # draw the between-nobble bits in highlight color

        p.setPen(self._transparent_pen)
        p.setBrush(self._bar_brush)
        p.drawRoundedRect(barRect, rounding, rounding)

        leftx = self._minimum_handle()
        rightx = self._maximum_handle()

        hiRect = QRectF(
            leftx, barRect.y(),
            rightx-leftx, 0.40 * contRect.height()
        )

        p.setBrush(self._highlight_brush)
        p.drawRect(hiRect)

        p.setPen(self._light_grey_pen)
        p.setBrush(self._handle_brush)
        p.drawEllipse(
            QPointF(leftx, barRect.center().y()),
            handleRadius, handleRadius)
        p.drawEllipse(
            QPointF(rightx, barRect.center().y()),
            handleRadius, handleRadius)

        p.end()

    def value(self):
        return (self._handle_min, self._handle_max)


app = QApplication([])
slider = RangeSlider(None, 0, 100)

# Print out the value as it changes.
slider.valueChanged.connect(print)

slider.show()
app.exec_()