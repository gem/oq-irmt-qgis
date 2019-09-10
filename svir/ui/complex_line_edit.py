from PyQt5.QtGui import (
    QPainter, QColor, QFont, QPainterPath, QPen,
    QFontMetrics,
    QFontDatabase,
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
            'font': QFontDatabase.systemFont(QFontDatabase.GeneralFont),
            'padding-x': 8,
            'padding-y': 2,
            }
        self.font_metrics = QFontMetrics(self.settings['font'])

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        self.draw_items(event, qp)
        qp.end()

    def draw_items(self, event, qp):
        qp.setFont(self.settings['font'])
        qp.setRenderHint(QPainter.Antialiasing)
        x = self.settings['padding-x']
        for text in self.text().split(';'):
            text = text.strip()
            width = self.font_metrics.width(text)
            # add padding
            width += 2 * self.settings['padding-x']
            height = self.font_metrics.height()

            rect = QRectF(x,
                          self.settings['padding-y'],
                          width,
                          self.height() - self.settings['padding-y'] * 2
                          )
            if not text:
                self.draw_text(qp,
                               event.rect(),
                               'Click to select items')
                return
            self.draw_bg(qp, rect)
            self.draw_text(qp, rect, text)
            # add margin between elements
            x = x + width + self.settings['padding-x']

    def draw_bg(self, qp, rect):
        path = QPainterPath()
        path.addRoundedRect(rect, 4, 4)
        qp.setPen(QPen(self.settings['highlight'], 2))
        qp.fillPath(path, self.settings['bg'])
        qp.drawPath(path)

    def draw_text(self, qp, rect, text):
        qp.setPen(self.settings['text'])
        # start text one padding in
        left = rect.left() + self.settings['padding-x']
        rect.setLeft(left)
        qp.drawText(rect, Qt.AlignLeft, text)
