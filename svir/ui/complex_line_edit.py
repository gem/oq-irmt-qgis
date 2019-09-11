from PyQt5.QtGui import (
    QPainter, QColor, QFont, QPainterPath, QPen,
    QFontMetrics,
    QFontDatabase,
    )
from PyQt5.QtCore import Qt, QRectF, QEvent
from PyQt5.QtWidgets import QLineEdit


class ComplexLineEdit(QLineEdit):

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        self.settings = {
            'bg': QColor(224, 242, 241),
            'highlight': QColor(0, 150, 136),
            'text': QColor(0, 105, 92),
            'font': QFontDatabase.systemFont(QFontDatabase.GeneralFont),
            'padding-x': 8,
            'padding-y': 2,
            }
        self.font_metrics = QFontMetrics(self.settings['font'])

        self.close_rectangles = {}

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        self.draw_items(event, qp)
        qp.end()

    def mouseReleaseEvent(self, event):
        for text, rect in self.close_rectangles.items():
            if event.pos() in rect:
                selected = self.parent.get_selected_items()
                selected.remove(text)
                self.parent.set_selected_items(selected)

                event.accept()
                return
        self.parent.showPopup()

    def draw_items(self, event, qp):
        font = self.settings['font']
        qp.setRenderHint(QPainter.Antialiasing)
        qp.setFont(font)

        self.close_rectangles = {}
        if not self.current_text():
            font.setUnderline(True)
            qp.setFont(font)
            self.draw_text(qp,
                           event.rect(),
                           'Click to select items')
            font.setUnderline(True)
            return

        x = self.settings['padding-x']
        for text in self.current_text():
            text = text.strip()
            width = self.font_metrics.width(text)

            # add padding
            height = self.height() - self.settings['padding-y'] * 2
            width += 2 * self.settings['padding-x']
            # add space for x button
            width += height

            rect = QRectF(x,
                          self.settings['padding-y'],
                          width,
                          height
                          )
            self.draw_bg(qp, rect, text)
            self.draw_text(qp, rect, text)
            # add margin between elements
            x = x + width + self.settings['padding-x']

    def draw_bg(self, qp, rect, text):
        path = QPainterPath()

        # add container
        path.addRoundedRect(rect, 4, 4)
        qp.setPen(QPen(self.settings['highlight'], 2))
        qp.fillPath(path, self.settings['bg'])

        # add close button
        circle_size = rect.height() / 1.8
        pen_size = 2
        qp.setPen(QPen(self.settings['text'], pen_size, Qt.SolidLine))
        rect = QRectF(
            rect.right() - circle_size - self.settings['padding-x']/2,
            rect.top() + (rect.height() - circle_size)/2,
            circle_size,
            circle_size
            )
        path.addEllipse(rect)
        qp.drawPath(path)
        # draw cross
        inside_rect = QRectF(rect)
        inside_rect.adjust(pen_size, pen_size, -pen_size, -pen_size)
        qp.drawLine(inside_rect.topLeft(), inside_rect.bottomRight())
        qp.drawLine(inside_rect.bottomLeft(), inside_rect.topRight())

        self.close_rectangles[text] = rect

    def draw_text(self, qp, rect, text):
        qp.setPen(self.settings['text'])
        # start text one padding in
        left = rect.left() + self.settings['padding-x']
        rect.setLeft(left)
        qp.drawText(rect, Qt.AlignLeft, text)

    def current_text(self):
        items = self.text().split('; ')
        if len(items) == 1 and not items[0]:
            # avoid returning ['']
            return []
        else:
            return items
