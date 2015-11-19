#-----------------------------------------------------------
# Copyright (C) 2015 Peter Petrik
#-----------------------------------------------------------
# Licensed under the terms of GNU GPL 2
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#---------------------------------------------------------------------

from PyQt4.QtGui import *
from PyQt4.QtCore import *
from qgis.core import *
import collections

def classFactory(iface):
    return MinimalPlugin(iface)

def export_to_mapserver_format(cr_name, min_val, max_val, nodata_val, invert):
    cr = QgsStyleV2.defaultStyle().colorRamp(cr_name)
    if not cr:
        return "Invalid colormap name"

    ramp = collections.OrderedDict()
    ramp[0] = cr.color1()
    for cstop in cr.stops():
        ramp[cstop.offset] = cstop.color
    ramp[1] = cr.color2()
    return ramp_to_style(cr_name, min_val, max_val, nodata_val, invert, ramp)

def color_to_rgb(color):
    return str(color.red()) + " " + str(color.green()) + " " + str(color.blue())

def ramp_to_style(cr_name, min_val, max_val, nodata_val, invert, ramp):
    res = "# From QGIS colormap: " + cr_name + "\n"
    if invert:
        res += "# Inverted\n"
    res += "# Min value: " + str(min_val) + "\n"
    res += "# Max value: " + str(max_val) + "\n"
    res += "# NODATA value: " + str(nodata_val) + "\n"
    last_color = None
    last_value = None

    for perc, color in ramp.iteritems():
        value = min_val + (max_val - min_val)*perc

        if invert:
            color = QColor(256-color.red(), 256-color.green(), 256-color.blue())

        if last_color is not None:
            res += "CLASS\n"

            if last_value < nodata_val and value > nodata_val:
                res += "  EXPRESSION (([pixel] < " + str(nodata_val) + ") OR ([pixel] > " + str(nodata_val+0.001) + "))\n"

            res += "  STYLE\n"
            res += "    DATARANGE " + str(last_value) + " " + str(value) + "\n"
            res += "    RANGEITEM \"pixel\"\n"
            res += "    COLORRANGE " + color_to_rgb(last_color) + " " + color_to_rgb(color) + "\n"
            res += "  END\n"
            res += "END\n"

        last_color = color
        last_value = value

    return res

class PluginDialog(QDialog):
    def __init__(self):
        super(PluginDialog, self).__init__()
        self.setWindowTitle("Export colormap")
        vbox = QVBoxLayout()
        vbox.addStretch(1)

        lName = QLabel("Colormap name")
        self.tbName = QLineEdit()
        lMin = QLabel("Minimum value")
        self.tbMin = QLineEdit()
        lMax = QLabel("Maximum value")
        self.tbMax = QLineEdit()
        lNoData = QLabel("NODATA value")
        self.tbNoData = QLineEdit("0.0")
        self.cbInverted=QCheckBox("Inverted?")
        okButton = QPushButton("OK")

        vbox.addWidget(lName)
        vbox.addWidget(self.tbName)
        vbox.addWidget(lMin)
        vbox.addWidget(self.tbMin)
        vbox.addWidget(lMax)
        vbox.addWidget(self.tbMax)
        vbox.addWidget(lNoData)
        vbox.addWidget(self.tbNoData)
        vbox.addWidget(self.cbInverted)
        vbox.addWidget(okButton)

        self.setLayout(vbox)

        okButton.clicked.connect(self.handleButton)

    def handleButton(self):
        try:
            cr_name = self.tbName.text();
            min_val = float(self.tbMin.text());
            max_val = float(self.tbMax.text());
            nodata_val = float(self.tbNoData.text());
            invert = self.cbInverted.isChecked();
            res = export_to_mapserver_format(cr_name, min_val, max_val, nodata_val, invert)
        except ValueError:
            res = "Invalid min/max (not float)"

        QMessageBox.information(None, "Result", res)
        self.close()

class MinimalPlugin:
    def __init__(self, iface):
        self.iface = iface

    def initGui(self):
        self.action = QAction("MapserverExport", self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addToolBarIcon(self.action)

    def unload(self):
        self.iface.removeToolBarIcon(self.action)
        del self.action

    def run(self):
        dialog = PluginDialog()
        dialog.exec_()
