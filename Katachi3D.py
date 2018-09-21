#!/usr/bin/python -O
# -*- coding: UTF-8 -*-
#####################################################
# Katachi3D
# Copyright Bjørn André Bredesen, 2013
# E-mail: contact@bjornbredesen.no
#####################################################
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#####################################################
# Katachi3D is a simple voxel graphics editor.

# Dependencies
from __future__ import division
import wx
import os
from wx import glcanvas
from OpenGL.GL import *

# Internal
from Katachi3Dlib import *
from project import *
from extra import *
from viewportVoxelmapEditor import *
from viewportVoxelmapOpenGL import *
from viewportContainer import *
from layerWindow import *
from propertiesWindow import *
from mainWindow import *


#####################################################
# Entry

print("------------------------------------------------------")
print("\tKatachi3D")
print("\tBy Bjørn Bredesen, 2013")
print("\tE-mail: contact@bjornbredesen.no")
print("------------------------------------------------------")
print("Please see 'About' for instructions.")
print("------------------------------------------------------")

project=voxelImage(20,32,20)
project.newLayer("Layer 1")

app=wx.App(False)
frame=mainFrame(project)
app.MainLoop()

