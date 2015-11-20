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

class Exporter():
    def __init__(self, cr_name, riattr, min_val, max_val, invert, keep_end_color):
        self.cr_name = cr_name
        self.riattr = riattr
        self.min_val = min_val
        self.max_val = max_val
        self.invert = invert
        self.keep_end_color = keep_end_color

    def export(self):
        cr = QgsStyleV2.defaultStyle().colorRamp(self.cr_name)
        if not cr:
            return "Invalid colormap name"

        ramp = collections.OrderedDict()
        ramp[0] = cr.color1()
        for cstop in cr.stops():
            ramp[cstop.offset] = cstop.color
        ramp[1] = cr.color2()

        if self.invert:
            items = ramp.items()
            items.reverse()
            ramp = collections.OrderedDict(items)
            new_ramp = collections.OrderedDict()
            for key, val in ramp.iteritems():
                new_ramp[1-key] = val
            ramp = new_ramp

        return self._ramp_to_style(ramp)

    def _color_to_rgb(self, color):
        return str(color.red()) + " " + str(color.green()) + " " + str(color.blue())

    def _expression_format(self, minimum=None, maximum=None):
        if minimum is None:
            return "  EXPRESSION ([" + self.riattr +"] > " + str(maximum) + ")\n"
        elif maximum is None:
            return "  EXPRESSION ([" + self.riattr +"] < " + str(minimum) + ")\n"
        else:
            return "  EXPRESSION (([" + self.riattr +"] >= " + str(minimum) + ") AND ([" + self.riattr +"] < " + str(maximum) + "))\n"

    def _single_color_format(self, color, minimum=None, maximum=None):
        res = "CLASS\n"
        res += self._expression_format(minimum, maximum)
        res += "  STYLE\n"
        res += "    COLOR " + self._color_to_rgb(color) + "\n"
        res += "  END\n"
        res += "END\n"
        return res

    def _colorrange_format(self, min_color, max_color, min_val, max_val):
        res = "CLASS\n"
        res += self._expression_format(min_val, max_val)
        res += "  STYLE\n"
        res += "    DATARANGE " + str(min_val) + " " + str(max_val) + "\n"
        res += "    RANGEITEM \"" + self.riattr +"\"\n"
        res += "    COLORRANGE " + self._color_to_rgb(min_color) + " " + self._color_to_rgb(max_color) + "\n"
        res += "  END\n"
        res += "END\n"
        return res

    def _ramp_to_style(self, ramp):
        res = "# From QGIS colormap: " + self.cr_name + "\n"
        if self.invert:
            res += "# Inverted\n"
        res += "# Min value: " + str(self.min_val) + "\n"
        res += "# Max value: " + str(self.max_val) + "\n"
        last_color = None
        last_value = None

        # special treatment for end colors
        if self.keep_end_color:
            color = ramp[0]
            res += self._single_color_format(color, minimum=self.min_val)

        # middle colors
        for perc, color in ramp.iteritems():
            value = self.min_val + (self.max_val - self.min_val)*perc

            if last_color is not None:
                res += self._colorrange_format(last_color, color, last_value, value)

            last_color = color
            last_value = value

        # special treatment for end colors
        if self.keep_end_color:
            color = ramp[1]
            res += self._single_color_format(color, maximum=self.max_val)

        return res

class PluginDialog(QDialog):
    def __init__(self):
        super(PluginDialog, self).__init__()
        self.setWindowTitle("Export colormap")
        vbox = QVBoxLayout()
        vbox.addStretch(1)

        lName = QLabel("Colormap name")
        self.tbName = QLineEdit("Greens")
        lMin = QLabel("Minimum value")
        self.tbMin = QLineEdit("0.0")
        lMax = QLabel("Maximum value")
        self.tbMax = QLineEdit("1.0")
        lRIAttr= QLabel("RANGEITEM attribute")
        self.tbRIAttr = QLineEdit("pixel")
        self.cbInverted=QCheckBox("Inverted?")
        self.cbEndColor=QCheckBox("Keep end color?")
        okButton = QPushButton("OK")

        vbox.addWidget(lName)
        vbox.addWidget(self.tbName)
        vbox.addWidget(lMin)
        vbox.addWidget(self.tbMin)
        vbox.addWidget(lMax)
        vbox.addWidget(self.tbMax)
        vbox.addWidget(lRIAttr)
        vbox.addWidget(self.tbRIAttr)
        vbox.addWidget(self.cbInverted)
        vbox.addWidget(self.cbEndColor)
        vbox.addWidget(okButton)

        self.setLayout(vbox)

        okButton.clicked.connect(self.handleButton)

    def handleButton(self):
        try:
            cr_name = self.tbName.text();
            min_val = float(self.tbMin.text());
            max_val = float(self.tbMax.text());
            invert = self.cbInverted.isChecked();
            keep_end_color = self.cbEndColor.isChecked();
            riattr = self.tbRIAttr.text();
            exporter = Exporter(cr_name, riattr, min_val, max_val, invert, keep_end_color)
            res = exporter.export()

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
