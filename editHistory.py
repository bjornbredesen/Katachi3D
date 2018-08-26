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
import struct

# Internal
from extra import *
from project import *
from viewportVoxelmapEditor import *
from viewportVoxelmapOpenGL import *
from layerWindow import *
from propertiesWindow import *
from viewportContainer import *


#####################################################
# Edit history

class EHProject:
	def __init__(self,prj):
		self.prj=prj.clone()
		prj.generated=False
	def use(self,parentwin):
		ret=EHProject(parentwin.prj)
		parentwin.setProject(self.prj)
		return ret

class EHLayer:
	def __init__(self,layer,index):
		self.layer=layer.clone()
		self.li=index
		layer.generated=False
	def use(self,parentwin):
		ret=EHLayer(parentwin.prj.layers[self.li],self.li)
		parentwin.prj.layers[self.li]=self.layer
		parentwin.setLayer(self.li)
		return ret

