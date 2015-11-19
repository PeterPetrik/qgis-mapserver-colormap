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

def color_to_rgb(color):
    return str(color.red()) + " " + str(color.green()) + " " + str(color.blue())

def ramp_to_style(cr_name, min_val, max_val, ramp):
    res = "# From QGIS colormap: " + cr_name + "\n"
    res += "# Min value: " + str(min_val) + "\n"
    res += "# Max value: " + str(max_val) + "\n"
    last_color = None
    last_value = None

    for perc, color in ramp.iteritems():
        value = min_val + (max_val - min_val)*perc
        if last_color is not None:
            res += "CLASS\n"
            res += "  STYLE\n"
            res += "    DATARANGE " + str(last_value) + " " + str(value) + "\n"
            res += "    RANGEITEM \"pixel\"\n"
            res += "    COLORRANGE " + color_to_rgb(last_color) + " " + color_to_rgb(color) + "\n"
            res += "  END\n"
            res += "END\n"

        last_color = color
        last_value = value

    return res

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
        cr_name, ok = QInputDialog.getText(None, 'Choose colormap', 'Enter colormap name:')
        if ok:
            cr = QgsStyleV2.defaultStyle().colorRamp(cr_name)
            if cr:
                min_val, ok = QInputDialog.getText(None, 'Choose min', 'Enter minimum val:')
                if ok:
                    max_val, ok = QInputDialog.getText(None, 'Choose max', 'Enter maximum val:')
                    if ok:
                        ramp = collections.OrderedDict()
                        ramp[0] = cr.color1()
                        for cstop in cr.stops():
                            ramp[cstop.offset] = cstop.color
                        ramp[1] = cr.color2()

                        res = ramp_to_style(cr_name, float(min_val), float(max_val), ramp)
                        QMessageBox.information(None, "Copy to mapfile", res)
            else:
                QMessageBox.information(None, "Information", "Wrong colormap name")

