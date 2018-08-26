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

from __future__ import division
import wx
import array
import os
import wx.lib.colourselect as csel
import wx.py as py
import struct
#from wx import glcanvas
#from OpenGL.GL import *

from wx import glcanvas
from wx.glcanvas import WX_GL_DEPTH_SIZE
import OpenGL.platform.glx
import OpenGL.GL
#import OpenGL.GLU
import OpenGL.GLUT
#from OpenGL.GL import *
import OpenGL.arrays.ctypesarrays
import OpenGL.arrays.ctypesparameters
import OpenGL.arrays.ctypespointers
import OpenGL.arrays.lists
import OpenGL.arrays.nones
import OpenGL.arrays.numbers
import OpenGL.arrays.strings
import OpenGL.raw.GL
import OpenGL.GL
#import OpenGL.GLU
import OpenGL.GLUT
from OpenGL.GL import *
from OpenGL.GLUT import *
#from OpenGL.GLU import *

import time

from Katachi3Dlib import *


#####################################################
# Extra

#bgDC=0
#bgBitmap=0
def makeBGBitmap(basedc):
	w=8
	h=8
	bgBytes=array.array('B',[0]*w*h*3)
	for y in range(h):
		for x in range(w):
			offset=y*w*3+x*3
			g=100
			if (int(x/4)&1) ^ (int(y/4)&1):
				g=150
			bgBytes[offset+0]=bgBytes[offset+1]=bgBytes[offset+2]=g
	dw=1600
	dh=1200
	bgBitmap=wx.Bitmap.FromBuffer(w,h,bgBytes)
	bgDC=wx.MemoryDC(wx.Bitmap(dw, dh, 24))
	bgDC.Clear()
	for y in range(int(dh/h)):
		for x in range(int(dw/w)):
			bgDC.DrawBitmap(bgBitmap,x*w,y*h)
	return bgDC

def DrawTextActive(dc,tname,x,y):
	dc.SetTextForeground(wx.Colour(0,0,0,wx.ALPHA_OPAQUE))
	for sx in range (-1,3):
		for sy in range (-1,2):
			dc.DrawText(tname,x+sx,y+sy)
	dc.SetTextForeground(wx.Colour(255,255,255,wx.ALPHA_OPAQUE))
	dc.DrawText(tname,x,y)
	dc.DrawText(tname,x+1,y)



