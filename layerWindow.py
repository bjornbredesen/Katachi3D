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
# Drawing functions

def iso2screen(x,y,z):
	return [(x-z)*2,(x+z+y*2.5)]

def isoscale(vec,x,y,zoom):
	return [vec[0]*zoom+x,vec[1]*zoom+y]

def drawIsometric(vMap,dc,x,y,w,h,zoom,drawX,drawY,drawZ):
	xS=vMap.xSize
	yS=vMap.ySize
	zS=vMap.zSize
	pA=iso2screen(0,0,0)
	pB=iso2screen(xS,yS,zS)
	pC1=iso2screen(xS,0,0)
	pC2=iso2screen(0,0,zS)
	# If no zooming specified, fit it based on specified width and height
	if zoom==0:
		minX=pC1[0]
		maxX=pC2[0]
		minY=pA[1]
		maxY=pB[1]
		zoom = min(w,h)/max(maxX-minX,maxY-minY)
	xC=x+(w-(pC2[0]+pC1[0])*zoom)/2
	yC=y+(h-(pB[1]+pA[1])*zoom)/2
	pD1=iso2screen(xS,yS,0)
	pD2=iso2screen(0,yS,zS)
	pE=iso2screen(0,yS,0)
	dc.SetPen(wx.Pen(wx.Colour('medium grey'),1))
	dc.SetBrush(wx.TRANSPARENT_BRUSH)
#	dc.DrawRectangle( x,y,w,h )
	# Draw base
	dc.DrawLine(pA[0]*zoom+xC,pA[1]*zoom+yC,pC1[0]*zoom+xC,pC1[1]*zoom+yC)
	dc.DrawLine(pC1[0]*zoom+xC,pC1[1]*zoom+yC,pD1[0]*zoom+xC,pD1[1]*zoom+yC)
	dc.DrawLine(pA[0]*zoom+xC,pA[1]*zoom+yC,pC2[0]*zoom+xC,pC2[1]*zoom+yC)
	dc.DrawLine(pC2[0]*zoom+xC,pC2[1]*zoom+yC,pD2[0]*zoom+xC,pD2[1]*zoom+yC)
	dc.DrawLine(pA[0]*zoom+xC,pA[1]*zoom+yC,pE[0]*zoom+xC,pE[1]*zoom+yC)
	dc.DrawLine(pE[0]*zoom+xC,pE[1]*zoom+yC,pD1[0]*zoom+xC,pD1[1]*zoom+yC)
	dc.DrawLine(pE[0]*zoom+xC,pE[1]*zoom+yC,pD2[0]*zoom+xC,pD2[1]*zoom+yC)
	dc.DrawLine(pD1[0]*zoom+xC,pD1[1]*zoom+yC,pB[0]*zoom+xC,pB[1]*zoom+yC)
	dc.DrawLine(pD2[0]*zoom+xC,pD2[1]*zoom+yC,pB[0]*zoom+xC,pB[1]*zoom+yC)
	if not (drawX or drawY or drawZ):
		return
	# Draw isometric
	buf=vMap.vMap
	for z in range(zS):
		for _y in range(yS):
			y=yS-_y-1
			for x in range(xS):
				offs=(z*yS*xS+y*xS+x)*4
				if buf[offs+3]!=0:
					offs2=(z*yS*xS+y*xS+x+1)*4
					dx=x==xS-1 or buf[offs2+3]==0
					offs3=(z*yS*xS+(y-1)*xS+x)*4
					dy=y==0 or buf[offs3+3]==0
					offs4=((z+1)*yS*xS+y*xS+x)*4
					dz=z==zS-1 or buf[offs4+3]==0
					if not (dx or dy or dz):
						continue
					r=buf[offs]
					g=buf[offs+1]
					b=buf[offs+2]
					sy = y*2.5
					sy2 = (y+1)*2.5
					p1 = [(x+1-z)*2*zoom+xC,(x+1+z+sy)*zoom+yC]
					p2 = [(x+1-z-1)*2*zoom+xC,(x+1+z+1+sy)*zoom+yC]
					p3 = [(x+1-z-1)*2*zoom+xC,(x+1+z+1+sy2)*zoom+yC]
					p4 = [(x+1-z)*2*zoom+xC,(x+1+z+sy2)*zoom+yC]
					p5 = [(x-z-1)*2*zoom+xC,(x+z+1+sy)*zoom+yC]
					if dx:
						colL=[ min(r*1.1+20,255),min(g*1.1+20,255),min(b*1.1+20,255) ]
						dc.SetPen(wx.Pen(wx.Colour( colL[0],colL[1],colL[2] ),1))
						dc.SetBrush(wx.Brush(wx.Colour( colL[0],colL[1],colL[2] )))
						dc.DrawPolygon([ [p1[0],p1[1]], [p2[0],p2[1]], [p3[0],p3[1]], [p4[0],p4[1]] ])
					if dy:
						p7 = [(x-z)*2*zoom+xC,(x+z+sy)*zoom+yC]
						dc.SetPen(wx.Pen(wx.Colour( r,g,b ),1))
						dc.SetBrush(wx.Brush(wx.Colour( r,g,b )))
						dc.DrawPolygon([ [p1[0],p1[1]], [p7[0],p7[1]], [p5[0],p5[1]], [p2[0],p2[1]] ])
					if dz:
						colD=[ max(r*0.9-20,0),max(g*0.9-20,0),max(b*0.9-20,0) ]
						p6 = [(x-z-1)*2*zoom+xC,(x+z+1+sy2)*zoom+yC]
						dc.SetPen(wx.Pen(wx.Colour( colD[0],colD[1],colD[2] ),1))
						dc.SetBrush(wx.Brush(wx.Colour( colD[0],colD[1],colD[2] )))
						dc.DrawPolygon([ [p2[0],p2[1]], [p5[0],p5[1]], [p6[0],p6[1]], [p3[0],p3[1]] ])
	#
#####################################################
# Layer window

layerHeight = 64

class layerWindow(wx.Window):
	def __init__(self,mparent,parent,ID,prj):
		wx.Window.__init__(self,parent,ID,pos=wx.DefaultPosition,size=wx.DefaultSize)
		if wx.Platform == '__WXGTK__':
			self.font = wx.Font(10, wx.MODERN, wx.NORMAL, wx.NORMAL)
		else:
			self.font = wx.Font(8, wx.MODERN, wx.NORMAL, wx.NORMAL)
		#
		self._parent=mparent
		self.xSize=0
		self.ySize=0
		self.prj=prj
		#
		self.Bind(wx.EVT_SIZE,self.resize)
		self.Bind(wx.EVT_PAINT,self.repaint)
		self.Bind(wx.EVT_LEFT_DOWN,self.leftclick)
		self.Bind(wx.EVT_RIGHT_UP,self.rightunclick)
		self.Bind(wx.EVT_KEY_DOWN,self.keydown)
	
	def setProject(self,prj):
		self.prj=prj
		self.setLayer(prj.activeLayer)
	
	def setLayer(self,layer):
		if layer<0 or layer>=len(self.prj.layers):
			print("Invalid layer")
			return

	def rightunclick(self,evt):
		pos=evt.GetPosition()
		pi=self.prj.activeLayer
		i=0
		for l in self.prj.layers:
			r = self.layerRect(i)
			if pos.x>=r[0] and pos.x<r[0]+r[2] and pos.y>=r[1] and pos.y<r[1]+r[3]:
				if i!=pi:
					self._parent.setLayer(i)
					self._parent.GenerateClients()
				mnu=wx.Menu()
				ne=False
				if i>0:
					mnu.Append(0,"Move &up")
					self.Bind(wx.EVT_MENU,self.moveUp,id=0)
					ne=True
				if i<len(self.prj.layers)-1:
					mnu.Append(1,"Move &down")
					self.Bind(wx.EVT_MENU,self.moveDown,id=1)
					ne=True
				if ne:
					mnu.AppendSeparator()
				if len(self.prj.layers)>1:
					mnu.Append(2,"&Remove")
					self.Bind(wx.EVT_MENU,self.removeLayer,id=2)
					ne=True
				if ne:
					self.PopupMenu(mnu,pos)
				mnu.Destroy()
				return
			i+=1

	def moveUp(self,evt):
		if self.prj.activeLayer<=0:
			print("Can't move layer further up.")
			return
		_q=self.prj.layers[self.prj.activeLayer-1]
		_c=self.prj.layers[self.prj.activeLayer]
		a=[]
		b=[]
		if self.prj.activeLayer>1:
			a=self.prj.layers[:self.prj.activeLayer-1]
		if self.prj.activeLayer<len(self.prj.layers)-1:
			b=self.prj.layers[self.prj.activeLayer+1:]
		self._parent.EHCandidateProject() # XXX TEMPORARY! Replace with simpler moving history
		self.prj.layers=a+[_c]+[_q]+b
		self._parent.setLayer(self.prj.activeLayer-1)
		self._parent.EHAddCandidate()
	def moveDown(self,evt):
		if self.prj.activeLayer>=len(self.prj.layers)-1:
			print("Can't move layer further down.")
			return
		_c=self.prj.layers[self.prj.activeLayer]
		_q=self.prj.layers[self.prj.activeLayer+1]
		a=[]
		b=[]
		if self.prj.activeLayer>0:
			a=self.prj.layers[:self.prj.activeLayer]
		if self.prj.activeLayer<len(self.prj.layers)-2:
			b=self.prj.layers[self.prj.activeLayer+2:]
		self._parent.EHCandidateProject() # XXX TEMPORARY! Replace with simpler moving history
		self.prj.layers=a+[_q]+[_c]+b
		self._parent.setLayer(self.prj.activeLayer+1)
		self._parent.EHAddCandidate()
	def removeLayer(self,evt):
		if len(self.prj.layers)<=1:
			print("Can't remove bottom layer.")
			return
		a=[]
		b=[]
		if self.prj.activeLayer>0:
			a=self.prj.layers[:self.prj.activeLayer]
		if self.prj.activeLayer<len(self.prj.layers)-1:
			b=self.prj.layers[self.prj.activeLayer+1:]
		self._parent.EHCandidateProject() # XXX TEMPORARY! Replace with simpler re-insertion operation
		self.prj.layers=a+b
		if self.prj.activeLayer>=len(self.prj.layers):
			self.prj.activeLayer-=1
		self._parent.setLayer(self.prj.activeLayer)
		self._parent.EHAddCandidate()
	
	def leftclick(self,evt):
		self.SetFocus()
		pos=evt.GetPosition()
		pi=self.prj.activeLayer
		i=0
		for l in self.prj.layers:
			r = self.layerRect(i)
			if pos.x>=r[0] and pos.x<r[0]+r[2] and pos.y>=r[1] and pos.y<r[1]+r[3]:
				if i!=pi:
					self._parent.setLayer(i)
					self._parent.GenerateClients()
				return
			i+=1
		
	def keydown(self,evt):
		kc=evt.GetKeyCode()
		if kc==wx.WXK_DOWN:
			if wx.GetKeyState(wx.WXK_CONTROL):
				self.moveDown(None)
			else:
				if self.prj.activeLayer<len(self.prj.layers)-1:
					self._parent.setLayer(self.prj.activeLayer+1)
					self._parent.GenerateClients()
		elif kc==wx.WXK_UP:
			if wx.GetKeyState(wx.WXK_CONTROL):
				self.moveUp(None)
			else:
				if self.prj.activeLayer>0:
					self._parent.setLayer(self.prj.activeLayer-1)
					self._parent.GenerateClients()
		elif kc==wx.WXK_DELETE:
			self.removeLayer(None)
		elif kc==wx.WXK_RIGHT:
			if wx.GetKeyState(wx.WXK_CONTROL):
				self._parent.leftPane.setOpenClient(-1)
				self._parent.control.clients[0].SetFocus()
	
	def resize(self,evt):
		size=evt.GetSize()
		self.xSize=size.x
		self.ySize=size.y
		self.Refresh(eraseBackground=False)
		self.draw()

	def repaint(self,evt):
		try:
			self.draw(wx.BufferedPaintDC(self))
		except wx._core.wxAssertionError as e:
			print('Exception: ' + str(e))
	
	def layerRect(self,ind):
		return [ 0,layerHeight*ind,self.xSize,layerHeight ]
	
	def draw(self,dc=None):
		if not dc:
			try:
				dc = wx.BufferedPaintDC(self)
			except wx._core.wxAssertionError as e:
				#print('Exception: ' + str(e))
				return
		#
		c=wx.SystemSettings.GetColour(wx.SYS_COLOUR_MENU)
		dc.SetPen(wx.Pen(c,1))
		dc.SetBrush(wx.Brush(c))
		dc.DrawRectangle(0,0,self.xSize,self.ySize)
		#
		dc.SetFont(self.font)
		i=0
		for l in self.prj.layers:
			r = self.layerRect(i)
			if i==self.prj.activeLayer:
				dc.SetPen(wx.Pen(wx.Colour('white'),1,wx.DOT))
				dc.SetBrush(wx.TRANSPARENT_BRUSH)
				dc.DrawRectangle(r[0],r[1],r[2],r[3])
				DrawTextActive(dc,l.name,r[0]+layerHeight+8,r[1]-9+layerHeight/2)
			else:
				dc.SetTextForeground(wx.Colour(0,0,0,wx.ALPHA_OPAQUE))
				dc.DrawText(l.name,r[0]+layerHeight+8,r[1]-9+layerHeight/2)
			drawIsometric(l.vMap,dc,r[0]+2,r[1]+2,layerHeight-4,layerHeight-4,0,True,True,True)
			i+=1
	
	def cleanup(self,evt):
		pass

