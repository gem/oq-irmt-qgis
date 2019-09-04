from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QLineEdit, QCheckBox, QComboBox, QListWidget, QListWidgetItem,
    QApplication, QMainWindow, QWidget, QVBoxLayout)
from PyQt5.QtCore import QEvent, pyqtSignal
from PyQt5.QtGui import QCursor


class MultiSelectComboBox(QComboBox):

    SEARCH_BAR_IDX = 0
    SELECT_ALL_IDX = 1
    selection_changed = pyqtSignal()
    item_was_clicked = pyqtSignal(str, bool)

    def __init__(self, parent, mono=False):

        super().__init__(parent)
        self.mono = mono
        if self.mono:
            return

        self.mlist = QListWidget(self)
        self.line_edit = QLineEdit(self)

        self.clear()

        self.line_edit.setReadOnly(True)
        self.line_edit.installEventFilter(self)

        self.setModel(self.mlist.model())
        self.setView(self.mlist)
        self.view().setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setLineEdit(self.line_edit)

        self.set_placeholder_text('Click to select items')

        # NOTE: this is necessary to handle the case in which an item in the
        # list is clicked to its right part, outside the text
        self.activated.connect(self.itemClicked)

    def on_select_all_toggled(self, state):
        self.blockSignals(True)
        for i in range(2, self.mlist.count()):
            checkbox = self.mlist.itemWidget(self.mlist.item(i))
            if self.search_bar.text().lower() in checkbox.text().lower():
                checkbox.setChecked(state)
        self.blockSignals(False)
        self.selection_changed.emit()

    def itemClicked(self, idx):
        if self.mono:
            self.item_was_clicked.emit(self.currentText(), True)
            return super().itemClicked(idx)
        if idx not in [self.SEARCH_BAR_IDX, self.SELECT_ALL_IDX]:
            checkbox = self.mlist.itemWidget(self.mlist.item(idx))
            checkbox.setChecked(not checkbox.isChecked())
            self.item_was_clicked.emit(checkbox.text(), checkbox.isChecked())

    def hidePopup(self):
        if self.mono:
            return super().hidePopup()
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
        if self.mono:
            return super().stateChanged(state)
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

    def on_checkbox_stateChanged(self, text, state):
        self.item_was_clicked.emit(text, state)

    def add_selected_items(self, items):
        if self.mono:
            return super().addItems(items)
        self.addItems(items, selected=True)

    def add_unselected_items(self, items):
        if self.mono:
            return super().addItems(items)
        self.addItems(items, selected=False)

    def set_selected_items(self, items):
        if self.mono:
            return
        self.set_items_selection(items, True)

    def set_unselected_items(self, items):
        if self.mono:
            return
        self.set_items_selection(items, False)

    def set_items_selection(self, items, checked):
        if self.mono:
            return
        for i in range(2, self.mlist.count()):
            checkbox = self.mlist.itemWidget(self.mlist.item(i))
            if checkbox.text() in items:
                checkbox.setChecked(checked)
            else:
                checkbox.setChecked(not checked)

    def get_selected_items(self):
        items = []
        if self.mono:
            if super().currentText():
                return [super().currentText()]
            else:
                return []
        for i in range(2, self.mlist.count()):
            checkbox = self.mlist.itemWidget(self.mlist.item(i))
            if checkbox.isChecked():
                items.append(checkbox.text())
        return items

    def get_unselected_items(self):
        items = []
        if self.mono:
            selected_text = self.currentText()
            for i in range(self.count()):
                item_text = self.itemText(i)
                if item_text and item_text != selected_text:
                    items.append(item_text)
            return items
        for i in range(2, self.mlist.count()):
            checkbox = self.mlist.itemWidget(self.mlist.item(i))
            if not checkbox.isChecked():
                items.append(checkbox.text())
        return items

    def addItem(self, text, user_data=None, selected=False):
        if self.mono:
            return super().addItem(text, user_data)
        # NOTE: not using user_data
        list_widget_item = QListWidgetItem(self.mlist)
        checkbox = QCheckBox(self)
        checkbox.setText(text)
        self.mlist.addItem(list_widget_item)
        self.mlist.setItemWidget(list_widget_item, checkbox)
        checkbox.stateChanged.connect(self.stateChanged)
        checkbox.stateChanged.connect(
            lambda state: self.on_checkbox_stateChanged(
                checkbox.text(), state))
        checkbox.setChecked(selected)

    def currentText(self):
        if self.mono:
            return super().currentText()
        items = self.line_edit.text().split('; ')
        if len(items) == 1 and not items[0]:
            # avoid returning ['']
            return []
        else:
            return items

    def addItems(self, texts, selected=False):
        if self.mono:
            return super().addItems(texts)
        for text in texts:
            self.addItem(text, selected=selected)

    def count(self):
        if self.mono:
            return super().count()
        # do not count search bar and toggle select all
        count = self.mlist.count() - 2
        if count < 0:
            count = 0
        return count

    def selected_count(self):
        if self.mono:
            if self.currentIndex() == -1:
                return 0
            else:
                return 1
        return len(self.get_selected_items())

    def onSearch(self, search_str):
        self.setMaxVisibleItems(min(10, self.mlist.count()))
        for i in range(2, self.mlist.count()):
            checkbox = self.mlist.itemWidget(self.mlist.item(i))
            if search_str.lower() in checkbox.text().lower():
                self.mlist.item(i).setHidden(False)
            else:
                self.mlist.item(i).setHidden(True)
        # NOTE: hack to fix problem when you first filter and have few items,
        # then filter again and have more items
        self.hidePopup()
        self.showPopup()
        # NOTE: hide/show would lose focus from the search bar
        self.search_bar.setFocus()

    def set_search_bar_placeholder_text(self, text):
        self.search_bar.setPlaceholderText(text)

    def set_placeholder_text(self, text):
        self.line_edit.setPlaceholderText(text)

    def clear(self):
        if self.mono:
            return super().clear()
        self.mlist.clear()
        self.search_bar = QLineEdit(self)
        self.search_item = QListWidgetItem(self.mlist)
        self.search_bar.setPlaceholderText("Search...")
        self.search_bar.setClearButtonEnabled(True)
        self.mlist.addItem(self.search_item)
        self.mlist.setItemWidget(self.search_item, self.search_bar)
        self.toggle_select_item = QListWidgetItem(self.mlist)
        self.toggle_ckb = QCheckBox(self)
        self.toggle_ckb.setText('Select/unselect all')
        self.mlist.addItem(self.toggle_select_item)
        self.mlist.setItemWidget(self.toggle_select_item, self.toggle_ckb)
        self.toggle_ckb.stateChanged.connect(self.on_select_all_toggled)
        self.search_bar.textChanged[str].connect(self.onSearch)

    def wheelEvent(self, wheel_event):
        if self.mono:
            return super().wheelEvent(wheel_event)
        # do not handle the wheel event
        pass

    def eventFilter(self, obj, event):
        if self.mono:
            return super().eventFilter(obj, event)
        if obj == self.line_edit and event.type() == QEvent.MouseButtonRelease:
            self.showPopup()
            return False
        return False

    def keyPressedEvent(self, event):
        if self.mono:
            return super().keyPressedEvent(event)
        # do not handle key event
        pass

    # def setCurrentText(self, text):
    #     pass

    def setCurrentText(self, texts):
        if self.mono:
            return super().setCurrentText(texts)
        for i in range(2, self.mlist.count()):
            checkbox = self.mlist.itemWidget(self.mlist.item(i))
            checkbox_str = checkbox.text()
            if checkbox_str in texts:
                checkbox.setChecked(True)

    def resetSelection(self):
        if self.mono:
            return self.resetSelection()
        for i in range(2, self.mlist.count()):
            checkbox = self.mlist.itemWidget(self.mlist.item(i))
            checkbox.setChecked(False)


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)

    win = QMainWindow()
    wdg = QWidget()
    wdg.setLayout(QVBoxLayout())
    win.setCentralWidget(wdg)
    mscb = MultiSelectComboBox(wdg)
    mscb.addItem("ITA")
    mscb.addItem("FRA")
    mscb.addItem("GER")
    mscb.addItems(["Rlz_%2d" % rlz for rlz in range(1, 100)])
    mscbmono = MultiSelectComboBox(wdg, mono=True)
    mscbmono.addItems(mscb.get_unselected_items())
    wdg.layout().addWidget(mscb)
    wdg.layout().addWidget(mscbmono)
    win.show()
    app.exec_()
