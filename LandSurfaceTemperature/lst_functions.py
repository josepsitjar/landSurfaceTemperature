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

from qgis.PyQt import QtCore, QtGui
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction

import numpy as np
from osgeo import gdal
from osgeo import ogr
import os, sys, struct

#from .land_temperature_dialog import LandTemperatureDialog as lst_dialog

class EstimateLST(QtCore.QObject):
    def __init__(self, geoProcessName, *args):
        QtCore.QObject.__init__(self)
        self.geoProcessName = geoProcessName
        self.args   = args[0]
        self.abort  = False
        self.killed = False


    def calcNDVI(self, redBandPath, NIRBandPath, outputPath, rasterType, addToQGIS):
        try:
            #The code below opens the datasets
            dsRedBand = gdal.Open(redBandPath, gdal.GA_ReadOnly)
            dsNIRBand = gdal.Open(NIRBandPath, gdal.GA_ReadOnly)
            self.progress.emit(20)
        except IOError as e:
            self.error.emit(e, traceback.format_exc())
        try:
            #Capture the Red and the NIR bands
            redBand = dsRedBand.GetRasterBand(1)
            NIRBand = dsNIRBand.GetRasterBand(1)

            # get numbers of rows and columns in the Red and NIR bands
            colsRed = dsRedBand.RasterXSize
            rowsRed = dsRedBand.RasterYSize

            # create the output image
            driver = gdal.GetDriverByName(rasterType)
            ndviDS = driver.Create(outputPath, colsRed, rowsRed, 1, gdal.GDT_Float32)
            ndviDS.SetGeoTransform(dsRedBand.GetGeoTransform())
            ndviDS.SetProjection(dsRedBand.GetProjection())
            ndviBand = ndviDS.GetRasterBand(1)
            self.progress.emit(40)

            # loop through rows of blocks
            blockSize = 64
            for i in range(0, rowsRed, blockSize):
                if i + blockSize < rowsRed:
                    numRows = blockSize
                else:
                    numRows = rowsRed - i

                # now loop through the blocks in the row
                for j in range(0, colsRed, blockSize):
                    if j + blockSize < colsRed:
                        numCols = blockSize
                    else:
                        numCols = colsRed - j
                    # get the data
                    redBandData = redBand.ReadAsArray(j, i, numCols, numRows).astype('f')
                    NIRBandData = NIRBand.ReadAsArray(j, i, numCols, numRows).astype('f')
                    # do the calculation
                    mask = np.greater(redBandData + NIRBandData, 0)
                    ndvi = np.choose(mask, (-99, (NIRBandData - redBandData) / (NIRBandData + redBandData)))
                    # write the data
                    ndviDS.GetRasterBand(1).WriteArray(ndvi, j, i)

            self.progress.emit(90)
            # set the histogram
            ndviDS.GetRasterBand(1).SetNoDataValue(-99)
            histogram = ndviDS.GetRasterBand(1).GetDefaultHistogram()
            ndviDS.GetRasterBand(1).SetDefaultHistogram(histogram[0], histogram[1], histogram[3])

            ndviDS   = None
            redBand  = None
            NIRBand  = None

            #Add the output to QGIS
            ret = outputPath
            if (addToQGIS == 'Yes'):
                self.progress.emit(100)
                self.finished.emit(ret)
            else:
                ret = None
                self.progress.emit(100)
                self.finished.emit(ret)

        except RuntimeError as e:
            self.error.emit(e, traceback.format_exc())

    def kill(self):
        self.killed = True

    def run(self):
        if (self.geoProcessName == 'LSTNDVI'):
            #Capture the varibles needed for NDVI calculation
            self.RedBand      = self.args[0]
            self.NIRBand      = self.args[1]
            self.outputRaster = self.args[2]
            self.rasterType   = self.args[3]
            self.addToQGIS    = self.args[4]
            self.calcNDVI(self.RedBand, self.NIRBand, self.outputRaster, self.rasterType, self.addToQGIS)


    finished = QtCore.pyqtSignal(object)
    error    = QtCore.pyqtSignal(Exception, str)
    progress = QtCore.pyqtSignal(int)
