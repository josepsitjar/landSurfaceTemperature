# -*- coding: utf-8 -*-
"""
/***************************************************************************
 LandSurfaceTemperature
                                 A QGIS plugin
 This tool extracts Land Surface Temperature from satellite imagery
                             -------------------
        begin                : 2015-11-10
        copyright            : (C) 2015 by Milton Isaya/Anadolu University
        email                : milton_issaya@hotmail.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""

import os

from PyQt5 import uic, QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QMessageBox

from qgis.PyQt import uic
from qgis.PyQt import QtWidgets

from qgis.utils import iface
from qgis.gui import QgsMessageBar
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.core import QgsMessageLog

from osgeo import gdal

from .lst_functions import EstimateLST

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'lst_tool_dialog_base.ui'))


class LandSurfaceTemperatureDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(LandSurfaceTemperatureDialog, self).__init__(parent)
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        #The code below attaches the close functionality
        self.NDVI_btnClose.clicked.connect(self.closePlugin)
        self.lseZhangClose.clicked.connect(self.closePlugin)
        self.rad_btnClose.clicked.connect(self.closePlugin)
        self.bt_btnClose.clicked.connect(self.closePlugin)
        self.plkClose.clicked.connect(self.closePlugin)
        self.ndviSensorType.currentIndexChanged.connect(self.uiChangeNDVISensorInput)

        #The code below is for the NDVI tab
        self.ndviBrwNIRBand.clicked.connect(self.uiNDVIBrwNIR)
        self.NDVI_btnCalc.clicked.connect(self.uiCalcNDVI)
        self.ndviBrwRedBand.clicked.connect(self.uiNDVIBrwRed)
        self.NDVI_btnOutputBrw.clicked.connect(self.uiNDVIBrwOut)
        self.ndviBrwVNIRBand.clicked.connect(self.uiNDVIBrwVNIR)
        self.uiNDVIOutputFile()
        self.uiChangeNDVISensorInput()

    def closePlugin(self):
        self.close()

    def uiChangeNDVISensorInput(self):
        #Capture the variables from the interface
        self.sensorType = self.ndviSensorType.currentText()
        #Change the interface according to the sensor selected
        if (self.sensorType == 'Landsat'):
            self.ndviLineEditRed.setEnabled(True)
            self.ndviLineEditNIR.setEnabled(True)
            self.ndviBrwRedBand.setEnabled(True)
            self.ndviBrwNIRBand.setEnabled(True)
            self.ndviBrwVNIRBand.setEnabled(False)
            self.ndviLineEditVNIR.setEnabled(False)
            self.ndviLblVNIR.setEnabled(False)
        elif (self.sensorType == 'ASTER'):
            self.ndviLineEditRed.setEnabled(False)
            self.ndviLineEditNIR.setEnabled(False)
            self.ndviBrwRedBand.setEnabled(False)
            self.ndviBrwNIRBand.setEnabled(False)
            self.ndviBrwVNIRBand.setEnabled(True)
            self.ndviLineEditVNIR.setEnabled(True)
            self.ndviLblVNIR.setEnabled(True)

    def uiNDVIBrwNIR(self):
        self.NIRBandPath = QtWidgets.QFileDialog.getOpenFileName(self, 'Select a near infrared raster file', '.')
        self.ndviLineEditNIR.setText(self.NIRBandPath[0])


    def uiNDVIBrwRed(self):
        self.RedBandPath = QtWidgets.QFileDialog.getOpenFileName(self, 'Select a red raster file', '.')
        self.ndviLineEditRed.setText(self.RedBandPath[0])


    def uiNDVIBrwOut(self):
        self.outBandPath = QtWidgets.QFileDialog.getSaveFileName(self, 'Select NDVI file location', '.')
        self.ndviLineEditOutputRaster.setText(self.outBandPath[0])

    def uiNDVIBrwVNIR(self):
        self.vnirBandPath = QtWidgets.QFileDialog.getOpenFileName(self, 'Select a visible and near Infrared raster file', '.')
        self.ndviLineEditVNIR.setText(self.vnirBandPath[0])

    def uiNDVIOutputFile(self):
        self.rasterFormats = self.getGdalRasterFormats()
        for i in range(len(self.rasterFormats)):
            self.ndviFormat.addItem(str(self.rasterFormats[i]))

    def getGdalRasterFormats(self):
        gdal.AllRegister()
        gdalRasters = ['GTiff']
        '''
        for i in range(0, gdal.GetDriverCount()):
            metadata = gdal.GetDriverCount()
            drv = gdal.GetDriver(i)
            drv_meta = drv.GetMetadata()
            if ('DMD_EXTENSION' in drv_meta):
                gdalRasters.append(drv.ShortName)
        '''
        return gdalRasters

    def uiCalcNDVI(self):
        self.sensorType   = self.ndviSensorType.currentText()
        self.NIRBand      = self.ndviLineEditNIR.text()
        self.VNIRBand     = self.ndviLineEditVNIR.text()
        self.RedBand      = self.ndviLineEditRed.text()
        self.outputRaster = self.ndviLineEditOutputRaster.text()
        self.rasterType   = str(self.ndviFormat.currentText())


        #Loading the raster to the QGIS project
        if (self.ndviAddToProject.isChecked()):
            self.addToQGIS = 'Yes'
        else:
            self.addToQGIS = 'No'
        if self.sensorType == 'Landsat':
            #Validate the inputs when the selected sensor is Landsat
            if self.NIRBand == '':
                iface.messageBar().pushWarning("Land Surface Temperature Plugin","The near infrared band is required")
            elif self.RedBand == '':
                iface.messageBar().pushWarning("Land Surface Temperature Plugin","The red band is required")
            elif self.outputRaster == '':
                iface.messageBar().pushWarning("Land Surface Temperature Plugin","The output save location is required")
            elif self.NIRBand != '' and self.RedBand != '' and self.outputRaster != '':
                self.argList = [self.RedBand, self.NIRBand, self.outputRaster, self.rasterType, self.addToQGIS]
                self.startWorker('LSTNDVI', self.argList, 'Calculating NDVI')
        elif self.sensorType == 'ASTER':
            #Validate the inputs when the selected sensor is ASTER
            if self.VNIRBand == '':
                iface.messageBar().pushWarning("Land Surface Temperature Plugin","The the visible/near infrared band is required")
            elif self.outputRaster == '':
                iface.messageBar().pushWarning("Land Surface Temperature Plugin","Specify output to be saved")
            #elif self.VNIRBand != '' and self.outputRaster != '':
                #self.argList = [self.VNIRBand, self.outputRaster, self.rasterType, self.addToQGIS]
                #self.startWorker('ASTERNDVI', self.argList, 'Calculating NDVI')

        self.closePlugin()

    def startWorker(self, processName, argList, message):
        self.processName = processName
        self.argList     = argList
        self.message     = message
        worker = EstimateLST(self.processName, self.argList)
        #Configure the QgsMessageBar
        messageBar  = iface.messageBar().createMessage(message)
        progressBar = QtGui.QProgressBar()
        progressBar.setAlignment(QtCore.Qt.AlignVCenter)
        cancelButton = QtGui.QPushButton()
        cancelButton.setText('Cancel')
        cancelButton.clicked.connect(worker.kill)
        messageBar.layout().addWidget(progressBar)
        messageBar.layout().addWidget(cancelButton)
        #iface.messageBar().pushWidget(messageBar, iface.messageBar().INFO)
        iface.messageBar().pushMessage(message)
        self.messageBar = messageBar

        #start the worker in a new thread
        thread = QtCore.QThread()
        worker.moveToThread(thread)
        worker.finished.connect(self.workerFinished)
        worker.error.connect(self.workerError)
        worker.progress.connect(progressBar.setValue)
        thread.started.connect(worker.run)
        thread.start()
        self.thread = thread
        self.worker = worker


    def workerFinished(self, ret):
        #Clean up the worker and thread
        self.worker.deleteLater()
        self.thread.quit()
        self.thread.wait()
        self.thread.deleteLater()

        #Remove widget from messagebar
        iface.messageBar().popWidget()
        if ret is not None:
            #Add the project to the map
            iface.addRasterLayer(ret, self.processName)
        else:
            #Notify the user that an error has occurred
            iface.messageBar().pushMessage("Error","Something went wrong! See the message log for more information")


    def workerError(self, e, exception_string):
        QgsMessageLog.logMessage('Worker thread raised an exception: \n'.format(exception_string), level = QgsMessageLog.CRITICAL)
