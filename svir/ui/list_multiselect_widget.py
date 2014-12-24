"""
allows multiple selection between in a large list

Contact : marco@opengis.ch

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.
"""

__author__ = 'marco@opengis.ch'
__revision__ = '$Format:%H$'
__date__ = '9/07/2013'

from PyQt4 import QtGui, QtCore


class ListMultiSelectWidget(QtGui.QGroupBox):
    """Widget to show two parallel lists and move elements between the two

    usage from code:
        self.myWidget = ListMultiSelectWidget(title='myTitle')
        self.myLayout.insertWidget(1, self.myWidget)
    usage from designer:
        insert a QGroupBox in your UI file
        optionally give a title to the QGroupBox
        promote it to ListMultiSelectWidget
    """

    def __init__(self, parent=None, title=None):
        QtGui.QGroupBox.__init__(self)
        self.setTitle(title)

        self.selected_widget = None
        self.unselected_widget = None
        self._setupUI()

        #connect actions
        self.select_all_btn.clicked.connect(self._select_all)
        self.deselect_all_btn.clicked.connect(self._deselect_all)
        self.select_btn.clicked.connect(self._select)
        self.deselect_btn.clicked.connect(self._deselect)

    def get_selected_items(self):
        """
        :return list with all the selected items text
        """
        return self._get_items(self.selected_widget)

    def get_unselected_items(self):
        """
        :return list with all the unselected items text
        """
        return self._get_items(self.unselected_widget)

    def add_selected_items(self, items):
        """
        :param items list of strings to be added in the selected list
        """
        self._add_items(self.selected_widget, items)

    def add_unselected_items(self, items):
        """
        :param items list of strings to be added in the unselected list
        """
        self._add_items(self.unselected_widget, items)

    def set_selected_items(self, items):
        """
        :param items list of strings to be set as the selected list
        """
        self._set_items(self.selected_widget, items)

    def set_unselected_items(self, items):
        """
        :param items list of strings to be set as the unselected list
        """
        self._set_items(self.unselected_widget, items)

    def _get_items(self, widget):
        for i in range(widget.count()):
            yield widget.item(i).text()

    def _set_items(self, widget, items):
        widget.clear()
        self._add_items(widget, items)

    def _add_items(self, widget, items):
        widget.addItems(items)

    def _select_all(self):
        self.unselected_widget.selectAll()
        self._do_move(self.unselected_widget, self.selected_widget)

    def _deselect_all(self):
        self.selected_widget.selectAll()
        self._do_move(self.selected_widget, self.unselected_widget)

    def _select(self):
        self._do_move(self.unselected_widget, self.selected_widget)

    def _deselect(self):
        self._do_move(self.selected_widget, self.unselected_widget)

    def _do_move(self, fromList, toList):
        for item in fromList.selectedItems():
            toList.addItem(fromList.takeItem(fromList.row(item)))

    def _setupUI(self):
        self.setSizePolicy(
            QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Ignored)

        self.main_horizontal_layout = QtGui.QHBoxLayout(self)

        #unselected widget
        self.unselected_widget = QtGui.QListWidget(self)
        self._set_list_widget_defaults(self.unselected_widget)

        #selected widget
        self.selected_widget = QtGui.QListWidget(self)
        self._set_list_widget_defaults(self.selected_widget)

        #buttons
        self.buttons_vertical_layout = QtGui.QVBoxLayout()
        self.buttons_vertical_layout.setContentsMargins(0, -1, 0, -1)

        self.select_all_btn = SmallQPushButton('>>')
        self.deselect_all_btn = SmallQPushButton('<<')
        self.select_btn = SmallQPushButton('>')
        self.deselect_btn = SmallQPushButton('<')
        self.select_btn.setToolTip('Add the selected items')
        self.deselect_btn.setToolTip('Remove the selected items')
        self.select_all_btn.setToolTip('Add all')
        self.deselect_all_btn.setToolTip('Remove all')

        #add buttons
        self.buttons_vertical_layout.addWidget(self.select_btn)
        self.buttons_vertical_layout.addWidget(self.deselect_btn)
        self.buttons_vertical_layout.addWidget(self.select_all_btn)
        self.buttons_vertical_layout.addWidget(self.deselect_all_btn)

        #add sub widgets
        self.main_horizontal_layout.addWidget(self.unselected_widget)
        self.main_horizontal_layout.addLayout(self.buttons_vertical_layout)
        self.main_horizontal_layout.addWidget(self.selected_widget)

    def _set_list_widget_defaults(self, widget):
        widget.setAlternatingRowColors(True)
        widget.setSortingEnabled(True)
        widget.setDragEnabled(True)
        widget.setDragDropMode(QtGui.QAbstractItemView.DragDrop)
        widget.setDragDropOverwriteMode(False)
        widget.setDefaultDropAction(QtCore.Qt.MoveAction)
        widget.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)


class SmallQPushButton(QtGui.QPushButton):
    def __init__(self, text):
        QtGui.QPushButton.__init__(self)
        self.setText(text)
        buttons_size_policy = QtGui.QSizePolicy(
            QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        self.setSizePolicy(buttons_size_policy)
        self.setMaximumSize(QtCore.QSize(30, 30))
