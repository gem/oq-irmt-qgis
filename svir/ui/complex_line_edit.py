from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtGui import (
    QPainter, QColor, QFont, QPainterPath, QPen,
    QFontMetrics,
    )
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtWidgets import QLineEdit


class ComplexLineEdit(QLineEdit):

    def __init__(self, parent):
        super().__init__(parent)
        self.settings = {
            'bg': QColor(224, 242, 241),
            'highlight': QColor(0, 150, 136),
            'text': QColor(0, 105, 92),
            'font': QFont('Decorative', 10),
            'padding': 4,
            }
        self.font_metrics = QFontMetrics(self.settings['font'])

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        self.draw_items(event, qp)
        qp.end()

    def draw_items(self, event, qp):
        print(self.text())
        qp.setFont(self.settings['font'])
        qp.setRenderHint(QPainter.Antialiasing)
        x = 0
        for text in self.text().split(';'):
            width = self.font_metrics.width(text)
            new_x = self.draw_bg(event, qp, text, x, width)
            self.draw_text(event, qp, text, x, width)
            x = new_x

    def draw_bg(self, event, qp, text, x, width):
        path = QPainterPath()
        x = x + self.settings['padding']
        rect = QRectF(x,
                      self.settings['padding'],
                      width,
                      self.height() - self.settings['padding'] * 2
                      )
        path.addRoundedRect(rect, 8, 8)
        qp.setPen(QPen(self.settings['highlight'], 2))
        qp.fillPath(path, self.settings['bg'])
        qp.drawPath(path)
        return x + width

    def draw_text(self, event, qp, text, x, width):
        qp.setPen(self.settings['text'])
        rect = QRectF(x,
                      self.settings['padding'],
                      width,
                      self.height() - self.settings['padding'] * 2
                      )
        qp.drawText(rect, Qt.AlignCenter, text)

