# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'hmtkwindow.ui'
#
# Created: Tue Oct 15 12:44:17 2013
#      by: PyQt4 UI code generator 4.10.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_HMTKWindow(object):
    def setupUi(self, HMTKWindow):
        HMTKWindow.setObjectName(_fromUtf8("HMTKWindow"))
        HMTKWindow.resize(1214, 756)
        self.centralWidget = QtGui.QWidget(HMTKWindow)
        self.centralWidget.setObjectName(_fromUtf8("centralWidget"))
        self.horizontalLayout = QtGui.QHBoxLayout(self.centralWidget)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.stackedFormWidget = QtGui.QTabWidget(self.centralWidget)
        self.stackedFormWidget.setMaximumSize(QtCore.QSize(500, 16777215))
        self.stackedFormWidget.setTabPosition(QtGui.QTabWidget.North)
        self.stackedFormWidget.setTabShape(QtGui.QTabWidget.Rounded)
        self.stackedFormWidget.setElideMode(QtCore.Qt.ElideNone)
        self.stackedFormWidget.setUsesScrollButtons(True)
        self.stackedFormWidget.setObjectName(_fromUtf8("stackedFormWidget"))
        self.stackedFormWidgetPage1 = QtGui.QWidget()
        self.stackedFormWidgetPage1.setObjectName(_fromUtf8("stackedFormWidgetPage1"))
        self.declusteringFormLayout = QtGui.QVBoxLayout(self.stackedFormWidgetPage1)
        self.declusteringFormLayout.setObjectName(_fromUtf8("declusteringFormLayout"))
        self.declusteringButtons = QtGui.QHBoxLayout()
        self.declusteringButtons.setObjectName(_fromUtf8("declusteringButtons"))
        self.declusterButton = QtGui.QPushButton(self.stackedFormWidgetPage1)
        self.declusterButton.setObjectName(_fromUtf8("declusterButton"))
        self.declusteringButtons.addWidget(self.declusterButton)
        self.declusteringPurgeButton = QtGui.QPushButton(self.stackedFormWidgetPage1)
        self.declusteringPurgeButton.setObjectName(_fromUtf8("declusteringPurgeButton"))
        self.declusteringButtons.addWidget(self.declusteringPurgeButton)
        self.declusteringFormLayout.addLayout(self.declusteringButtons)
        self.declusteringChart = FigureCanvasQTAggWidget(self.stackedFormWidgetPage1)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.declusteringChart.sizePolicy().hasHeightForWidth())
        self.declusteringChart.setSizePolicy(sizePolicy)
        self.declusteringChart.setMinimumSize(QtCore.QSize(0, 300))
        self.declusteringChart.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.declusteringChart.setObjectName(_fromUtf8("declusteringChart"))
        self.declusteringFormLayout.addWidget(self.declusteringChart)
        self.stackedFormWidget.addTab(self.stackedFormWidgetPage1, _fromUtf8(""))
        self.stackedFormWidgetPage2 = QtGui.QWidget()
        self.stackedFormWidgetPage2.setObjectName(_fromUtf8("stackedFormWidgetPage2"))
        self.completenessFormLayout = QtGui.QVBoxLayout(self.stackedFormWidgetPage2)
        self.completenessFormLayout.setObjectName(_fromUtf8("completenessFormLayout"))
        self.completenessButtons = QtGui.QHBoxLayout()
        self.completenessButtons.setObjectName(_fromUtf8("completenessButtons"))
        self.completenessButton = QtGui.QPushButton(self.stackedFormWidgetPage2)
        self.completenessButton.setObjectName(_fromUtf8("completenessButton"))
        self.completenessButtons.addWidget(self.completenessButton)
        self.completenessPurgeButton = QtGui.QPushButton(self.stackedFormWidgetPage2)
        self.completenessPurgeButton.setObjectName(_fromUtf8("completenessPurgeButton"))
        self.completenessButtons.addWidget(self.completenessPurgeButton)
        self.completenessFormLayout.addLayout(self.completenessButtons)
        self.completenessChart = FigureCanvasQTAggWidget(self.stackedFormWidgetPage2)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.completenessChart.sizePolicy().hasHeightForWidth())
        self.completenessChart.setSizePolicy(sizePolicy)
        self.completenessChart.setMinimumSize(QtCore.QSize(0, 300))
        self.completenessChart.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.completenessChart.setObjectName(_fromUtf8("completenessChart"))
        self.completenessFormLayout.addWidget(self.completenessChart)
        self.stackedFormWidget.addTab(self.stackedFormWidgetPage2, _fromUtf8(""))
        self.stackedFormWidgetPage3 = QtGui.QWidget()
        self.stackedFormWidgetPage3.setObjectName(_fromUtf8("stackedFormWidgetPage3"))
        self.recurrenceModelFormLayout = QtGui.QVBoxLayout(self.stackedFormWidgetPage3)
        self.recurrenceModelFormLayout.setObjectName(_fromUtf8("recurrenceModelFormLayout"))
        self.recurrenceModelChart = FigureCanvasQTAggWidget(self.stackedFormWidgetPage3)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.recurrenceModelChart.sizePolicy().hasHeightForWidth())
        self.recurrenceModelChart.setSizePolicy(sizePolicy)
        self.recurrenceModelChart.setMinimumSize(QtCore.QSize(0, 300))
        self.recurrenceModelChart.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.recurrenceModelChart.setObjectName(_fromUtf8("recurrenceModelChart"))
        self.recurrenceModelFormLayout.addWidget(self.recurrenceModelChart)
        self.recurrenceModelButton = QtGui.QPushButton(self.stackedFormWidgetPage3)
        self.recurrenceModelButton.setObjectName(_fromUtf8("recurrenceModelButton"))
        self.recurrenceModelFormLayout.addWidget(self.recurrenceModelButton)
        self.stackedFormWidget.addTab(self.stackedFormWidgetPage3, _fromUtf8(""))
        self.stackedFormWidgetPage4 = QtGui.QWidget()
        self.stackedFormWidgetPage4.setObjectName(_fromUtf8("stackedFormWidgetPage4"))
        self.maxMagnitudeFormLayout = QtGui.QVBoxLayout(self.stackedFormWidgetPage4)
        self.maxMagnitudeFormLayout.setObjectName(_fromUtf8("maxMagnitudeFormLayout"))
        self.maxMagnitudeChart = FigureCanvasQTAggWidget(self.stackedFormWidgetPage4)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.maxMagnitudeChart.sizePolicy().hasHeightForWidth())
        self.maxMagnitudeChart.setSizePolicy(sizePolicy)
        self.maxMagnitudeChart.setMinimumSize(QtCore.QSize(0, 300))
        self.maxMagnitudeChart.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.maxMagnitudeChart.setObjectName(_fromUtf8("maxMagnitudeChart"))
        self.maxMagnitudeFormLayout.addWidget(self.maxMagnitudeChart)
        self.maxMagnitudeButton = QtGui.QPushButton(self.stackedFormWidgetPage4)
        self.maxMagnitudeButton.setObjectName(_fromUtf8("maxMagnitudeButton"))
        self.maxMagnitudeFormLayout.addWidget(self.maxMagnitudeButton)
        self.stackedFormWidget.addTab(self.stackedFormWidgetPage4, _fromUtf8(""))
        self.stackedFormWidgetPage5 = QtGui.QWidget()
        self.stackedFormWidgetPage5.setObjectName(_fromUtf8("stackedFormWidgetPage5"))
        self.smoothedSeismicityFormLayout = QtGui.QVBoxLayout(self.stackedFormWidgetPage5)
        self.smoothedSeismicityFormLayout.setObjectName(_fromUtf8("smoothedSeismicityFormLayout"))
        self.smoothedSeismicityChart = FigureCanvasQTAggWidget(self.stackedFormWidgetPage5)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.smoothedSeismicityChart.sizePolicy().hasHeightForWidth())
        self.smoothedSeismicityChart.setSizePolicy(sizePolicy)
        self.smoothedSeismicityChart.setMinimumSize(QtCore.QSize(0, 300))
        self.smoothedSeismicityChart.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.smoothedSeismicityChart.setObjectName(_fromUtf8("smoothedSeismicityChart"))
        self.smoothedSeismicityFormLayout.addWidget(self.smoothedSeismicityChart)
        self.smoothedSeismicityButton = QtGui.QPushButton(self.stackedFormWidgetPage5)
        self.smoothedSeismicityButton.setObjectName(_fromUtf8("smoothedSeismicityButton"))
        self.smoothedSeismicityFormLayout.addWidget(self.smoothedSeismicityButton)
        self.stackedFormWidget.addTab(self.stackedFormWidgetPage5, _fromUtf8(""))
        self.stackedFormWidgetPage6 = QtGui.QWidget()
        self.stackedFormWidgetPage6.setObjectName(_fromUtf8("stackedFormWidgetPage6"))
        self.stackedFormWidget.addTab(self.stackedFormWidgetPage6, _fromUtf8(""))
        self.stackedFormWidgetPage7 = QtGui.QWidget()
        self.stackedFormWidgetPage7.setObjectName(_fromUtf8("stackedFormWidgetPage7"))
        self.gridLayout_7 = QtGui.QGridLayout(self.stackedFormWidgetPage7)
        self.gridLayout_7.setObjectName(_fromUtf8("gridLayout_7"))
        self.catalogueTableView = QtGui.QTableView(self.stackedFormWidgetPage7)
        self.catalogueTableView.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.catalogueTableView.setSelectionMode(QtGui.QAbstractItemView.NoSelection)
        self.catalogueTableView.setSortingEnabled(True)
        self.catalogueTableView.setObjectName(_fromUtf8("catalogueTableView"))
        self.catalogueTableView.verticalHeader().setVisible(False)
        self.gridLayout_7.addWidget(self.catalogueTableView, 0, 0, 1, 1)
        self.stackedFormWidget.addTab(self.stackedFormWidgetPage7, _fromUtf8(""))
        self.horizontalLayout.addWidget(self.stackedFormWidget)
        self.outputVerticalLayout = QtGui.QVBoxLayout()
        self.outputVerticalLayout.setObjectName(_fromUtf8("outputVerticalLayout"))
        self.mapWidget = QgsMapCanvas(self.centralWidget)
        self.mapWidget.setMinimumSize(QtCore.QSize(300, 400))
        self.mapWidget.setMaximumSize(QtCore.QSize(16777215, 600))
        self.mapWidget.setObjectName(_fromUtf8("mapWidget"))
        self.outputVerticalLayout.addWidget(self.mapWidget)
        self.resultsTable = QtGui.QTableWidget(self.centralWidget)
        self.resultsTable.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.resultsTable.setSelectionMode(QtGui.QAbstractItemView.NoSelection)
        self.resultsTable.setSelectionBehavior(QtGui.QAbstractItemView.SelectColumns)
        self.resultsTable.setObjectName(_fromUtf8("resultsTable"))
        self.resultsTable.setColumnCount(0)
        self.resultsTable.setRowCount(0)
        self.outputVerticalLayout.addWidget(self.resultsTable)
        self.horizontalLayout.addLayout(self.outputVerticalLayout)
        HMTKWindow.setCentralWidget(self.centralWidget)
        self.menuBar = QtGui.QMenuBar(HMTKWindow)
        self.menuBar.setGeometry(QtCore.QRect(0, 0, 1214, 22))
        self.menuBar.setObjectName(_fromUtf8("menuBar"))
        self.menuFile = QtGui.QMenu(self.menuBar)
        self.menuFile.setObjectName(_fromUtf8("menuFile"))
        self.menuExport = QtGui.QMenu(self.menuFile)
        self.menuExport.setObjectName(_fromUtf8("menuExport"))
        self.menuLoad_catalogue = QtGui.QMenu(self.menuFile)
        self.menuLoad_catalogue.setObjectName(_fromUtf8("menuLoad_catalogue"))
        self.menuPlatform = QtGui.QMenu(self.menuFile)
        self.menuPlatform.setObjectName(_fromUtf8("menuPlatform"))
        self.menuTools = QtGui.QMenu(self.menuBar)
        self.menuTools.setObjectName(_fromUtf8("menuTools"))
        self.menuEdit = QtGui.QMenu(self.menuBar)
        self.menuEdit.setObjectName(_fromUtf8("menuEdit"))
        self.menuSelect = QtGui.QMenu(self.menuEdit)
        self.menuSelect.setObjectName(_fromUtf8("menuSelect"))
        self.menuView = QtGui.QMenu(self.menuBar)
        self.menuView.setObjectName(_fromUtf8("menuView"))
        self.menuStyle_Events = QtGui.QMenu(self.menuView)
        self.menuStyle_Events.setObjectName(_fromUtf8("menuStyle_Events"))
        self.menuStyle_Sources = QtGui.QMenu(self.menuView)
        self.menuStyle_Sources.setObjectName(_fromUtf8("menuStyle_Sources"))
        self.menuHelp = QtGui.QMenu(self.menuBar)
        self.menuHelp.setObjectName(_fromUtf8("menuHelp"))
        HMTKWindow.setMenuBar(self.menuBar)
        self.toolBar = QtGui.QToolBar(HMTKWindow)
        self.toolBar.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.toolBar.setMovable(False)
        self.toolBar.setAllowedAreas(QtCore.Qt.TopToolBarArea)
        self.toolBar.setIconSize(QtCore.QSize(24, 24))
        self.toolBar.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.toolBar.setFloatable(False)
        self.toolBar.setObjectName(_fromUtf8("toolBar"))
        HMTKWindow.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBar)
        self.statusBar = QtGui.QStatusBar(HMTKWindow)
        self.statusBar.setObjectName(_fromUtf8("statusBar"))
        HMTKWindow.setStatusBar(self.statusBar)
        self.actionDeclustering = QtGui.QAction(HMTKWindow)
        self.actionDeclustering.setObjectName(_fromUtf8("actionDeclustering"))
        self.actionRecurrenceModel = QtGui.QAction(HMTKWindow)
        self.actionRecurrenceModel.setObjectName(_fromUtf8("actionRecurrenceModel"))
        self.actionCompleteness = QtGui.QAction(HMTKWindow)
        self.actionCompleteness.setObjectName(_fromUtf8("actionCompleteness"))
        self.actionMaximumMagnitude = QtGui.QAction(HMTKWindow)
        self.actionMaximumMagnitude.setObjectName(_fromUtf8("actionMaximumMagnitude"))
        self.actionSmoothedSeismicity = QtGui.QAction(HMTKWindow)
        self.actionSmoothedSeismicity.setObjectName(_fromUtf8("actionSmoothedSeismicity"))
        self.actionSaveCatalogue = QtGui.QAction(HMTKWindow)
        self.actionSaveCatalogue.setObjectName(_fromUtf8("actionSaveCatalogue"))
        self.actionLoadCatalogue = QtGui.QAction(HMTKWindow)
        self.actionLoadCatalogue.setObjectName(_fromUtf8("actionLoadCatalogue"))
        self.actionLoadSourceNRML = QtGui.QAction(HMTKWindow)
        self.actionLoadSourceNRML.setObjectName(_fromUtf8("actionLoadSourceNRML"))
        self.actionCatalogueAnalysis = QtGui.QAction(HMTKWindow)
        self.actionCatalogueAnalysis.setObjectName(_fromUtf8("actionCatalogueAnalysis"))
        self.actionEventsInspector = QtGui.QAction(HMTKWindow)
        self.actionEventsInspector.setObjectName(_fromUtf8("actionEventsInspector"))
        self.actionZoomIn = QtGui.QAction(HMTKWindow)
        self.actionZoomIn.setCheckable(True)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8(":/zoomIn.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionZoomIn.setIcon(icon)
        self.actionZoomIn.setObjectName(_fromUtf8("actionZoomIn"))
        self.actionZoomOut = QtGui.QAction(HMTKWindow)
        self.actionZoomOut.setCheckable(True)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(_fromUtf8(":/zoomOut.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionZoomOut.setIcon(icon1)
        self.actionZoomOut.setObjectName(_fromUtf8("actionZoomOut"))
        self.actionPan = QtGui.QAction(HMTKWindow)
        self.actionPan.setCheckable(True)
        self.actionPan.setChecked(True)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(_fromUtf8(":/pan.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionPan.setIcon(icon2)
        self.actionPan.setObjectName(_fromUtf8("actionPan"))
        self.actionIdentify = QtGui.QAction(HMTKWindow)
        self.actionIdentify.setCheckable(True)
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap(_fromUtf8(":/identify.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionIdentify.setIcon(icon3)
        self.actionIdentify.setObjectName(_fromUtf8("actionIdentify"))
        self.actionUndo = QtGui.QAction(HMTKWindow)
        self.actionUndo.setObjectName(_fromUtf8("actionUndo"))
        self.actionPlatformViewCatalogue = QtGui.QAction(HMTKWindow)
        self.actionPlatformViewCatalogue.setObjectName(_fromUtf8("actionPlatformViewCatalogue"))
        self.actionPlatformUploadModels = QtGui.QAction(HMTKWindow)
        self.actionPlatformUploadModels.setObjectName(_fromUtf8("actionPlatformUploadModels"))
        self.actionDeleteUnselectedEvents = QtGui.QAction(HMTKWindow)
        self.actionDeleteUnselectedEvents.setObjectName(_fromUtf8("actionDeleteUnselectedEvents"))
        self.actionWithinPolyhedra = QtGui.QAction(HMTKWindow)
        self.actionWithinPolyhedra.setObjectName(_fromUtf8("actionWithinPolyhedra"))
        self.actionWithinJoynerBooreSource = QtGui.QAction(HMTKWindow)
        self.actionWithinJoynerBooreSource.setObjectName(_fromUtf8("actionWithinJoynerBooreSource"))
        self.actionWithinRuptureDistance = QtGui.QAction(HMTKWindow)
        self.actionWithinRuptureDistance.setObjectName(_fromUtf8("actionWithinRuptureDistance"))
        self.actionWithinSquare = QtGui.QAction(HMTKWindow)
        self.actionWithinSquare.setObjectName(_fromUtf8("actionWithinSquare"))
        self.actionWithinDistance = QtGui.QAction(HMTKWindow)
        self.actionWithinDistance.setObjectName(_fromUtf8("actionWithinDistance"))
        self.actionWithinJoynerBoorePoint = QtGui.QAction(HMTKWindow)
        self.actionWithinJoynerBoorePoint.setObjectName(_fromUtf8("actionWithinJoynerBoorePoint"))
        self.actionTimeBetween = QtGui.QAction(HMTKWindow)
        self.actionTimeBetween.setObjectName(_fromUtf8("actionTimeBetween"))
        self.actionFieldBetween = QtGui.QAction(HMTKWindow)
        self.actionFieldBetween.setObjectName(_fromUtf8("actionFieldBetween"))
        self.actionReloadPlugin = QtGui.QAction(HMTKWindow)
        self.actionReloadPlugin.setObjectName(_fromUtf8("actionReloadPlugin"))
        self.actionCatalogueStyleByCluster = QtGui.QAction(HMTKWindow)
        self.actionCatalogueStyleByCluster.setObjectName(_fromUtf8("actionCatalogueStyleByCluster"))
        self.actionCatalogueStyleByDepthMagnitude = QtGui.QAction(HMTKWindow)
        self.actionCatalogueStyleByDepthMagnitude.setObjectName(_fromUtf8("actionCatalogueStyleByDepthMagnitude"))
        self.actionInvertSelection = QtGui.QAction(HMTKWindow)
        self.actionInvertSelection.setObjectName(_fromUtf8("actionInvertSelection"))
        self.actionUnselectAall = QtGui.QAction(HMTKWindow)
        self.actionUnselectAall.setObjectName(_fromUtf8("actionUnselectAall"))
        self.actionManual = QtGui.QAction(HMTKWindow)
        self.actionManual.setObjectName(_fromUtf8("actionManual"))
        self.actionTutorial = QtGui.QAction(HMTKWindow)
        self.actionTutorial.setObjectName(_fromUtf8("actionTutorial"))
        self.actionVisitGEMWebsite = QtGui.QAction(HMTKWindow)
        self.actionVisitGEMWebsite.setObjectName(_fromUtf8("actionVisitGEMWebsite"))
        self.actionSelectionEditor = QtGui.QAction(HMTKWindow)
        self.actionSelectionEditor.setObjectName(_fromUtf8("actionSelectionEditor"))
        self.actionCatalogueStyleByCompleteness = QtGui.QAction(HMTKWindow)
        self.actionCatalogueStyleByCompleteness.setObjectName(_fromUtf8("actionCatalogueStyleByCompleteness"))
        self.menuLoad_catalogue.addAction(self.actionLoadCatalogue)
        self.menuLoad_catalogue.addAction(self.actionLoadSourceNRML)
        self.menuPlatform.addAction(self.actionPlatformViewCatalogue)
        self.menuPlatform.addAction(self.actionPlatformUploadModels)
        self.menuFile.addAction(self.menuLoad_catalogue.menuAction())
        self.menuFile.addAction(self.actionSaveCatalogue)
        self.menuFile.addAction(self.menuExport.menuAction())
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.menuPlatform.menuAction())
        self.menuFile.addAction(self.actionReloadPlugin)
        self.menuTools.addAction(self.actionDeclustering)
        self.menuTools.addAction(self.actionCompleteness)
        self.menuTools.addAction(self.actionRecurrenceModel)
        self.menuTools.addAction(self.actionMaximumMagnitude)
        self.menuTools.addAction(self.actionSmoothedSeismicity)
        self.menuTools.addSeparator()
        self.menuTools.addAction(self.actionCatalogueAnalysis)
        self.menuTools.addAction(self.actionEventsInspector)
        self.menuSelect.addAction(self.actionWithinPolyhedra)
        self.menuSelect.addAction(self.actionWithinJoynerBooreSource)
        self.menuSelect.addAction(self.actionWithinRuptureDistance)
        self.menuSelect.addAction(self.actionWithinSquare)
        self.menuSelect.addAction(self.actionWithinDistance)
        self.menuSelect.addAction(self.actionWithinJoynerBoorePoint)
        self.menuSelect.addAction(self.actionTimeBetween)
        self.menuSelect.addAction(self.actionFieldBetween)
        self.menuEdit.addAction(self.actionUndo)
        self.menuEdit.addAction(self.actionUnselectAall)
        self.menuEdit.addAction(self.menuSelect.menuAction())
        self.menuEdit.addAction(self.actionInvertSelection)
        self.menuEdit.addAction(self.actionDeleteUnselectedEvents)
        self.menuStyle_Events.addAction(self.actionCatalogueStyleByDepthMagnitude)
        self.menuStyle_Events.addAction(self.actionCatalogueStyleByCluster)
        self.menuStyle_Events.addAction(self.actionCatalogueStyleByCompleteness)
        self.menuView.addAction(self.menuStyle_Events.menuAction())
        self.menuView.addAction(self.menuStyle_Sources.menuAction())
        self.menuView.addSeparator()
        self.menuView.addAction(self.actionSelectionEditor)
        self.menuHelp.addAction(self.actionManual)
        self.menuHelp.addAction(self.actionTutorial)
        self.menuHelp.addSeparator()
        self.menuHelp.addAction(self.actionVisitGEMWebsite)
        self.menuBar.addAction(self.menuFile.menuAction())
        self.menuBar.addAction(self.menuEdit.menuAction())
        self.menuBar.addAction(self.menuView.menuAction())
        self.menuBar.addAction(self.menuTools.menuAction())
        self.menuBar.addAction(self.menuHelp.menuAction())
        self.toolBar.addAction(self.actionZoomIn)
        self.toolBar.addAction(self.actionZoomOut)
        self.toolBar.addAction(self.actionPan)
        self.toolBar.addAction(self.actionIdentify)

        self.retranslateUi(HMTKWindow)
        self.stackedFormWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(HMTKWindow)

    def retranslateUi(self, HMTKWindow):
        HMTKWindow.setWindowTitle(_translate("HMTKWindow", "Hazard Modeller\'s Toolkit", None))
        self.declusterButton.setText(_translate("HMTKWindow", "Decluster", None))
        self.declusteringPurgeButton.setText(_translate("HMTKWindow", "Purge Catalogue", None))
        self.stackedFormWidget.setTabText(self.stackedFormWidget.indexOf(self.stackedFormWidgetPage1), _translate("HMTKWindow", "Declustering", None))
        self.stackedFormWidget.setTabToolTip(self.stackedFormWidget.indexOf(self.stackedFormWidgetPage1), _translate("HMTKWindow", "Declustering", None))
        self.completenessButton.setText(_translate("HMTKWindow", "Run Analysis", None))
        self.completenessPurgeButton.setText(_translate("HMTKWindow", "Purge Catalogue", None))
        self.stackedFormWidget.setTabText(self.stackedFormWidget.indexOf(self.stackedFormWidgetPage2), _translate("HMTKWindow", "Completeness", None))
        self.stackedFormWidget.setTabToolTip(self.stackedFormWidget.indexOf(self.stackedFormWidgetPage2), _translate("HMTKWindow", "Completeness", None))
        self.recurrenceModelButton.setText(_translate("HMTKWindow", "Run Analysis", None))
        self.stackedFormWidget.setTabText(self.stackedFormWidget.indexOf(self.stackedFormWidgetPage3), _translate("HMTKWindow", "Recurrence Model", None))
        self.stackedFormWidget.setTabToolTip(self.stackedFormWidget.indexOf(self.stackedFormWidgetPage3), _translate("HMTKWindow", "Recurrence Model", None))
        self.maxMagnitudeButton.setText(_translate("HMTKWindow", "Run Analysis", None))
        self.stackedFormWidget.setTabText(self.stackedFormWidget.indexOf(self.stackedFormWidgetPage4), _translate("HMTKWindow", "Maximum Magnitude", None))
        self.stackedFormWidget.setTabToolTip(self.stackedFormWidget.indexOf(self.stackedFormWidgetPage4), _translate("HMTKWindow", "Maximum Magnitude", None))
        self.smoothedSeismicityButton.setText(_translate("HMTKWindow", "Run Analysis", None))
        self.stackedFormWidget.setTabText(self.stackedFormWidget.indexOf(self.stackedFormWidgetPage5), _translate("HMTKWindow", "Smoothed Seismicity", None))
        self.stackedFormWidget.setTabToolTip(self.stackedFormWidget.indexOf(self.stackedFormWidgetPage5), _translate("HMTKWindow", "Smoothed Seismicity", None))
        self.stackedFormWidget.setTabText(self.stackedFormWidget.indexOf(self.stackedFormWidgetPage6), _translate("HMTKWindow", "Catalogue Analysis", None))
        self.stackedFormWidget.setTabToolTip(self.stackedFormWidget.indexOf(self.stackedFormWidgetPage6), _translate("HMTKWindow", "Catalogue Analysis", None))
        self.stackedFormWidget.setTabText(self.stackedFormWidget.indexOf(self.stackedFormWidgetPage7), _translate("HMTKWindow", "Events", None))
        self.stackedFormWidget.setTabToolTip(self.stackedFormWidget.indexOf(self.stackedFormWidgetPage7), _translate("HMTKWindow", "Events inspector", None))
        self.menuFile.setTitle(_translate("HMTKWindow", "File", None))
        self.menuExport.setTitle(_translate("HMTKWindow", "Export", None))
        self.menuLoad_catalogue.setTitle(_translate("HMTKWindow", "Load", None))
        self.menuPlatform.setTitle(_translate("HMTKWindow", "Platform", None))
        self.menuTools.setTitle(_translate("HMTKWindow", "Tools", None))
        self.menuEdit.setTitle(_translate("HMTKWindow", "Edit", None))
        self.menuSelect.setTitle(_translate("HMTKWindow", "Select events", None))
        self.menuView.setTitle(_translate("HMTKWindow", "View", None))
        self.menuStyle_Events.setTitle(_translate("HMTKWindow", "Style Events", None))
        self.menuStyle_Sources.setTitle(_translate("HMTKWindow", "Style Sources", None))
        self.menuHelp.setTitle(_translate("HMTKWindow", "Help", None))
        self.toolBar.setWindowTitle(_translate("HMTKWindow", "toolBar", None))
        self.actionDeclustering.setText(_translate("HMTKWindow", "Declustering", None))
        self.actionDeclustering.setShortcut(_translate("HMTKWindow", "Ctrl+1", None))
        self.actionRecurrenceModel.setText(_translate("HMTKWindow", "Recurrence Model", None))
        self.actionRecurrenceModel.setShortcut(_translate("HMTKWindow", "Ctrl+3", None))
        self.actionCompleteness.setText(_translate("HMTKWindow", "Completeness", None))
        self.actionCompleteness.setShortcut(_translate("HMTKWindow", "Ctrl+2", None))
        self.actionMaximumMagnitude.setText(_translate("HMTKWindow", "Maximum Magnitude", None))
        self.actionMaximumMagnitude.setShortcut(_translate("HMTKWindow", "Ctrl+4", None))
        self.actionSmoothedSeismicity.setText(_translate("HMTKWindow", "Smoothed Seismicity", None))
        self.actionSmoothedSeismicity.setShortcut(_translate("HMTKWindow", "Ctrl+5", None))
        self.actionSaveCatalogue.setText(_translate("HMTKWindow", "Save catalogue", None))
        self.actionLoadCatalogue.setText(_translate("HMTKWindow", "Catalogue", None))
        self.actionLoadSourceNRML.setText(_translate("HMTKWindow", "Source Model (NRML)", None))
        self.actionCatalogueAnalysis.setText(_translate("HMTKWindow", "Catalogue Analysis", None))
        self.actionCatalogueAnalysis.setShortcut(_translate("HMTKWindow", "Ctrl+6", None))
        self.actionEventsInspector.setText(_translate("HMTKWindow", "Events Inspector", None))
        self.actionEventsInspector.setShortcut(_translate("HMTKWindow", "Ctrl+7", None))
        self.actionZoomIn.setText(_translate("HMTKWindow", "Zoom In", None))
        self.actionZoomIn.setShortcut(_translate("HMTKWindow", "Ctrl+Shift+=", None))
        self.actionZoomOut.setText(_translate("HMTKWindow", "Zoom out", None))
        self.actionZoomOut.setToolTip(_translate("HMTKWindow", "Zoom out", None))
        self.actionZoomOut.setShortcut(_translate("HMTKWindow", "Ctrl+-", None))
        self.actionPan.setText(_translate("HMTKWindow", "Pan", None))
        self.actionPan.setToolTip(_translate("HMTKWindow", "Pan map", None))
        self.actionIdentify.setText(_translate("HMTKWindow", "Identify", None))
        self.actionIdentify.setToolTip(_translate("HMTKWindow", "Identify features", None))
        self.actionIdentify.setShortcut(_translate("HMTKWindow", "Ctrl+I", None))
        self.actionUndo.setText(_translate("HMTKWindow", "Undo model change", None))
        self.actionUndo.setShortcut(_translate("HMTKWindow", "Ctrl+Z", None))
        self.actionPlatformViewCatalogue.setText(_translate("HMTKWindow", "Share", None))
        self.actionPlatformUploadModels.setText(_translate("HMTKWindow", "Import", None))
        self.actionDeleteUnselectedEvents.setText(_translate("HMTKWindow", "Delete unselected events", None))
        self.actionWithinPolyhedra.setText(_translate("HMTKWindow", "within a polyhedra", None))
        self.actionWithinJoynerBooreSource.setText(_translate("HMTKWindow", "within Joyner-Boore distance of source", None))
        self.actionWithinRuptureDistance.setText(_translate("HMTKWindow", "within Rupture distance", None))
        self.actionWithinSquare.setText(_translate("HMTKWindow", "within a Square centered on", None))
        self.actionWithinDistance.setText(_translate("HMTKWindow", "within distance from point", None))
        self.actionWithinJoynerBoorePoint.setText(_translate("HMTKWindow", "within Joyner Boore distance from point", None))
        self.actionTimeBetween.setText(_translate("HMTKWindow", "Time between", None))
        self.actionFieldBetween.setText(_translate("HMTKWindow", "Field between", None))
        self.actionReloadPlugin.setText(_translate("HMTKWindow", "Reload plugins", None))
        self.actionCatalogueStyleByCluster.setText(_translate("HMTKWindow", "by cluster / event type", None))
        self.actionCatalogueStyleByDepthMagnitude.setText(_translate("HMTKWindow", "by depth / magnitude", None))
        self.actionInvertSelection.setText(_translate("HMTKWindow", "Invert selection", None))
        self.actionUnselectAall.setText(_translate("HMTKWindow", "Unselect all", None))
        self.actionManual.setText(_translate("HMTKWindow", "Manual", None))
        self.actionTutorial.setText(_translate("HMTKWindow", "Hazard Modeller\'s Toolkit Tutorial", None))
        self.actionVisitGEMWebsite.setText(_translate("HMTKWindow", "Visit GEM website", None))
        self.actionSelectionEditor.setText(_translate("HMTKWindow", "Selection editor", None))
        self.actionCatalogueStyleByCompleteness.setText(_translate("HMTKWindow", "by completeness", None))

from widgets import FigureCanvasQTAggWidget
from qgis.gui import QgsMapCanvas
import images_rc
