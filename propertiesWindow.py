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


#####################################################
# Properties window

renderModeNames=['Hard','VPS','VPS+NC']
#renderModeNames=['Hard','Positional smoothing','Positional smoothing with normal compensation']

class propertiesWindow(wx.Window):
	def __init__(self,mparent,parent,ID):
		self.changeLock=False
		wx.Window.__init__(self,parent,ID,pos=wx.DefaultPosition,size=wx.DefaultSize)
		if wx.Platform == '__WXGTK__':
			self.font = wx.Font(10, wx.MODERN, wx.NORMAL, wx.NORMAL)
		else:
			self.font = wx.Font(8, wx.MODERN, wx.NORMAL, wx.NORMAL)
		self._parent=mparent
		self.prj=mparent.prj
		self.Bind(wx.EVT_SIZE,self.onsize)
		#
		sizer=wx.BoxSizer(wx.VERTICAL)
		self.namer=wx.TextCtrl(self,-1,"")
		self.Bind(wx.EVT_TEXT,self.named,self.namer)

		self.layerSizer=wx.StaticBoxSizer(wx.StaticBox(self,label="Layer"),wx.VERTICAL)
		
		#layerSizer=wx.GridSizer(20, 2, 0, 0)
		layerSizer=wx.FlexGridSizer(20,2,0,0)
		# Name
		layerSizer.AddMany([ (wx.StaticText(self,-1,"Name"),2,wx.GROW|wx.ALIGN_CENTER|wx.LEFT|wx.RIGHT|wx.TOP,6), (self.namer,0,wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL,1) ])
		
		# Position
		box=wx.BoxSizer(wx.HORIZONTAL)
		self.xPoser=wx.SpinCtrl(self,-1,"")
		self.xPoser.SetRange(-1000,1000)
		self.Bind(wx.EVT_SPINCTRL,self.xPos,self.xPoser)
		box.Add(self.xPoser,1,wx.ALIGN_CENTRE|wx.ALL)
		self.yPoser=wx.SpinCtrl(self,-1,"")
		self.yPoser.SetRange(-1000,1000)
		self.Bind(wx.EVT_SPINCTRL,self.yPos,self.yPoser)
		box.Add(self.yPoser,1,wx.ALIGN_CENTRE|wx.ALL)
		self.zPoser=wx.SpinCtrl(self,-1,"")
		self.zPoser.SetRange(-1000,1000)
		self.Bind(wx.EVT_SPINCTRL,self.zPos,self.zPoser)
		box.Add(self.zPoser,1,wx.ALIGN_CENTRE|wx.ALL)
		layerSizer.AddMany([ (wx.StaticText(self,-1,"Position"),0,wx.GROW|wx.ALIGN_CENTER|wx.LEFT|wx.RIGHT|wx.TOP,6), (box,0,wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL,1) ])
		
		# Rendering parameter
		self.renderModeSetter=wx.ComboBox(self,500,"",choices=[],style=wx.CB_DROPDOWN|wx.CB_READONLY)
		v=0
		for i in renderModeNames:
			self.renderModeSetter.Append(i,v)
			v+=1
		self.Bind(wx.EVT_COMBOBOX,self.renderMode,self.renderModeSetter)
		layerSizer.AddMany([ (wx.StaticText(self,-1,"Smoothing"),2,wx.GROW|wx.ALIGN_CENTER|wx.LEFT|wx.RIGHT|wx.TOP,6), (self.renderModeSetter,0,wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL,1) ])

		self.passSetter=wx.SpinCtrl(self,-1,"")
		self.Bind(wx.EVT_SPINCTRL,self.nSmoothPasses,self.passSetter)
		layerSizer.AddMany([ (wx.StaticText(self,-1,"Smoothing passes"),0,wx.GROW|wx.ALIGN_CENTER|wx.LEFT|wx.RIGHT|wx.TOP,6), (self.passSetter,0,wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL,1) ])

		self.radiusSetter=wx.SpinCtrl(self,-1,"")
		self.Bind(wx.EVT_SPINCTRL,self.smoothRadius,self.radiusSetter)
		layerSizer.AddMany([ (wx.StaticText(self,-1,"Smoothing radius"),0,wx.GROW|wx.ALIGN_CENTER|wx.LEFT|wx.RIGHT|wx.TOP,6), (self.radiusSetter,0,wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL,1) ])

		self.ntSetter=wx.SpinCtrl(self,-1,"")
		self.Bind(wx.EVT_SPINCTRL,self.normalTolerance,self.ntSetter)
		layerSizer.AddMany([ (wx.StaticText(self,-1,"Normal tolerance"),0,wx.GROW|wx.ALIGN_CENTER|wx.LEFT|wx.RIGHT|wx.TOP,6), (self.ntSetter,0,wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL,1) ])
		
		self.sssmoother=wx.SpinCtrl(self,-1,"")
		self.Bind(wx.EVT_SPINCTRL,self.sssmooth,self.sssmoother)
		layerSizer.AddMany([ (wx.StaticText(self,-1,"Sub-surface smoothing"),0,wx.GROW|wx.ALIGN_CENTER|wx.LEFT|wx.RIGHT|wx.TOP,6), (self.sssmoother,0,wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL,1) ])
		
		self.materialsetter=wx.SpinCtrl(self,-1,"")
		self.Bind(wx.EVT_SPINCTRL,self.material,self.materialsetter)
		layerSizer.AddMany([ (wx.StaticText(self,-1,"Material"),0,wx.GROW|wx.ALIGN_CENTER|wx.LEFT|wx.RIGHT|wx.TOP,6), (self.materialsetter,0,wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL,1) ])

		self.cbCartoon=wx.CheckBox(self,-1,"")
		self.Bind(wx.EVT_CHECKBOX,self.scbCartoon,self.cbCartoon)
		layerSizer.AddMany([ (wx.StaticText(self,-1,"Outline"),0,wx.GROW|wx.ALIGN_CENTER|wx.LEFT|wx.RIGHT|wx.TOP,6), (self.cbCartoon,0,wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL,1) ])
		layerSizer.AddGrowableCol(1)

		self.layerSizer.Add(layerSizer,1,wx.EXPAND)
		sizer.Add(self.layerSizer,1,wx.EXPAND)


		self.renderSizer=wx.StaticBoxSizer(wx.StaticBox(self,label="Rendering"),wx.VERTICAL)
		renderSizer=wx.FlexGridSizer(2,2,0,0)
		
		self.singleLayer=wx.CheckBox(self,-1,"")
		self.Bind(wx.EVT_CHECKBOX,self.ssingleLayer,self.singleLayer)
		self.singleLayer.SetValue(self._parent.singleLayer)

		self.uselight=wx.CheckBox(self,-1,"")
		self.Bind(wx.EVT_CHECKBOX,self.suselight,self.uselight)
		self.uselight.SetValue(self._parent.useLight)
		
		renderSizer.AddMany([ (wx.StaticText(self,-1,"Draw single layer"),2,wx.GROW|wx.ALIGN_CENTER|wx.LEFT|wx.RIGHT|wx.TOP,6), (self.singleLayer,0,wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL,1), (wx.StaticText(self,-1,"Use light"),2,wx.GROW|wx.ALIGN_CENTER|wx.LEFT|wx.RIGHT|wx.TOP,6), (self.uselight,0,wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL,1) ])
		
		renderSizer.AddGrowableCol(1)
		self.renderSizer.Add(renderSizer,1,wx.EXPAND)
		
		sizer.Add(self.renderSizer,1,wx.EXPAND)
		
		self.brushSizer=wx.StaticBoxSizer(wx.StaticBox(self,label="Brush"),wx.VERTICAL)
		brushSizer=wx.FlexGridSizer(2,2,0,0)
		self.penSizer=wx.SpinCtrl(self,-1,"")
		self.penSizer.SetRange(1,100)
		self.penSizer.SetValue(self._parent.cpenSize)
		self.Bind(wx.EVT_SPINCTRL,self.penSize,self.penSizer)

		brushSizer.AddMany([ (wx.StaticText(self,-1,"Size"),2,wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP,6), (self.penSizer,0,wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL,1) ])
		brushSizer.AddGrowableCol(1)
		self.brushSizer.Add(brushSizer,1,wx.EXPAND)
		sizer.Add(self.brushSizer,1,wx.EXPAND)

		self.Bind(wx.EVT_KEY_DOWN,self.keydown)
		
		self.SetSizer(sizer)
		self.SetAutoLayout(True)
		self.Layout()
	
	def keydown(self,evt):
		kc=evt.GetKeyCode()
		if kc==wx.WXK_LEFT:
			if wx.GetKeyState(wx.WXK_CONTROL):
				self._parent.rightPane.setOpenClient(-1)
				self._parent.control.clients[0].SetFocus()

	def suselight(self,evt):
		self._parent.useLight=evt.IsChecked()
		self._parent.control.RefreshClients()
			
	def ssingleLayer(self,evt):
		self._parent.singleLayer=evt.IsChecked()
		self._parent.control.RefreshClients()

	def smoothRadius(self,evt):
		if not self.changeLock:
			self._parent.EHCandidateActiveLayer() # XXX TEMPORARY! Replace with simpler layer parameter operation
			self.prj.layers[self.prj.activeLayer].smoothRadius=self.radiusSetter.GetValue()
			self._parent.EHAddCandidate()
	def nSmoothPasses(self,evt):
		if not self.changeLock:
			self._parent.EHCandidateActiveLayer() # XXX TEMPORARY! Replace with simpler layer parameter operation
			self.prj.layers[self.prj.activeLayer].smoothPasses=self.passSetter.GetValue()
			self._parent.EHAddCandidate()
		
	def penSize(self,evt):
		self._parent.cpenSize=self.penSizer.GetValue()
		
	def renderMode(self,evt):
		if not self.changeLock:
			self._parent.EHCandidateActiveLayer() # XXX TEMPORARY! Replace with simpler layer parameter operation
			self.prj.layers[self.prj.activeLayer].renderMode=renderModeNames.index(evt.GetString())
			self._parent.EHAddCandidate()
		
	def normalTolerance(self,evt):
		if not self.changeLock:
			self._parent.EHCandidateActiveLayer() # XXX TEMPORARY! Replace with simpler layer parameter operation
			self.prj.layers[self.prj.activeLayer].normalTolerance=self.ntSetter.GetValue()
			self._parent.EHAddCandidate()
		
	def scbCartoon(self,evt):
		if not self.changeLock:
			self._parent.EHCandidateActiveLayer() # XXX TEMPORARY! Replace with simpler layer parameter operation
			self.prj.layers[self.prj.activeLayer].cartoon=evt.IsChecked()
			self._parent.EHAddCandidate()

	def material(self,evt):
		if not self.changeLock:
			self._parent.EHCandidateActiveLayer() # XXX TEMPORARY! Replace with simpler layer parameter operation
			self._parent.EHAddCandidate()
			self.prj.layers[self.prj.activeLayer].material=self.materialsetter.GetValue()

	def sssmooth(self,evt):
		if not self.changeLock:
			self._parent.EHCandidateActiveLayer() # XXX TEMPORARY! Replace with simpler layer parameter operation
			self.prj.layers[self.prj.activeLayer].nSubSurface=self.sssmoother.GetValue()
			self._parent.EHAddCandidate()

	def xPos(self,evt):
		if not self.changeLock:
			self._parent.EHCandidateActiveLayer() # XXX TEMPORARY! Replace with simpler layer parameter operation
			self.prj.layers[self.prj.activeLayer].xPos=self.xPoser.GetValue()
			self._parent.EHAddCandidate()
	def yPos(self,evt):
		if not self.changeLock:
			self._parent.EHCandidateActiveLayer() # XXX TEMPORARY! Replace with simpler layer parameter operation
			self.prj.layers[self.prj.activeLayer].yPos=self.yPoser.GetValue()
			self._parent.EHAddCandidate()
	def zPos(self,evt):
		if not self.changeLock:
			self._parent.EHCandidateActiveLayer() # XXX TEMPORARY! Replace with simpler layer parameter operation
			self.prj.layers[self.prj.activeLayer].zPos=self.zPoser.GetValue()
			self._parent.EHAddCandidate()
	
	def named(self,evt):
		if not self.changeLock:
			self._parent.EHCandidateActiveLayer() # XXX TEMPORARY! Replace with simpler renaming operation
			name=evt.GetString()
			self.prj.layers[self.prj.activeLayer].name=evt.GetString()
			self._parent.EHAddCandidate()
	
	def onsize(self,evt):
		if self.GetAutoLayout():
			self.Layout()

	def setProject(self,prj):
		self.prj=prj
		self.setLayer(prj.activeLayer)
		
	def setLayer(self,layer):
		if layer<0 or layer>=len(self.prj.layers):
			print("Invalid layer")
			return
		self.changeLock=True
		self.namer.SetValue(self.prj.layers[layer].name)
		self.xPoser.SetValue(self.prj.layers[layer].xPos)
		self.yPoser.SetValue(self.prj.layers[layer].yPos)
		self.zPoser.SetValue(self.prj.layers[layer].zPos)
		self.sssmoother.SetValue(self.prj.layers[layer].nSubSurface)
		self.materialsetter.SetValue(self.prj.layers[layer].material)
		self.ntSetter.SetValue(self.prj.layers[layer].normalTolerance)
		self.cbCartoon.SetValue(self.prj.layers[layer].cartoon)
		self.renderModeSetter.SetValue(renderModeNames[self.prj.layers[layer].renderMode])
		self.changeLock=False
		self.radiusSetter.SetValue(self.prj.layers[self.prj.activeLayer].smoothRadius)
		self.passSetter.SetValue(self.prj.layers[self.prj.activeLayer].smoothPasses)

