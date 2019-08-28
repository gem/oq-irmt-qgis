from PyQt5.QtWidgets import (
    QLineEdit, QCheckBox, QComboBox, QListWidget, QListWidgetItem,
    QApplication, QMainWindow)
from PyQt5.QtCore import QEvent, pyqtSignal
from PyQt5.QtGui import QCursor


class MultiSelectComboBox(QComboBox):

    SEARCH_BAR_IDX = 0
    SELECT_ALL_IDX = 1
    selection_changed = pyqtSignal()
    item_was_clicked = pyqtSignal(str)

    def __init__(self, parent):

        super().__init__(parent)

        self.mlist = QListWidget(self)
        self.line_edit = QLineEdit(self)
        self.search_bar = QLineEdit(self)

        self.clear()

        self.line_edit.setReadOnly(True)
        self.line_edit.installEventFilter(self)

        self.setModel(self.mlist.model())
        self.setView(self.mlist)
        self.setLineEdit(self.line_edit)

        self.search_bar.textChanged[str].connect(self.onSearch)
        self.activated.connect(self.itemClicked)

    def on_select_all_toggled(self, state):
        for i in range(2, self.mlist.count()):
            checkbox = self.mlist.itemWidget(self.mlist.item(i))
            if self.search_bar.text().lower() in checkbox.text().lower():
                checkbox.setChecked(state)

    def hidePopup(self):
        width = self.width()
        height = self.mlist.height()
        x = (QCursor.pos().x()
             - self.mapToGlobal(self.geometry().topLeft()).x()
             + self.geometry().x())
        y = (QCursor.pos().y()
             - self.mapToGlobal(self.geometry().topLeft()).y()
             + self.geometry().y())
        if (x >= 0 and x <= width and y >= self.height()
                and y <= height + self.height()):
            # Item was clicked, do not hide popup
            pass
        else:
            super().hidePopup()

    def stateChanged(self, state):
        # NOTE: not using state
        selected_data = ""
        for i in range(2, self.mlist.count()):
            checkbox = self.mlist.itemWidget(self.mlist.item(i))
            if checkbox.isChecked():
                selected_data += checkbox.text() + "; "
        if selected_data.endswith("; "):
            selected_data = selected_data[:-2]
        if selected_data:
            self.line_edit.setText(selected_data)
        else:
            self.line_edit.clear()
        self.line_edit.setToolTip(selected_data)
        self.selection_changed.emit()

    def add_selected_items(self, items):
        self.addItems(items, selected=True)

    def add_unselected_items(self, items):
        self.addItems(items, selected=False)

    def set_selected_items(self, items):
        self.set_items_selection(items, True)

    def set_unselected_items(self, items):
        self.set_items_selection(items, False)

    def set_items_selection(self, items, checked):
        for i in range(2, self.mlist.count()):
            checkbox = self.mlist.itemWidget(self.mlist.item(i))
            if checkbox.text() in items:
                checkbox.setChecked(checked)
            else:
                checkbox.setChecked(not checked)

    def get_selected_items(self):
        items = []
        for i in range(2, self.mlist.count()):
            checkbox = self.mlist.itemWidget(self.mlist.item(i))
            if checkbox.isChecked():
                items.append(checkbox.text())
        return items

    def get_unselected_items(self):
        items = []
        for i in range(2, self.mlist.count()):
            checkbox = self.mlist.itemWidget(self.mlist.item(i))
            if not checkbox.isChecked():
                items.append(checkbox.text())
        return items

    def addItem(self, text, user_data=None, selected=False):
        # NOTE: not using user_data
        list_widget_item = QListWidgetItem(self.mlist)
        checkbox = QCheckBox(self)
        checkbox.setText(text)
        self.mlist.addItem(list_widget_item)
        self.mlist.setItemWidget(list_widget_item, checkbox)
        checkbox.stateChanged.connect(self.stateChanged)
        checkbox.setChecked(selected)

    def currentText(self):
        items = self.line_edit.text().split('; ')
        if len(items) == 1 and not items[0]:
            # avoid returning ['']
            return []
        else:
            return items

    def addItems(self, texts, selected=False):
        for text in texts:
            self.addItem(text, selected=selected)

    def count(self):
        # do not count search bar and toggle select all
        count = self.mlist.count() - 2
        if count < 0:
            count = 0
        return count

    def selected_count(self):
        return len(self.get_selected_items())

    def onSearch(self, search_str):
        for i in range(2, self.mlist.count()):
            checkbox = self.mlist.itemWidget(self.mlist.item(i))
            if search_str.lower() in checkbox.text().lower():
                self.mlist.item(i).setHidden(False)
            else:
                self.mlist.item(i).setHidden(True)

    def itemClicked(self, idx):
        if idx not in [self.SEARCH_BAR_IDX, self.SELECT_ALL_IDX]:
            checkbox = self.mlist.itemWidget(self.mlist.item(idx))
            checkbox.setChecked(not checkbox.isChecked())
            self.item_was_clicked.emit(checkbox.text())

    def set_search_bar_placeholder_text(self, text):
        self.search_bar.setPlaceholderText(text)

    def set_placeholder_text(self, text):
        self.line_edit.setPlaceholderText(text)

    def clear(self):
        self.mlist.clear()
        search_item = QListWidgetItem(self.mlist)
        self.search_bar.setPlaceholderText("Search...")
        self.search_bar.setClearButtonEnabled(True)
        self.mlist.addItem(search_item)
        self.mlist.setItemWidget(search_item, self.search_bar)
        toggle_select_item = QListWidgetItem(self.mlist)
        self.toggle_ckb = QCheckBox(self)
        self.toggle_ckb.setText('Select/unselect all')
        self.mlist.addItem(toggle_select_item)
        self.mlist.setItemWidget(toggle_select_item, self.toggle_ckb)
        self.toggle_ckb.stateChanged.connect(self.on_select_all_toggled)

    def wheelEvent(self, wheel_event):
        # do not handle the wheel event
        pass

    def eventFilter(self, obj, event):
        if obj == self.line_edit and event.type() == QEvent.MouseButtonRelease:
            self.showPopup()
            return False
        return False

    def keyPressedEvent(self, event):
        # do not handle key event
        pass

    # def setCurrentText(self, text):
    #     pass

    def setCurrentText(self, texts):
        for i in range(2, self.mlist.count()):
            checkbox = self.mlist.itemWidget(self.mlist.item(i))
            checkbox_str = checkbox.text()
            if checkbox_str in texts:
                checkbox.setChecked(True)

    def resetSelection(self):
        for i in range(2, self.mlist.count()):
            checkbox = self.mlist.itemWidget(self.mlist.item(i))
            checkbox.setChecked(False)


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)

    win = QMainWindow()
    mscb = MultiSelectComboBox(win)
    mscb.addItem("ITA")
    mscb.addItem("FRA")
    mscb.addItem("GER")
    mscb.addItems(["Rlz_%2d" % rlz for rlz in range(1, 100)])
    win.layout().addWidget(mscb)
    win.show()
    app.exec_()
