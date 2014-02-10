import os
import sys
import sip

try:
    sip.setapi("QString", 2)
except ValueError:  # API 'QString' has already been set to version 1

    pass

from PyQt4 import QtCore, QtGui
import customtableview
from customtableview import tr, messagebox

from openquake.nrmllib.node import node_to_nrml
from openquake.common.converter import Converter


class MainWindow(QtGui.QMainWindow):
    MENU_NEW = '''\
VM,VulnerabilityModel,Ctrl+Shift+V,new_vulnerability_model
FMD,FragilityModelDiscrete,Ctrl+Shift+F,new_fragility_model_discrete
FMC,FragilityModelContinuous,Ctrl+Alt+F,new_fragility_model_continuous
EMP,ExposureModelPopulation,Ctrl+Shift+P,new_exposure_model_population
EMP,ExposureModelBuildings,Ctrl+Alt+P,new_exposure_model_buildings
'''

    def __init__(self, nrmlfile=None):
        QtGui.QMainWindow.__init__(self)
        self.setWindowTitle(tr("Input Tool Window"))
        self.setupMenu()
        if nrmlfile:
            self.set_central_widget(nrmlfile)

    def set_central_widget(self, nrmlfile):
        self.nrmlfile = nrmlfile
        with messagebox(self):
            converter = Converter.from_nrml(nrmlfile)
        self.tableset = converter.tableset
        widgetname = converter.__class__.__name__ + 'Widget'
        widgetclass = getattr(customtableview, widgetname)
        self.widget = widgetclass(converter.tableset, nrmlfile, self)
        self.setCentralWidget(self.widget)

    def setupMenuNew(self):
        self.menuNew = QtGui.QMenu(self.menuFile)
        self.menuNew.setObjectName("menuNew")
        rows = [line.split(',') for line in self.MENU_NEW.splitlines()]
        for abbrev, name, shortcut, method in rows:
            action_name = 'actionNew' + abbrev
            action = QtGui.QAction(self)
            action.setObjectName(action_name)
            setattr(self, action_name, action)
            action.setText(tr(name))
            action.setShortcut(tr(shortcut))
            self.menuNew.addAction(action)
            action.triggered.connect(getattr(self, method))

    def setupMenu(self):
        self.menubar = QtGui.QMenuBar(self)
        self.menubar.setObjectName("menubar")
        self.menuFile = QtGui.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        self.setMenuBar(self.menubar)
        self.setupMenuNew()

        self.actionOpen = QtGui.QAction(self)
        self.actionOpen.setObjectName("actionOpen")
        self.actionSave = QtGui.QAction(self)
        self.actionSave.setObjectName("actionSave")
        self.actionWrite = QtGui.QAction(self)
        self.actionWrite.setObjectName("actionWrite")
        self.actionFullCheck = QtGui.QAction(self)
        self.actionFullCheck.setObjectName("actionFullCheck")
        self.actionCopy = QtGui.QAction(self)
        self.actionCopy.setObjectName("actionCopy")
        self.actionPaste = QtGui.QAction(self)
        self.actionPaste.setObjectName("actionPaste")
        self.actionReload = QtGui.QAction(self)
        self.actionReload.setObjectName("actionReload")
        self.actionQuit = QtGui.QAction(self)
        self.actionQuit.setObjectName("actionQuit")

        self.menuFile.addMenu(self.menuNew)
        self.menuFile.addAction(self.actionOpen)
        self.menuFile.addAction(self.actionSave)
        self.menuFile.addAction(self.actionWrite)
        self.menuFile.addAction(self.actionCopy)
        self.menuFile.addAction(self.actionFullCheck)
        self.menuFile.addAction(self.actionPaste)
        self.menuFile.addAction(self.actionReload)
        self.menuFile.addAction(self.actionQuit)

        self.menubar.addMenu(self.menuFile)
        self.menuFile.setTitle(tr("InputToolWindow"))

        self.menuNew.setTitle(tr("New"))

        self.menuFile.setTitle(tr("File"))
        self.actionOpen.setText(tr("&Open"))
        self.actionOpen.setShortcut(tr("Ctrl+O"))
        self.actionSave.setText(tr("&Save"))
        self.actionSave.setShortcut(tr("Ctrl+S"))
        self.actionWrite.setText(tr("&Save As"))
        self.actionWrite.setShortcut(tr("Ctrl+Shift+S"))
        self.actionCopy.setText(tr("&Copy"))
        self.actionCopy.setShortcut(tr("Ctrl+C"))
        self.actionFullCheck.setText(tr("&FullCheck"))
        self.actionFullCheck.setShortcut(tr("Ctrl+F"))
        self.actionPaste.setText(tr("&Paste"))
        self.actionPaste.setShortcut(tr("Ctrl+V"))
        self.actionReload.setText(tr("&Reload"))
        self.actionReload.setShortcut(tr("Ctrl+R"))
        self.actionQuit.setText(tr("&Quit"))
        self.actionQuit.setShortcut(tr("Ctrl+Q"))

        # menu actions
        self.actionOpen.triggered.connect(self.open_nrml)
        self.actionSave.triggered.connect(self.save_nrml)
        self.actionWrite.triggered.connect(self.write_nrml)
        self.actionQuit.triggered.connect(self.quit)
        self.actionCopy.triggered.connect(self.copy)
        self.actionPaste.triggered.connect(self.paste)
        self.actionFullCheck.triggered.connect(self.full_check)
        self.actionReload.triggered.connect(
            lambda: self.set_central_widget(self.nrmlfile))

    def copy(self):
        widget = QtGui.QApplication.focusWidget()
        if not isinstance(widget, QtGui.QTableView):
            return
        currsel = widget.parent().current_selection()
        QtGui.QApplication.clipboard().setText(currsel)

    def paste(self):
        widget = QtGui.QApplication.focusWidget()
        if not isinstance(widget, QtGui.QTableView):
            return
        widget = widget.parent()  # CustomTableView
        lines = QtGui.QApplication.clipboard().text().split('\n')
        rows = [line.split('\t') for line in lines]
        if not rows:
            return
        ncolumns = len(widget.table.recordtype) - widget.table.ordinal
        with messagebox(self):
            for row in rows:
                assert len(row) <= ncolumns, 'Got %d columns, expected %d' % (
                    len(row), ncolumns)
            indexes = widget.appendRows(len(rows))
            for index, row in zip(indexes, rows):
                widget.tableModel.set_row(index, row)

    def open_nrml(self):
        nrmlfile = unicode(QtGui.QFileDialog.getOpenFileName(
            self, 'Choose file',
            QtCore.QDir.homePath(),
            "Model file (*.xml);;Config files (*.ini)"))
        self.set_central_widget(nrmlfile)

    def new_vulnerability_model(self):
        empty = '''<?xml version='1.0' encoding='utf-8'?>
        <nrml xmlns="http://openquake.org/xmlns/nrml/0.4">
        <vulnerabilityModel/>
        </nrml>'''
        open('vulnerability-model.xml', 'w').write(empty)
        self.set_central_widget('vulnerability-model.xml')

    def new_fragility_model_discrete(self):
        empty = '''<?xml version='1.0' encoding='utf-8'?>
        <nrml xmlns="http://openquake.org/xmlns/nrml/0.4">
        <fragilityModel format="discrete">
        <description>New fragility model</description>
        <limitStates> </limitStates>
        <ffs>
           <taxonomy> </taxonomy>
           <IML IMT="" imlUnit=""> </IML>
           <ffd><poEs/></ffd>
        </ffs>
        </fragilityModel>
        </nrml>'''
        open('fragility-model-discrete.xml', 'w').write(empty)
        self.set_central_widget('fragility-model-discrete.xml')

    def new_fragility_model_continuous(self):
        empty = '''<?xml version='1.0' encoding='utf-8'?>
        <nrml xmlns="http://openquake.org/xmlns/nrml/0.4">
        <fragilityModel format="continuous">
        <description>New fragility model</description>
        <limitStates> </limitStates>
        <ffs>
           <taxonomy> </taxonomy>
           <IML IMT="" imlUnit="" minIML="" maxIML=""> </IML>
           <ffc><params/></ffc>
        </ffs>
        </fragilityModel>
        </nrml>'''
        open('fragility-model-continuous.xml', 'w').write(empty)
        self.set_central_widget('fragility-model-continuous.xml')

    def new_exposure_model_buildings(self):
        empty = '''<?xml version='1.0' encoding='utf-8'?>
        <nrml xmlns="http://openquake.org/xmlns/nrml/0.4">
        <exposureModel category="buildings"
         id="my_exposure_model"
         taxonomySource="UNKNOWN">
        <description>New exposure model</description>
        <conversions>
            <area type="per_asset" unit="square meters"/>
            <costTypes>
                <costType name="structural" retrofittedType=""
                 retrofittedUnit="" type="" unit=""/>
            </costTypes>
            <deductible isAbsolute="false"/>
            <insuranceLimit isAbsolute="false"/>
        </conversions>
        <assets>
           <asset id="" number="" taxonomy="">
           <location lat="" lon="" />
           <costs>
            <cost deductible="" insuranceLimit=""
                  type="structural" value=""/>
           </costs>
           <occupancies>
             <occupancy occupants="" period=""/>
           </occupancies>
           </asset>
        </assets>
        </exposureModel>
        </nrml>'''
        open('exposure-model-buildings.xml', 'w').write(empty)
        self.set_central_widget('exposure-model-buildings.xml')

    def new_exposure_model_population(self):
        empty = '''<?xml version='1.0' encoding='utf-8'?>
        <nrml xmlns="http://openquake.org/xmlns/nrml/0.4">
        <exposureModel category="population"
         id="my_exposure_model"
         taxonomySource="UNKNOWN">
        <description>New exposure model</description>
        <conversions>
            <area type="per_asset" unit="square meters"/>
        </conversions>
        <assets>
           <asset id="" number="" taxonomy="">
           <location lat="" lon="" />
           <occupancies>
             <occupancy occupants="" period=""/>
           </occupancies>
           </asset>
        </assets>
        </exposureModel>
        </nrml>'''
        open('exposure-model-population.xml', 'w').write(empty)
        self.set_central_widget('exposure-model-population.xml')

    def full_check(self):
        with messagebox(self):
            return self.tableset.to_node()

    def save(self, nrmlfile):  # save on current file
        try:
            node = self.full_check()
        except:
            return
        with messagebox(self):
            # save to a temporary file
            with open(nrmlfile + '~', 'w+') as f:
                node_to_nrml(node, f)
            # only if there are no errors rename the file
            os.rename(nrmlfile + '~', nrmlfile)

    def save_nrml(self):
        """
        Save the current content of the tableset in NRML format
        """
        self.save(self.nrmlfile)

    def write_nrml(self):  # save as
        """
        Save the current content of the tableset in NRML format
        """
        self.nrmlfile = QtGui.QFileDialog.getSaveFileName(
            self, 'Save NRML', '', 'XML (*.xml)')
        if self.nrmlfile:  # can be the empty string if nothing is selected
            self.save(self.nrmlfile)

    def quit(self):
        # TODO: we should check if something has changed before quitting
        QtGui.QApplication.quit()


def main(argv):
    app = QtGui.QApplication(argv, True)
    app.setStyleSheet('''
QTableWidget::item:selected
{ background-color: palette(highlight)}
''')
    mw = MainWindow(sys.argv[1] if sys.argv[1:] else None)
    mw.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    print __file__
    main(sys.argv)
