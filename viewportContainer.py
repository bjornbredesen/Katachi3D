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
# Multi-viewport editor

class viewportContainer(wx.Window):
	def __init__(self,mparent,parent,ID,prj,_zoom=8):
		wx.Window.__init__(self,parent,ID,pos=wx.DefaultPosition,size=wx.DefaultSize,style=wx.TRANSPARENT_WINDOW)
		#
		self.cX=0
		self.cY=0
		self.cZ=0
		self.caxis=None
		#
		self._parent=mparent
		self.clients=[]
		self.maximized=-1
		self.clients.append(viewportVoxelmapEditor(self,-1,prj,axis=0,zoom=_zoom))
		self.clients.append(viewportVoxelmapEditor(self,-1,prj,axis=1,zoom=_zoom))
		self.clients.append(viewportVoxelmapEditor(self,-1,prj,axis=2,zoom=_zoom))
		self.clients.append(viewportVoxelmapOpenGL(self,-1,prj,zoom=_zoom))
		#
		self.sxA=-1
		self.syA=-1
		self.szA=-1
		self.sxB=-1
		self.syB=-1
		self.szB=-1
		self.selRect=False
		self.prj=prj
		self.activeLayer=0
		self.xSize=0
		self.ySize=0
		#
		self.Bind(wx.EVT_SIZE,self.resize)
		self.clients[0].SetFocus()
		self.RefreshClients()

	def childKeyDown(self,evt):
		kc=evt.GetKeyCode()
		if kc==wx.WXK_TAB:
			if self.maximized!=-1:
				if wx.GetKeyState(wx.WXK_SHIFT):
					self.maximized=self.maximized-1
					if self.maximized<0:
						self.maximized=len(self.clients)-1
				else:
					self.maximized=(self.maximized+1)%len(self.clients)
				i=0
				for x in self.clients:
					x.Show(i==self.maximized)
					i+=1
				self.sizeupd()
				self.clients[self.maximized].SetFocus()
			else:
				i=0
				for x in self.clients:
					if x!=0 and x._focus:
						break
					i+=1
				if wx.GetKeyState(wx.WXK_SHIFT):
					self.clients[i-1].SetFocus()
					return True
				else:
					self.clients[(i+1)%len(self.clients)].SetFocus()
					return True
		elif kc==wx.WXK_LEFT:
			if wx.GetKeyState(wx.WXK_CONTROL):
				pane=self._parent.leftPane.setOpenClient(0)
				return True
		elif kc==wx.WXK_RIGHT:
			if wx.GetKeyState(wx.WXK_CONTROL):
				pane=self._parent.rightPane.setOpenClient(0)
				return True
		elif kc==wx.WXK_DOWN:
			if wx.GetKeyState(wx.WXK_CONTROL):
				pane=self._parent.bottomPane.setOpenClient(0)
				return True
		elif kc>=ord('1') and kc<=ord('7'):
			self._parent.tool=kc-ord('1')
			self._parent.toolbar.ToggleTool(20+self._parent.tool,True)
			return True
		elif kc==ord('C'):
			cold=wx.ColourData()
			cold.SetColour(self._parent.penColour)
			colc=wx.ColourDialog(self._parent,cold)
			if colc.ShowModal()==wx.ID_OK:
				self.setColour(colc.GetColourData().GetColour())
			colc.Destroy()
			return True
		elif kc==ord('Q'):
			self._parent.cpenSize+=1
			self._parent.propertieswin.penSizer.SetValue(self._parent.cpenSize)
		elif kc==ord('A'):
			self._parent.cpenSize-=1
			if  self._parent.cpenSize<1:
				self._parent.cpenSize=1
			self._parent.propertieswin.penSizer.SetValue(self._parent.cpenSize)
		elif kc==ord('X'):
			if self.maximized==-1:
				i=0
				for x in self.clients:
					if x!=0 and x._focus:
						self.maximized=i
					else:
						x.Show(False)
					i+=1
			else:
				for x in self.clients:
					x.Show(True)
				self.maximized=-1
			self.sizeupd()
		return False
	
	def GenerateClients(self):
		for x in self.clients:
			if x!=0:
				x.generate()
	
	def emptySelection(self):
		if self.prj.clipboard:
			self.prj.clipboard=None
			self.RefreshClients()
			return
		mask=self.prj.selMask
		if mask.empty:
			return
		self._parent.EHCandidateActiveLayer()
		layer=self.prj.layers[self.activeLayer]
		vMap=layer.vMap
		xS=self.prj.xSize
		zS=self.prj.zSize
		yS=self.prj.ySize
		lxS=layer.vMap.xSize
		lzS=layer.vMap.zSize
		lyS=layer.vMap.ySize
		lxP=layer.xPos
		lyP=layer.yPos
		lzP=layer.zPos
		xMin=max(0,-lxP)
		xMax=lxS-max(((lxP+lxS)-xS),0)
		yMin=max(0,-lyP)
		yMax=lyS-max(((lyP+lyS)-yS),0)
		zMin=max(0,-lzP)
		zMax=lzS-max(((lzP+lzS)-zS),0)
		for z in range(zMin,zMax):
			for y in range(yMin,yMax):
				for x in range(xMin,xMax):
					if mask.getPx([x+layer.xPos,y+layer.yPos,z+layer.zPos]):
						vMap.setPx([x,y,z],[0,0,0,0])
		self._parent.EHAddCandidate()
		
	def selectAll(self):
		b=self.prj.selMask.vMap
		xs=self.prj.selMask.xSize
		ys=self.prj.selMask.ySize
		zs=self.prj.selMask.zSize
		for x in range(xs):
			for y in range(ys):
				for z in range(zs):
					b[z*ys*xs+y*xs+x]=255
		self.prj.selMask.empty=False
		self.selRect=False
		self.RefreshClients()
	
	def clearSelection(self):
		self.prj.selMask.clear()
	def addSelectionRectangle(self):
		if self.sxA==self.sxB or self.syA==self.syB or self.szA==self.szB:
			self.selRect=False
			self.RefreshClients()
			return
		b=self.prj.selMask.vMap
		xs=self.prj.selMask.xSize
		ys=self.prj.selMask.ySize
		for x in range(self.sxA,self.sxB):
			for y in range(self.syA,self.syB):
				for z in range(self.szA,self.szB):
					b[z*ys*xs+y*xs+x]=255
		self.prj.selMask.empty=False
		self.selRect=False
		self.RefreshClients()
	def setSelectionRectangle(self,xA,yA,zA,xB,yB,zB):
		layer=self.prj.layers[self.activeLayer]
		vMap=layer.vMap
		self.sxA=max(min(max(min(min(xA,xB),vMap.xSize),0)+layer.xPos,self.prj.xSize),0)
		self.sxB=max(min(max(min(max(xA,xB),vMap.xSize),0)+layer.xPos,self.prj.xSize),0)
		self.syA=max(min(max(min(min(yA,yB),vMap.ySize),0)+layer.yPos,self.prj.ySize),0)
		self.syB=max(min(max(min(max(yA,yB),vMap.ySize),0)+layer.yPos,self.prj.ySize),0)
		self.szA=max(min(max(min(min(zA,zB),vMap.zSize),0)+layer.zPos,self.prj.zSize),0)
		self.szB=max(min(max(min(max(zA,zB),vMap.zSize),0)+layer.zPos,self.prj.zSize),0)
		if self.sxA!=self.sxB and self.syA!=self.syB and self.szA!=self.szB:
			self.selRect=True
		else:
			self.selRect=False
		self.RefreshClientsActive()
	
	def setProject(self,prj):
		self.prj=prj
		for x in self.clients:
			if x!=0:
				x.setProject(prj)
		self.setLayer(prj.activeLayer)
		
	def setLayer(self,layer):
		self.activeLayer=layer
		for x in self.clients:
			if x!=0:
				x.setLayer(layer)
	
	def RefreshClientsActive(self):
		for x in self.clients:
			if x!=0:
				x.RefreshActive()
	
	def setColour(self,col):
		self._parent.setColour(col)
	
	def RefreshClients(self):
		for x in self.clients:
			if x!=0:
				x.Refresh()
	
	def sizeupd(self):
		xs=self.xSize
		ys=self.ySize
		if self.maximized!=-1:
			self.clients[self.maximized].SetRect(wx.Rect(0,0,xs,ys))
		else:
			if self.clients[0]:
				self.clients[0].SetRect(wx.Rect(0,0,xs/2,ys/2))
			if self.clients[1]:
				self.clients[1].SetRect(wx.Rect(xs/2+1,0,xs/2,ys/2))
			if self.clients[2]:
				self.clients[2].SetRect(wx.Rect(0,ys/2+1,xs/2,ys/2))
			if self.clients[3]:
				self.clients[3].SetRect(wx.Rect(xs/2+1,ys/2+1,xs/2,ys/2))
		
	def resize(self,evt):
		size=evt.GetSize()
		self.xSize=size.x
		self.ySize=size.y
		self.sizeupd()
	
	def cleanup(self,evt):
		pass

