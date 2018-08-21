#!/usr/bin/python -O
# -*- coding: latin-1 -*-
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
from wx import glcanvas
from OpenGL.GL import *
import time

from Katachi3Dlib import *


#####################################################
# Global

bgDC=0
bgBitmap=0
def makeBGBitmap(basedc):
	w=8
	h=8
	bgBytes=array.array('B',[0]*w*h*3)
	for y in xrange(h):
		for x in xrange(w):
			offset=y*w*3+x*3
			g=100
			if (int(x/4)&1) ^ (int(y/4)&1):
				g=150
			bgBytes[offset+0]=bgBytes[offset+1]=bgBytes[offset+2]=g
	global bgBitmap
	global bgDC
	dw=1600
	dh=1200
	bgBitmap=wx.BitmapFromBuffer(w,h,bgBytes)
	bgDC=wx.MemoryDC(wx.EmptyBitmap(dw,dh))
	bgDC.Clear()
	for y in xrange(int(dh/h)):
		for x in xrange(int(dw/w)):
			bgDC.DrawBitmap(bgBitmap,x*w,y*h)

def DrawTextActive(dc,tname,x,y):
	dc.SetTextForeground(wx.Colour(0,0,0,wx.ALPHA_OPAQUE))
	for sx in range (-1,3):
		for sy in range (-1,2):
			dc.DrawText(tname,x+sx,y+sy)
	dc.SetTextForeground(wx.Colour(255,255,255,wx.ALPHA_OPAQUE))
	dc.DrawText(tname,x,y)
	dc.DrawText(tname,x+1,y)


#####################################################
# Voxel map

class voxelmask():
	def __init__(self,xSize,ySize,zSize):
		self.xSize=xSize
		self.ySize=ySize
		self.zSize=zSize
		self.vMap=array.array('B',[0]*xSize*ySize*zSize)
		self.clear()
	def clear(self):
		for i in xrange(self.xSize*self.ySize*self.zSize):
			self.vMap[i]=0
		self.empty=True
	def setPx(self,pos,col):
		if len(pos)!=3:
			print "Illegal voxelmask drawing parameters"
			return
		x=pos[0]
		y=pos[1]
		z=pos[2]
		if x<0 or x>=self.xSize or y<0 or y>=self.ySize or z<0 or z>=self.zSize:
			print "Illegal voxelmap point"
			return
		self.vMap[z*self.ySize*self.xSize+y*self.xSize+x]=col
		self.empty=False
	def getPx(self,pos):
		if self.empty:
			return 0
		if len(pos)!=3:
			print "Illegal voxelmap coordinates"
			return []
		x=pos[0]
		y=pos[1]
		z=pos[2]
		if x<0 or x>=self.xSize or y<0 or y>=self.ySize or z<0 or z>=self.zSize:
			print "Illegal voxelmap point"
			return
		return self.vMap[z*self.ySize*self.xSize+y*self.xSize+x]
	def dbgout(self):
		print "voxelmask:"
		print "\txSize=",self.xSize
		print "\tySize=",self.ySize
		print "\tzSize=",self.zSize

class voxelmap():
	def __init__(self,xSize,ySize,zSize):
		self.xSize=xSize
		self.ySize=ySize
		self.zSize=zSize
		self.vMap=array.array('B',[0]*xSize*ySize*zSize*4)
		self.clear()
	def clear(self):
		for i in xrange(self.xSize*self.ySize*self.zSize*4):
			self.vMap[i]=0
	def setPx(self,pos,col):
		if len(pos)!=3 or len(col)!=4:
			print "Illegal voxelmap drawing parameters"
			return
		x=pos[0]
		y=pos[1]
		z=pos[2]
		if x<0 or x>=self.xSize or y<0 or y>=self.ySize or z<0 or z>=self.zSize:
			print "Illegal voxelmap point"
			return
		offs=(z*self.ySize*self.xSize+y*self.xSize+x)*4
		self.vMap[offs+0]=col[0]
		self.vMap[offs+1]=col[1]
		self.vMap[offs+2]=col[2]
		self.vMap[offs+3]=col[3]
	def getPx(self,pos):
		if len(pos)!=3:
			print "Illegal voxelmap drawing parameters"
			return []
		x=pos[0]
		y=pos[1]
		z=pos[2]
		if x<0 or x>=self.xSize or y<0 or y>=self.ySize or z<0 or z>=self.zSize:
			print "Illegal voxelmap point"
			return
		
		offs=(z*self.ySize*self.xSize+y*self.xSize+x)*4
		return [self.vMap[offs+0],self.vMap[offs+1],self.vMap[offs+2],self.vMap[offs+3]]
	
	def blitFrom(self,vMapSource,destPos):
		
		dxA = max(min(destPos[0],self.xSize),0)
		dyA = max(min(destPos[1],self.ySize),0)
		dzA = max(min(destPos[2],self.zSize),0)

		dxB = max(min(destPos[0]+vMapSource.xSize,self.xSize),0)
		dyB = max(min(destPos[1]+vMapSource.ySize,self.ySize),0)
		dzB = max(min(destPos[2]+vMapSource.zSize,self.zSize),0)
		
		sx=dxA-destPos[0]
		for x in xrange( dxA,dxB ):
			sy=dyA-destPos[1]
			for y in xrange( dyA,dyB ):
				sz=dzA-destPos[2]
				for z in xrange( dzA,dzB ):
					spx = vMapSource.getPx([ sx, sy, sz ])
					if spx[3]!=0:
						self.setPx([ x, y, z ],spx)
					sz+=1
				sy+=1
			sx+=1
	
	def clone(self):
		ret=voxelmap(self.xSize,self.ySize,self.zSize)
		for i in xrange(self.xSize*self.ySize*self.zSize*4):
			ret.vMap[i]=self.vMap[i]
		return ret
	
	def dbgout(self):
		print "voxelmap:"
		print "\txSize=",self.xSize
		print "\tySize=",self.ySize
		print "\tzSize=",self.zSize


#####################################################
# Voxel image

class voxelLayer:
	def __init__(self,name,vMap):
		self.vMap=vMap
		self.name=name
		self.xPos=0
		self.yPos=0
		self.zPos=0
		self.renderMode=2
		self.nSubSurface=0
		self.material=0
		self.normalTolerance=0
		self.cartoon=False
		self.smoothPasses=4
		self.smoothRadius=1
		self.generated=False
	
	def clone(self):
		vmc=self.vMap.clone()
		ret=voxelLayer(self.name+"",vmc)
		ret.xPos=self.xPos
		ret.yPos=self.yPos
		ret.zPos=self.zPos
		ret.renderMode=self.renderMode
		ret.nSubSurface=self.nSubSurface
		ret.material=self.material
		ret.normalTolerance=self.normalTolerance
		ret.cartoon=self.cartoon
		ret.smoothPasses=self.smoothPasses
		ret.smoothRadius=self.smoothRadius
		return ret

class voxelImage:
	def __init__(self,xSize,ySize,zSize):
		self.xSize=xSize
		self.ySize=ySize
		self.zSize=zSize
		self.layers=[]
		self.activeLayer=0
		self.selMask=voxelmask(xSize,ySize,zSize)
		self.clipboard=None
		self.generated=False
	
	def newLayer(self,name):
		self.layers.append(voxelLayer(name,voxelmap(self.xSize,self.ySize,self.zSize)))
		
	def addLayer(self,name,vMap):
		l=voxelLayer(name,vMap)
		self.layers.append(l)
		return l
		
	def save(self,path):
		# Write header
		b=open(path,'wb')
		b.write('K3DGv001')
		# Write basic info
		b.write(struct.pack(">IIII",self.xSize,self.ySize,self.zSize,len(self.layers)))
		for l in self.layers:
			b.write(struct.pack(">IIII",l.vMap.xSize,l.vMap.ySize,l.vMap.zSize,len(l.name)))
			b.write(l.name)
			b.write(struct.pack(">iiiiiiiiii",l.xPos,l.yPos,l.zPos,l.renderMode,l.nSubSurface,l.material,l.normalTolerance,int(l.cartoon),l.smoothPasses,l.smoothRadius))
			# Write voxels
			for j in xrange(l.vMap.xSize*l.vMap.ySize*l.vMap.zSize*4):
				b.write( struct.pack(">B",l.vMap.vMap[j]) )
		b.close()
		
	def load(self,path):
		# Open and make sure it is compatible.
		b=open(path,'r')
		s=b.read(4)
		if s!='K3DG':
			print "Not a Katachi3D graphics file"
			b.close()
			return
		v=b.read(4)
		if v=="v001":
			print "Katachi3D version 0.001 graphics file"
		else:
			print "Unsupported file version"
			b.close()
			return
		# Read basic info
		xs,ys,zs,nl = struct.unpack(">IIII",b.read(struct.calcsize(">IIII")))
		print "\txSize = ",xs
		print "\tySize = ",ys
		print "\tzSize = ",zs
		print "\t# layers = ",nl
		self.layers=[]
		self.xSize=xs
		self.ySize=ys
		self.zSize=zs
		# Read layers
		for i in xrange(nl):
			lxs,lys,lzs,nlen = struct.unpack(">IIII",b.read(struct.calcsize(">IIII")))
			lname = ""
			if nlen>0:
				lname = b.read(nlen)
			print "\tLayer \"",lname,"\""
			print "\t\txSize = ",lxs
			print "\t\tySize = ",lys
			print "\t\tzSize = ",lzs
			xPos,yPos,zPos,renderMode,nSubSurface,material,normalTolerance,cartoon,smoothPasses,smoothRadius=struct.unpack(">iiiiiiiiii",b.read(struct.calcsize(">iiiiiiiiii")))
			# Read voxels
			vm = voxelmap(lxs,lys,lzs)
			for j in xrange(lxs*lys*lzs*4):
				vm.vMap[j] = struct.unpack(">B",b.read(1))[0]
			nlayer=voxelLayer(lname,vm)
			nlayer.xPos=xPos
			nlayer.yPos=yPos
			nlayer.zPos=zPos
			nlayer.renderMode=renderMode
			nlayer.nSubSurface=nSubSurface
			nlayer.material=material
			nlayer.normalTolerance=normalTolerance
			nlayer.cartoon=cartoon
			nlayer.smoothPasses=smoothPasses
			nlayer.smoothRadius=smoothRadius
			self.layers.append(nlayer)
		b.close()
		self.selMask=voxelmask(self.xSize,self.ySize,self.zSize)
		
	def clone(self):
		ret=voxelImage(self.xSize,self.ySize,self.zSize)
		ret.activeLayer=self.activeLayer
		for l in self.layers:
			ret.layers.append(l.clone())
		return ret
	
	def dbgout(self):
		print "Voxel image:"
		print "\txSize=",self.xSize
		print "\tySize=",self.ySize
		print "\tzSize=",self.zSize
		for l in self.layers:
			print "\tLayer \"",l.name,"\":"
			print "\t\txSize=",l.vMap.xSize
			print "\t\tySize=",l.vMap.ySize
			print "\t\tzSize=",l.vMap.zSize


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


#####################################################
# 3D Model

class Model:
	def __init__(self):
		self.meshes=[]
		self.center=Vector3D(0,0,0)
	def newMesh(self):
		r=Mesh()
		self.meshes.append(r)
		return r
	def renderFlat(self):
		renderFlatCython(self)
		return
	def renderLight(self):
		renderLightCython(self)
		return
	def dbgout(self):
		print "Model:"
		print " - Center: ",self.center.x,", ",self.center.y,", ",self.center.z
		print " - Meshes[",(len(self.meshes)),"]"
		for m in self.meshes:
			m.dbgout()


#####################################################
# Other

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
	dc.SetPen(wx.Pen(wx.NamedColour('medium grey'),1))
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
	for z in xrange(zS):
		for _y in xrange(yS):
			y=yS-_y-1
			for x in xrange(xS):
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
						dc.SetBrush(wx.Brush(wx.Colour( colL[0],colL[1],colL[2] ),1))
						dc.DrawPolygon([ [p1[0],p1[1]], [p2[0],p2[1]], [p3[0],p3[1]], [p4[0],p4[1]] ])
					if dy:
						p7 = [(x-z)*2*zoom+xC,(x+z+sy)*zoom+yC]
						dc.SetPen(wx.Pen(wx.Colour( r,g,b ),1))
						dc.SetBrush(wx.Brush(wx.Colour( r,g,b ),1))
						dc.DrawPolygon([ [p1[0],p1[1]], [p7[0],p7[1]], [p5[0],p5[1]], [p2[0],p2[1]] ])
					if dz:
						colD=[ max(r*0.9-20,0),max(g*0.9-20,0),max(b*0.9-20,0) ]
						p6 = [(x-z-1)*2*zoom+xC,(x+z+1+sy2)*zoom+yC]
						dc.SetPen(wx.Pen(wx.Colour( colD[0],colD[1],colD[2] ),1))
						dc.SetBrush(wx.Brush(wx.Colour( colD[0],colD[1],colD[2] ),1))
						dc.DrawPolygon([ [p2[0],p2[1]], [p5[0],p5[1]], [p6[0],p6[1]], [p3[0],p3[1]] ])
	#


#####################################################
# Voxel editor

# Axes:
#	Z-axis: X/Y for editing, stepping through Z
#	X-axis: Z/Y for editing, stepping through X
#	Y-axis: X/Z for editing, stepping through Y
axisName=["Z-axis","X-axis","Y-axis"]

class voxelmapDraw(wx.Window):
	def __init__(self,parent,ID,prj,axis=2,zoom=8):
		wx.Window.__init__(self,parent,ID,pos=wx.DefaultPosition,size=wx.DefaultSize)
		self.SetCursor(wx.StockCursor(wx.CURSOR_PENCIL))
		if wx.Platform=='__WXGTK__':
			self.font = wx.Font(10,wx.MODERN,wx.NORMAL,wx.NORMAL)
		else:
			self.font = wx.Font(8,wx.MODERN,wx.NORMAL,wx.NORMAL)
		self.xSize=0
		self.ySize=0
		self.xScroll=0
		self.yScroll=0
		self.clkL=False
		self.clkMode=0
		self.zInd=0
		self.prj=prj
		self._parent=parent
		self.cxa=-1
		self.cya=-1
		self.cza=-1
		self.cxb=-1
		self.cyb=-1
		#
		self.zoom=zoom
		self.axis=axis
		self.vm=None
		self.layer=None
		self.setLayer(prj.activeLayer)
		#
		self.Bind(wx.EVT_LEFT_DOWN,self.leftclick)
		self.Bind(wx.EVT_LEFT_UP,self.leftunclick)
		self.Bind(wx.EVT_MOTION,self.motion)
		self.Bind(wx.EVT_MOUSEWHEEL,self.wheel)
		self.Bind(wx.EVT_PAINT,self.repaint)
		self.Bind(wx.EVT_SIZE,self.resize)
		self.Bind(wx.EVT_WINDOW_DESTROY,self.cleanup)
		self.Bind(wx.EVT_KEY_DOWN,self.keydown)
		self.Bind(wx.EVT_SET_FOCUS,self.sfocus)
		self.Bind(wx.EVT_KILL_FOCUS,self.kfocus)
		self._focus=False
		#
		self.changed=False
	
	def setZ(self,z):
		self.zInd=z
		if self.axis==0:
			self._parent.cZ=z
		elif self.axis==1:
			self._parent.cX=z
		elif self.axis==2:
			self._parent.cY=z
	
	def RefreshActive(self):
		self.Refresh()
	
	def setProject(self,prj):
		self.prj=prj
		self.setLayer(prj.activeLayer)
	
	def setLayer(self,layer):
		if layer<0 or layer>=len(self.prj.layers):
			print "Invalid layer"
			return
		self.layer=self.prj.layers[self.prj.activeLayer]
		self.vm=self.layer.vMap
		if self.axis==0:
			self.setZ(int(self.vm.zSize/2)+self.layer.zPos)
		elif self.axis==1:
			self.setZ(int(self.vm.xSize/2)+self.layer.xPos)
		elif self.axis==2:
			self.setZ(int(self.vm.ySize/2)+self.layer.yPos)
	
	def cleanup(self,evt):
		pass
		
	def getVMLimits(self,vm):
		if self.axis==0:
			return [vm.xSize,vm.ySize,vm.zSize]
		elif self.axis==1:
			return [vm.zSize,vm.ySize,vm.xSize]
		elif self.axis==2:
			return [vm.xSize,vm.zSize,vm.ySize]
		return [0,0]
	def getLayerPos(self,layer):
		if self.axis==0:
			return [layer.xPos,layer.yPos,layer.zPos]
		elif self.axis==1:
			return [self.prj.zSize-layer.vMap.zSize-layer.zPos,layer.yPos,layer.xPos]
		elif self.axis==2:
			return [layer.xPos,layer.zPos,layer.yPos]
		return [0,0]
	def getProjectLimits(self):
		if self.axis==0:
			return [self.prj.xSize,self.prj.ySize,self.prj.zSize]
		elif self.axis==1:
			return [self.prj.zSize,self.prj.ySize,self.prj.xSize]
		elif self.axis==2:
			return [self.prj.xSize,self.prj.zSize,self.prj.ySize]
		return [0,0]
	def local2globalPX(self,lx,ly,lz,vm):
		ret=[0,0,0]
		if self.axis==0:
			ret=[lx,ly,lz]
		elif self.axis==1:
			ret=[lz,ly,vm.zSize-lx-1]
		elif self.axis==2:
			ret=[lx,lz,ly]
		return ret
	def global2localPX(self,gx,gy,gz,vm):
		ret=[0,0,0]
		if self.axis==0:
			ret=[gx,gy,gz]
		elif self.axis==1:
			ret=[vm.zSize-gz-1,gy,gx]
		elif self.axis==2:
			ret=[gx,gz,gy]
		return ret
	
	def sfocus(self,evt):
		self._focus=True
		self._parent.caxis=self.axis
		self._parent.RefreshClientsActive()
	def kfocus(self,evt):
		self._focus=False
		if self._parent.caxis==self.axis:
			self._parent.caxis=None
			self._parent.RefreshClientsActive()
		else:
			self.Refresh()
	
	def leftclick(self,evt):
		self.CaptureMouse()
		pos=evt.GetPosition()
		self.clkL=True
		self.clkMode=0
		self.cxa=pos.x
		self.cya=pos.y
		self.cza=self.zInd
		if self.prj.clipboard!=None:
			if self.ptInClipboard(pos.x,pos.y):
				self.clkMode=2
				self.prj.clipboard.oxPos=self.prj.clipboard.xPos
				self.prj.clipboard.oyPos=self.prj.clipboard.yPos
				self.prj.clipboard.ozPos=self.prj.clipboard.zPos
			else:
				cpl=self.prj.clipboard
				cpvm=cpl.vMap
				self._parent._parent.EHCandidateActiveLayer()
				self.layer.vMap.blitFrom(cpvm,[cpl.xPos-self.layer.xPos,cpl.yPos-self.layer.yPos,cpl.zPos-self.layer.zPos])
				self._parent._parent.EHAddCandidate()
				self.prj.clipboard=None
		if self.clkMode!=2:
			plimits=self.getProjectLimits()
			x1=(self.xSize-plimits[0]*self.zoom)/2-self.xScroll
			z1=(self.ySize-plimits[2]*self.zoom)/2-self.yScroll
			if pos.x>=x1-2-self.zoom-8 and pos.x<x1-8 and pos.y>=z1 and pos.y<z1+plimits[2]*self.zoom:
				self.clkMode=1
		if self.clkMode==0:
			if self._parent._parent.tool==2 or self._parent._parent.tool==3 or self._parent._parent.tool==4:
				self._parent._parent.EHCandidateActiveLayer()
			elif self._parent._parent.tool==5:
				plimits=self.getProjectLimits()
				lpos=self.getLayerPos(self.layer)
				limits=self.getVMLimits(self.vm)
				z1=(self.ySize-plimits[2]*self.zoom)/2-self.yScroll
				lx1=(self.xSize-plimits[0]*self.zoom)/2-self.xScroll+lpos[0]*self.zoom
				ly1=(self.ySize-plimits[1]*self.zoom)/2-self.yScroll+lpos[1]*self.zoom
				zI=self.zInd-lpos[2]
				lx=int((pos.x-lx1)/self.zoom)
				ly=int((pos.y-ly1)/self.zoom)
				if pos.x>=lx1 and lx<limits[0] and pos.y>=ly1 and ly<limits[1] and zI>=0 and zI<limits[2]:
					basecol=self.vm.getPx(self.local2globalPX(lx,ly,zI,self.vm))
					if wx.GetKeyState(wx.WXK_CONTROL):
						self._parent.setColour(basecol)
					else:
						if wx.GetKeyState(wx.WXK_SHIFT):
							destcol=[0,0,0,0]
						else:
							destcol=self._parent._parent.penColour
						if not self.colourCloseEnough(basecol,destcol):
							self._parent._parent.EHCandidateActiveLayer()
							vm=self.vm
							self.vm.setPx(self.local2globalPX(lx,ly,zI,vm),destcol)
							Q=[ [lx,ly,zI] ]
							while len(Q)>0:
								e=Q.pop()
								pl=[ [e[0]-1,e[1],e[2]], [e[0],e[1]-1,e[2]], [e[0]+1,e[1],e[2]], [e[0],e[1]+1,e[2]] ]
								for p in pl:
									gp=self.local2globalPX(p[0],p[1],p[2],vm)
									if self.ptEditable(gp) and self.colourCloseEnough(self.vm.getPx(gp),basecol):
										self.vm.setPx(gp,destcol)
										Q.append(p)
							self._parent._parent.EHAddCandidate()
			elif self._parent._parent.tool==6:
				plimits=self.getProjectLimits()
				lpos=self.getLayerPos(self.layer)
				limits=self.getVMLimits(self.vm)
				z1=(self.ySize-plimits[2]*self.zoom)/2-self.yScroll
				lx1=(self.xSize-plimits[0]*self.zoom)/2-self.xScroll+lpos[0]*self.zoom
				ly1=(self.ySize-plimits[1]*self.zoom)/2-self.yScroll+lpos[1]*self.zoom
				zI=self.zInd-lpos[2]
				lx=int((pos.x-lx1)/self.zoom)
				ly=int((pos.y-ly1)/self.zoom)
				basept=self.local2globalPX(lx,ly,zI,self.vm)
				if self.ptEditable(basept):
					basecol=self.vm.getPx(basept)
					if wx.GetKeyState(wx.WXK_CONTROL):
						self._parent.setColour(basecol)
					else:
						if wx.GetKeyState(wx.WXK_SHIFT):
							destcol=[0,0,0,0]
						else:
							destcol=self._parent._parent.penColour
						if not self.colourCloseEnough(basecol,destcol):
							self._parent._parent.EHCandidateActiveLayer()
							vm=self.vm
							self.vm.setPx(basept,destcol)
							Q=[ basept ]
							while len(Q)>0:
								e=Q.pop()
								pl=[ [e[0]-1,e[1],e[2]], [e[0],e[1]-1,e[2]], [e[0],e[1],e[2]-1], [e[0]+1,e[1],e[2]], [e[0],e[1]+1,e[2]], [e[0],e[1],e[2]+1] ]
								for p in pl:
									if self.ptEditable(p) and self.colourCloseEnough(self.vm.getPx(p),basecol):
										self.vm.setPx(p,destcol)
										Q.append(p)
							self._parent._parent.EHAddCandidate()
		self.hclk(pos.x,pos.y)
		self.SetFocus()
	
	def colourCloseEnough(self,colA,colB):
		if colA[0]==colB[0] and colA[1]==colB[1] and colA[2]==colB[2] and colA[3]==colB[3]:
			return True
		return False
	
	def ptInClipboard(self,x,y):
		cpl=self.prj.clipboard
		cpvm=cpl.vMap
		plimits=self.getProjectLimits()
		lpos=self.getLayerPos(cpl)
		limits=self.getVMLimits(cpvm)
		z1=(self.ySize-plimits[2]*self.zoom)/2-self.yScroll
		lx1=(self.xSize-plimits[0]*self.zoom)/2-self.xScroll+lpos[0]*self.zoom
		ly1=(self.ySize-plimits[1]*self.zoom)/2-self.yScroll+lpos[1]*self.zoom
		zI=self.zInd-lpos[2]
		lx=int((x-lx1)/self.zoom)
		ly=int((y-ly1)/self.zoom)
		if x>=lx1 and lx<limits[0] and y>=ly1 and ly<limits[1]:
			if zI>=0 and zI<limits[2]:
				if cpvm.getPx(self.local2globalPX(lx,ly,zI,cpvm))[3]!=0:
					return True
		return False

	def ptEditable(self,_pt):
		l=self.layer
		if _pt[0]<0 or _pt[0]>=l.vMap.xSize or _pt[1]<0 or _pt[1]>=l.vMap.ySize or _pt[2]<0 or _pt[2]>=l.vMap.zSize:
			return False
		mask=self.prj.selMask
		if mask.empty:
			return True
		pt=[_pt[0]+l.xPos,_pt[1]+l.yPos,_pt[2]+l.zPos]
		if pt[0]<0 or pt[1]<0 or pt[2]<0 or pt[0]>=mask.xSize or pt[1]>=mask.ySize or pt[2]>=mask.zSize:
			return False
		if mask.getPx(pt)!=0:
			return True
		else:
			return False
	
	def leftunclick(self,evt):
		self.ReleaseMouse()
		pos=evt.GetPosition()
		self.clkL=False
		if self._parent._parent.tool==0 and self.clkMode==0:
			if not wx.GetKeyState(wx.WXK_SHIFT):
				self._parent.clearSelection()
			self._parent.addSelectionRectangle()
		self.cxa=-1
		self.cya=-1
		if self.changed:
			if self.clkMode==0 and (self._parent._parent.tool==2 or self._parent._parent.tool==3 or self._parent._parent.tool==4):
				self._parent._parent.EHAddCandidate()
			self.changed=False
		else:
			if self.clkMode==0 and (self._parent._parent.tool==2 or self._parent._parent.tool==3 or self._parent._parent.tool==4):
				self._parent._parent.EHClearCandidate()
		
	def motion(self,evt):
		pos=evt.GetPosition()
		self.hclk(pos.x,pos.y)

	def wheel(self,evt):
		d=evt.GetWheelRotation()
		if wx.GetKeyState(wx.WXK_CONTROL):
			pzoom=self.zoom
			self.zoom*=1+d*0.001
			self.xScroll*=self.zoom/pzoom
			self.yScroll*=self.zoom/pzoom
			self.Refresh()
		elif wx.GetKeyState(wx.WXK_SHIFT):
			self.xScroll-=d*0.2
			self.Refresh()
		elif wx.GetKeyState(wx.WXK_ALT):
			self.setZ(max(min(int(self.zInd-d*0.01),self.getProjectLimits()[2]-1),0))
			if self._parent._parent.tool==0 and self.clkMode==0 and self.clkL:
				self.czb=self.zInd
				self.updateSelRect()
			else:
				self._parent.RefreshClientsActive()
		else:
			self.yScroll-=d*0.2
			self.Refresh()
	
	def updateSelRect(self):
		plimits=self.getProjectLimits()
		pxs=plimits[0]*self.zoom
		pys=plimits[1]*self.zoom
		pos=self.getLayerPos(self.layer)
		lx1=(self.xSize-pxs)/2-self.xScroll+pos[0]*self.zoom
		ly1=(self.ySize-pys)/2-self.yScroll+pos[1]*self.zoom
		pA=self.local2globalPX(int((self.cxa-lx1)/self.zoom),int((self.cya-ly1)/self.zoom),min(self.cza,self.zInd)-pos[2],self.vm)
		pB=self.local2globalPX(int((self.cxb-lx1)/self.zoom),int((self.cyb-ly1)/self.zoom),max(self.cza,self.zInd+1)-pos[2],self.vm)
		self._parent.setSelectionRectangle(pA[0],pA[1],pA[2],pB[0],pB[1],pB[2])
	
	def hclk(self,x,y):
		plimits=self.getProjectLimits()
		pos=self.getLayerPos(self.layer)
		limits=self.getVMLimits(self.vm)
		z1=(self.ySize-plimits[2]*self.zoom)/2-self.yScroll
		lx1=(self.xSize-plimits[0]*self.zoom)/2-self.xScroll+pos[0]*self.zoom
		ly1=(self.ySize-plimits[1]*self.zoom)/2-self.yScroll+pos[1]*self.zoom
		zI=self.zInd-pos[2]
		self.cxb=x
		self.cyb=y
		if self.clkL and self.clkMode==1:
			self.setZ(max(min(int(int((y-z1)/self.zoom)),limits[2]-1),0))
			self._parent.RefreshClientsActive()
		elif self.clkL and self.clkMode==2:
			pA=self.local2globalPX(int(self.cxa/self.zoom),int(self.cya/self.zoom),self.cza,self.prj.clipboard.vMap)
			pB=self.local2globalPX(int(self.cxb/self.zoom),int(self.cyb/self.zoom),self.zInd,self.prj.clipboard.vMap)
			self.prj.clipboard.xPos = self.prj.clipboard.oxPos+pB[0]-pA[0]
			self.prj.clipboard.yPos = self.prj.clipboard.oyPos+pB[1]-pA[1]
			self.prj.clipboard.zPos = self.prj.clipboard.ozPos+pB[2]-pA[2]
			self._parent.RefreshClientsActive()
		else:
			lx=int((x-lx1)/self.zoom)
			ly=int((y-ly1)/self.zoom)
			if self._parent._parent.tool==0 and self.clkMode==0 and self.clkL:
				self.updateSelRect()
			elif (self._parent._parent.tool==1 or wx.GetKeyState(wx.WXK_CONTROL)) and self.clkL:
				if x>=lx1 and lx<limits[0] and y>=ly1 and ly<limits[1]:
					if zI>=0 and zI<limits[2]:
						self._parent.setColour(self.vm.getPx(self.local2globalPX(lx,ly,zI,self.vm)))
			elif self._parent._parent.tool==2 and self.clkL:
				gpx=self.local2globalPX(lx,ly,zI,self.vm)
				if self.ptEditable(gpx):
					if wx.GetKeyState(wx.WXK_SHIFT):
						self.vm.setPx(gpx,[0,0,0,0])
					else:
						self.vm.setPx(gpx,self._parent._parent.penColour)
					self._parent.RefreshClientsActive()
					self.changed=True
			elif self._parent._parent.tool==3 and self.clkL:
				ps=self._parent._parent.cpenSize*0.5
				ch=False
				minX=int(max(min(lx-ps,limits[0]),0))
				maxX=int(max(min(lx+ps+1,limits[0]),0))
				minY=int(max(min(ly-ps,limits[1]),0))
				maxY=int(max(min(ly+ps+1,limits[1]),0))
				vMap=self.vm.vMap
				sX=self.vm.xSize
				sY=self.vm.ySize
				sZ=self.vm.zSize
				cz=zI
				col=self._parent._parent.penColour
				if zI>=0 and zI<limits[2]:
					for cx in xrange(minX,maxX):
						for cy in xrange(minY,maxY):
							if ((lx-cx)**2+(ly-cy)**2)**(1/2)>=ps+0.2:
								continue
							if self.axis==0:
								gv=[cx,cy,cz]
							elif self.axis==1:
								gv=[cz,cy,sZ-cx-1]
							elif self.axis==2:
								gv=[cx,cz,cy]
							if self.ptEditable(gv):
								offs=(gv[2]*sY*sX+gv[1]*sX+gv[0])*4
								if wx.GetKeyState(wx.WXK_SHIFT):
									vMap[offs+0]=vMap[offs+1]=vMap[offs+2]=vMap[offs+3]=0
								else:
									vMap[offs+0]=col[0]
									vMap[offs+1]=col[1]
									vMap[offs+2]=col[2]
									vMap[offs+3]=col[3]
								ch=True
				if ch:
					self.changed=True
					self._parent.RefreshClientsActive()
			elif self._parent._parent.tool==4 and self.clkL:
				ps=self._parent._parent.cpenSize*0.5
				ch=False
				minX=int(max(min(lx-ps,limits[0]),0))
				maxX=int(max(min(lx+ps+1,limits[0]),0))
				minY=int(max(min(ly-ps,limits[1]),0))
				maxY=int(max(min(ly+ps+1,limits[1]),0))
				minZ=int(max(min(zI-ps,limits[2]),0))
				maxZ=int(max(min(zI+ps+1,limits[2]),0))
				vMap=self.vm.vMap
				sX=self.vm.xSize
				sY=self.vm.ySize
				sZ=self.vm.zSize
				col=self._parent._parent.penColour
				mask=self.prj.selMask
				maskVM=None
				smX=0
				smY=0
				smZ=0
				if mask!=None and not mask.empty:
					maskVM=mask.vMap
					smX=mask.xSize
					smY=mask.ySize
					smZ=mask.zSize
				if wx.GetKeyState(wx.WXK_SHIFT):
					if brush3D_cython(vMap, 0,0,0,0, self.axis, sX,sY,sZ, minX,maxX,minY,maxY,minZ,maxZ, ps, lx, ly, zI, maskVM,self.layer.xPos,self.layer.yPos,self.layer.zPos,smX,smY,smZ ) == True:
						self.changed=True
						self._parent.RefreshClientsActive()
				else:
					if brush3D_cython(vMap, col[0],col[1],col[2],col[3], self.axis, sX,sY,sZ, minX,maxX,minY,maxY,minZ,maxZ, ps, lx, ly, zI, maskVM,self.layer.xPos,self.layer.yPos,self.layer.zPos,smX,smY,smZ ) == True:
						self.changed=True
						self._parent.RefreshClientsActive()
				return
		
	def keydown(self,evt):
		if self._parent.childKeyDown(evt):
			return
		limits=self.getProjectLimits()
		xs=limits[0]*self.zoom
		ys=limits[1]*self.zoom
		zs=limits[2]*self.zoom
		kc=evt.GetKeyCode()
		if kc==wx.WXK_NUMPAD_ADD:
			pzoom=self.zoom
			self.zoom*=1.5
			self.xScroll*=self.zoom/pzoom
			self.yScroll*=self.zoom/pzoom
			self.Refresh()
		elif kc==wx.WXK_NUMPAD_SUBTRACT:
			pzoom=self.zoom
			self.zoom/=1.5
			self.xScroll*=self.zoom/pzoom
			self.yScroll*=self.zoom/pzoom
			self.Refresh()
		elif kc==wx.WXK_NEXT:
			self.setZ(max(min(self.zInd+1,limits[2]-1),0))
			self._parent.RefreshClientsActive()
			if self._parent._parent.tool==0 and self.clkMode==0 and self.clkL:
				self.czb=self.zInd
				self.updateSelRect()
			else:
				self.Refresh()
		elif kc==wx.WXK_PRIOR:
			self.setZ(max(self.zInd-1,0))
			self._parent.RefreshClientsActive()
			if self._parent._parent.tool==0 and self.clkMode==0 and self.clkL:
				self.czb=self.zInd
				self.updateSelRect()
			else:
				self.Refresh()
		elif kc==wx.WXK_RIGHT:
			self.xScroll+=25
			self.Refresh()
		elif kc==wx.WXK_LEFT:
			self.xScroll-=25
			self.Refresh()
		elif kc==wx.WXK_DOWN:
			self.yScroll+=25
			self.Refresh()
		elif kc==wx.WXK_UP:
			self.yScroll-=25
			self.Refresh()
		
	def resize(self,evt):
		size=evt.GetSize()
		self.xSize=size.x
		self.ySize=size.y
		self.Refresh()
		
	def repaint(self,evt):
		self.draw(wx.PaintDC(self))
	
	def drawLayer(self,dc,layer,zI,sel):
		plimits=self.getProjectLimits()
		pos=self.getLayerPos(layer)
		limits=self.getVMLimits(layer.vMap)
		lx1=(self.xSize-plimits[0]*self.zoom)/2-self.xScroll+pos[0]*self.zoom
		ly1=(self.ySize-plimits[1]*self.zoom)/2-self.yScroll+pos[1]*self.zoom
		vMap=layer.vMap.vMap
		zoom=self.zoom
		sX=layer.vMap.xSize
		sY=layer.vMap.ySize
		sZ=layer.vMap.zSize
		if zI>=0 and zI<limits[2]:
			for x in xrange(max(0,-pos[0]),min(limits[0],plimits[0]-pos[0])):
				for y in xrange(max(0,-pos[1]),min(limits[1],plimits[1]-pos[1])):
					if self.axis==0:
						gv=[x,y,zI]
					elif self.axis==1:
						gv=[zI,y,sZ-x-1]
					elif self.axis==2:
						gv=[x,zI,y]
					offs=(gv[2]*sY*sX+gv[1]*sX+gv[0])*4
					if vMap[offs+3]!=0:
						dx=lx1+x*zoom
						dy=ly1+y*zoom
						col=wx.Colour(vMap[offs],vMap[offs+1],vMap[offs+2],wx.ALPHA_OPAQUE)
						dc.SetPen(wx.Pen(col,1))
						dc.SetBrush(wx.Brush(col))
						dc.DrawRectangle(int(dx),int(dy),int(dx+zoom+0.5)-int(dx),int(dy+zoom+0.5)-int(dy))
						if sel:
							dc.SetPen(wx.Pen(wx.NamedColour('white'),1,wx.DOT))
							dc.SetBrush(wx.TRANSPARENT_BRUSH)
							if self.axis==0:
								gv1=[x-1,y,zI]
								gv2=[x+1,y,zI]
								gv3=[x,y-1,zI]
								gv4=[x,y+1,zI]
							elif self.axis==1:
								gv1=[zI,y,sZ-x+1-1]
								gv2=[zI,y,sZ-x-1-1]
								gv3=[zI,y-1,sZ-x-1]
								gv4=[zI,y+1,sZ-x-1]
							elif self.axis==2:
								gv1=[x-1,zI,y]
								gv2=[x+1,zI,y]
								gv3=[x,zI,y-1]
								gv4=[x,zI,y+1]
							offs1=(gv1[2]*sY*sX+gv1[1]*sX+gv1[0])*4
							offs2=(gv2[2]*sY*sX+gv2[1]*sX+gv2[0])*4
							offs3=(gv3[2]*sY*sX+gv3[1]*sX+gv3[0])*4
							offs4=(gv4[2]*sY*sX+gv4[1]*sX+gv4[0])*4
							dxA=int(lx1+x*zoom)
							dyA=int(ly1+y*zoom)
							dxB=int(lx1+(x+1)*zoom)
							dyB=int(ly1+(y+1)*zoom)
							if x==0 or vMap[offs1+3]==0:
								dc.DrawLine(dxA,dyA,dxA,dyB)
							if x==limits[0]-1 or vMap[offs2+3]==0:
								dc.DrawLine(dxB,dyA,dxB,dyB)
							if y==0 or vMap[offs3+3]==0:
								dc.DrawLine(dxA,dyA,dxB,dyA)
							if y==limits[1]-1 or vMap[offs4+3]==0:
								dc.DrawLine(dxA,dyB,dxB,dyB)
	
	def draw(self,dc=None):
		if not dc:
			dc=wx.PaintDC(self)
		dc.SetFont(self.font)
		#
		zoom=self.zoom
		dc.SetPen(wx.Pen(wx.NamedColour('black'),1))
		dc.SetBrush(wx.TRANSPARENT_BRUSH)
		plimits=self.getProjectLimits()
		pos=self.getLayerPos(self.layer)
		pxs=plimits[0]*zoom
		pys=plimits[1]*zoom
		pzs=plimits[2]*zoom
		limits=self.getVMLimits(self.vm)
		xs=limits[0]*zoom
		ys=limits[1]*zoom
		zs=limits[2]*zoom
		x1=(self.xSize-pxs)/2-self.xScroll
		y1=(self.ySize-pys)/2-self.yScroll
		z1=(self.ySize-pzs)/2-self.yScroll
		lx1=x1+pos[0]*zoom
		ly1=y1+pos[1]*zoom
		_wx=x1
		_wy=y1
		_wxs=pxs
		_wys=pys
		if _wx<0:
			_wxs+=_wx
			_wx=0
		if _wy<0:
			_wys+=_wy
			_wy=0
		dc.Blit(_wx,_wy,_wxs,_wys,bgDC,0,0)
		dc.DrawRectangle(x1-1,y1-1,pxs+2,pys+2)
		dc.DrawRectangle(x1-2-self.zoom-8,z1-1,self.zoom+2,pzs+2)

		dc.DrawRectangle(x1-1+pos[0]*zoom,y1-1+pos[1]*zoom,xs+2,ys+2)
		dc.DrawRectangle(x1-2-self.zoom-8,z1-1+pos[2]*zoom,self.zoom+2,zs+2)
		#
		dc.SetBrush(wx.Brush(wx.NamedColour('red')))
		dc.DrawRectangle(x1-self.zoom-10,z1-1+self.zInd*self.zoom,self.zoom+2,self.zoom+2)
		#
		dc.SetBrush(wx.Brush(wx.NamedColour('grey')))
		if self.axis==0:
			dc.DrawRectangle(x1+pxs+10,y1-1+self._parent.cY*self.zoom,self.zoom+2,self.zoom+2)
			dc.DrawRectangle(x1-1+self._parent.cX*self.zoom,y1+pys+10,self.zoom+2,self.zoom+2)
		elif self.axis==1:
			dc.DrawRectangle(x1+pxs+10,y1-1+self._parent.cY*self.zoom,self.zoom+2,self.zoom+2)
			dc.DrawRectangle(x1-1+(self.vm.zSize-self._parent.cZ-1)*self.zoom,y1+pys+10,self.zoom+2,self.zoom+2)
		elif self.axis==2:
			dc.DrawRectangle(x1+pxs+10,y1-1+self._parent.cZ*self.zoom,self.zoom+2,self.zoom+2)
			dc.DrawRectangle(x1-1+self._parent.cX*self.zoom,y1+pys+10,self.zoom+2,self.zoom+2)
		#
		vMap=self.vm.vMap
		psX=self.prj.xSize
		psY=self.prj.ySize
		zI=self.zInd
		#
		li=0
		for l in self.prj.layers:
			if li!=self.prj.activeLayer:
				if not self._parent._parent.singleLayer:
					self.drawLayer(dc,l,self.zInd-self.getLayerPos(l)[2],False)
			li+=1
		self.drawLayer(dc,self.prj.layers[self.prj.activeLayer],self.zInd-pos[2],False)
		if self.prj.clipboard!=None:
			self.drawLayer(dc,self.prj.clipboard,self.zInd-self.getLayerPos(self.prj.clipboard)[2],True)
		#
		selMask=self.prj.selMask
		if selMask!=None and not selMask.empty:
			sm=selMask.vMap
			dc.SetPen(wx.Pen(wx.NamedColour('white'),1,wx.DOT))
			dc.SetBrush(wx.TRANSPARENT_BRUSH)
			for x in xrange(plimits[0]):
				for y in xrange(plimits[1]):
					gv=self.local2globalPX(x,y,zI,self.vm)
					offs=(gv[2]*psY*psX+gv[1]*psX+gv[0])
					if sm[offs]!=0:
						gv1=self.local2globalPX(x-1,y,zI,self.vm)
						offs1=(gv1[2]*psY*psX+gv1[1]*psX+gv1[0])
						gv2=self.local2globalPX(x+1,y,zI,self.vm)
						offs2=(gv2[2]*psY*psX+gv2[1]*psX+gv2[0])
						gv3=self.local2globalPX(x,y-1,zI,self.vm)
						offs3=(gv3[2]*psY*psX+gv3[1]*psX+gv3[0])
						gv4=self.local2globalPX(x,y+1,zI,self.vm)
						offs4=(gv4[2]*psY*psX+gv4[1]*psX+gv4[0])
						dxA=int(x1+x*zoom)
						dyA=int(y1+y*zoom)
						dxB=int(x1+(x+1)*zoom)
						dyB=int(y1+(y+1)*zoom)
						if x==0 or sm[offs1]==0:
							dc.DrawLine(dxA,dyA,dxA,dyB)
						if x==plimits[0]-1 or sm[offs2]==0:
							dc.DrawLine(dxB,dyA,dxB,dyB)
						if y==0 or sm[offs3]==0:
							dc.DrawLine(dxA,dyA,dxB,dyA)
						if y==plimits[1]-1 or sm[offs4]==0:
							dc.DrawLine(dxA,dyB,dxB,dyB)
		if self._parent.selRect:
			dc.SetPen(wx.Pen(wx.NamedColour('white'),1,wx.DOT))
			dc.SetBrush(wx.TRANSPARENT_BRUSH)
			sA = self.global2localPX(self._parent.sxA, self._parent.syA, self._parent.szA,self.vm)
			sB = self.global2localPX(self._parent.sxB, self._parent.syB, self._parent.szB,self.vm)
			if self.axis==1:
				sA[0]+=1
				sB[0]+=1
			if zI>=sA[2] and zI<sB[2]:
				dxA=int( x1+min(sA[0],sB[0])*zoom )
				dyA=int( y1+min(sA[1],sB[1])*zoom )
				dxB=int( x1+max(sA[0],sB[0])*zoom )
				dyB=int( y1+max(sA[1],sB[1])*zoom )
				dc.DrawRectangle(dxA,dyA,dxB-dxA,dyB-dyA)
		if self._focus:
			DrawTextActive(dc,axisName[self.axis],5,5)
		else:
			dc.SetTextForeground(wx.Colour(0,0,0,wx.ALPHA_OPAQUE))
			dc.DrawText(axisName[self.axis],5,5)
		
#		drawIsometric(self.vm,dc,self.xSize-68,self.ySize-68,64,64,0,self.axis==1,self.axis==2,self.axis==0)
	def generate(self):
		pass


#####################################################
# Isometric view

class voxelmapIsoView(wx.Window):
	def __init__(self,parent,ID,prj,zoom=8):
		wx.Window.__init__(self,parent,ID,pos=wx.DefaultPosition,size=wx.DefaultSize)
		self.SetCursor(wx.StockCursor(wx.CURSOR_PENCIL))
		if wx.Platform == '__WXGTK__':
			self.font = wx.Font(10, wx.MODERN, wx.NORMAL, wx.NORMAL)
		else:
			self.font = wx.Font(8, wx.MODERN, wx.NORMAL, wx.NORMAL)
		self._parent=parent
		self.xSize=0
		self.ySize=0
		self.xScroll=0
		self.yScroll=0
		self.vm=0
		self.prj=prj
		self.zoom=zoom
		self.setLayer(prj.activeLayer)
		#
		self.Bind(wx.EVT_MOUSEWHEEL,self.wheel)
		self.Bind(wx.EVT_PAINT,self.repaint)
		self.Bind(wx.EVT_SIZE,self.resize)
		self.Bind(wx.EVT_WINDOW_DESTROY,self.cleanup)
		self.Bind(wx.EVT_KEY_DOWN,self.keydown)
		self.Bind(wx.EVT_SET_FOCUS,self.sfocus)
		self.Bind(wx.EVT_KILL_FOCUS,self.kfocus)
		self._focus=False
		#
	
	def setProject(self,prj):
		self.prj=prj
		self.setLayer(prj.activeLayer)
		
	def setLayer(self,layer):
		if layer<0 or layer>=len(self.prj.layers):
			print "Invalid layer"
			return
		self.layer=self.prj.layers[self.prj.activeLayer]
		self.vm=self.layer.vMap
	
	def cleanup(self,evt):
		pass
		
	def sfocus(self,evt):
		self._focus=True
		self.Refresh()
	def kfocus(self,evt):
		self._focus=False
		self.Refresh()
	
	def RefreshActive(self):
		pass
	
	def wheel(self,evt):
		d=evt.GetWheelRotation()
		if wx.GetKeyState(wx.WXK_CONTROL):
			pzoom=self.zoom
			self.zoom*=1+d*0.001
			self.xScroll*=self.zoom/pzoom
			self.yScroll*=self.zoom/pzoom
			self.Refresh()
		elif wx.GetKeyState(wx.WXK_SHIFT):
			self.xScroll-=d*0.2
			self.Refresh()
		else:
			self.yScroll-=d*0.2
			self.Refresh()
		
	def keydown(self,evt):
		kc=evt.GetKeyCode()
		if kc==wx.WXK_NUMPAD_ADD:
			pzoom=self.zoom
			self.zoom*=1.5
			self.xScroll*=self.zoom/pzoom
			self.yScroll*=self.zoom/pzoom
			self.draw()
		elif kc==wx.WXK_NUMPAD_SUBTRACT:
			pzoom=self.zoom
			self.zoom/=1.5
			self.xScroll*=self.zoom/pzoom
			self.yScroll*=self.zoom/pzoom
			self.draw()
		elif kc==wx.WXK_RIGHT:
			self.xScroll+=25
			self.draw()
		elif kc==wx.WXK_LEFT:
			self.xScroll-=25
			self.draw()
		elif kc==wx.WXK_DOWN:
			self.yScroll+=25
			self.draw()
		elif kc==wx.WXK_UP:
			self.yScroll-=25
			self.draw()
		
	def resize(self,evt):
		size=evt.GetSize()
		self.xSize=size.x
		self.ySize=size.y
		self.Refresh()
		self.draw()
		
	def repaint(self,evt):
		self.draw(wx.PaintDC(self))
	
	def iso2screen(self,x,y,z):
		return [(x-z)*2*self.zoom*0.3,(x+z+y*2.5)*self.zoom*0.3]
	
	def shift(self,vec,x,y):
		return [vec[0]+x,vec[1]+y]
	
	def drawLayer(self,dc,layer):
		zoom=self.zoom
		xS=self.prj.xSize
		zS=self.prj.zSize
		yS=self.prj.ySize
		vMap=layer.vMap.vMap
		lxS=layer.vMap.xSize
		lzS=layer.vMap.zSize
		lyS=layer.vMap.ySize
		lxP=layer.xPos
		lyP=layer.yPos
		lzP=layer.zPos
		pA=self.iso2screen(0,0,0)
		pB=self.iso2screen(xS,yS,zS)
		xC=(pA[0]+pB[0]-self.xSize)/2+self.xScroll
		yC=(pA[1]+pB[1]-self.ySize)/2+self.yScroll
		xMin=max(0,-lxP)
		xMax=lxS-max(((lxP+lxS)-xS),0)
		_yMin=max(((lyP+lyS)-yS),0)
		_yMax=lyS-max(0,-lyP)
		zMin=max(0,-lzP)
		zMax=lzS-max(((lzP+lzS)-zS),0)
		for z in xrange(zMin,zMax):
			gz=z+lzP
			for _y in xrange(_yMin,_yMax):
				y=lyS-_y-1
				gy=y+lyP
				for x in xrange(xMin,xMax):
					gx=x+lxP
					offs=(z*lyS*lxS+y*lxS+x)*4
					if vMap[offs+3]!=0:
						offs2=(z*lyS*lxS+y*lxS+x+1)*4
						dx=x==xMax-1 or vMap[offs2+3]==0
						offs3=(z*lyS*lxS+(y-1)*lxS+x)*4
						dy=_y==_yMax-1 or vMap[offs3+3]==0
						offs4=((z+1)*lyS*lxS+y*lxS+x)*4
						dz=z==zMax-1 or vMap[offs4+3]==0
						if not (dx or dy or dz):
							continue
						r=vMap[offs]
						g=vMap[offs+1]
						b=vMap[offs+2]
						p1 = [(gx+1-gz)*2*zoom*0.3-xC,(gx+1+gz+gy*2.5)*zoom*0.3-yC]
						p2 = [(gx+1-gz-1)*2*zoom*0.3-xC,(gx+1+gz+1+gy*2.5)*zoom*0.3-yC]
						p3 = [(gx+1-gz-1)*2*zoom*0.3-xC,(gx+1+gz+1+(gy+1)*2.5)*zoom*0.3-yC]
						p4 = [(gx+1-gz)*2*zoom*0.3-xC,(gx+1+gz+(gy+1)*2.5)*zoom*0.3-yC]
						p5 = [(gx-gz-1)*2*zoom*0.3-xC,(gx+gz+1+gy*2.5)*zoom*0.3-yC]
						if dx:
							colL=[ min(r*1.1+20,255),min(g*1.1+20,255),min(b*1.1+20,255) ]
							dc.SetPen(wx.Pen(wx.Colour( colL[0],colL[1],colL[2] ),1))
							dc.SetBrush(wx.Brush(wx.Colour( colL[0],colL[1],colL[2] ),1))
							dc.DrawPolygon([ [p1[0],p1[1]], [p2[0],p2[1]], [p3[0],p3[1]], [p4[0],p4[1]] ])
						if dy:
							p7 = [(gx-gz)*2*zoom*0.3-xC,(gx+gz+gy*2.5)*zoom*0.3-yC]
							dc.SetPen(wx.Pen(wx.Colour( r,g,b ),1))
							dc.SetBrush(wx.Brush(wx.Colour( r,g,b ),1))
							dc.DrawPolygon([ [p1[0],p1[1]], [p7[0],p7[1]], [p5[0],p5[1]], [p2[0],p2[1]] ])
						if dz:
							colD=[ max(r*0.9-20,0),max(g*0.9-20,0),max(b*0.9-20,0) ]
							p6 = [(gx-gz-1)*2*zoom*0.3-xC,(gx+gz+1+(gy+1)*2.5)*zoom*0.3-yC]
							dc.SetPen(wx.Pen(wx.Colour( colD[0],colD[1],colD[2] ),1))
							dc.SetBrush(wx.Brush(wx.Colour( colD[0],colD[1],colD[2] ),1))
							dc.DrawPolygon([ [p2[0],p2[1]], [p5[0],p5[1]], [p6[0],p6[1]], [p3[0],p3[1]] ])
	
	def draw(self,dc=None):
		if not dc:
			dc=wx.PaintDC(self)
		dc.SetFont(self.font)
		dc.SetBackground(wx.Brush(wx.NamedColour('grey')))
		#
		xS=self.prj.xSize
		zS=self.prj.zSize
		yS=self.prj.ySize
		lxS=self.vm.xSize
		lzS=self.vm.zSize
		lyS=self.vm.ySize
		
		pA=self.iso2screen(0,0,0)
		pB=self.iso2screen(xS,yS,zS)
		xC=(pA[0]+pB[0]-self.xSize)/2+self.xScroll
		yC=(pA[1]+pB[1]-self.ySize)/2+self.yScroll
		
		dc.SetPen(wx.Pen(wx.NamedColour('medium grey'),1))
		dc.SetBrush(wx.TRANSPARENT_BRUSH)

		pC1=self.iso2screen(xS,0,0)
		pC2=self.iso2screen(0,0,zS)
		pD1=self.iso2screen(xS,yS,0)
		pD2=self.iso2screen(0,yS,zS)
		pE=self.iso2screen(0,yS,0)
		dc.DrawLine(pA[0]-xC,pA[1]-yC,pC1[0]-xC,pC1[1]-yC)
		dc.DrawLine(pC1[0]-xC,pC1[1]-yC,pD1[0]-xC,pD1[1]-yC)
		dc.DrawLine(pA[0]-xC,pA[1]-yC,pC2[0]-xC,pC2[1]-yC)
		dc.DrawLine(pC2[0]-xC,pC2[1]-yC,pD2[0]-xC,pD2[1]-yC)
		dc.DrawLine(pA[0]-xC,pA[1]-yC,pE[0]-xC,pE[1]-yC)
		dc.DrawLine(pE[0]-xC,pE[1]-yC,pD1[0]-xC,pD1[1]-yC)
		dc.DrawLine(pE[0]-xC,pE[1]-yC,pD2[0]-xC,pD2[1]-yC)
		dc.DrawLine(pD1[0]-xC,pD1[1]-yC,pB[0]-xC,pB[1]-yC)
		dc.DrawLine(pD2[0]-xC,pD2[1]-yC,pB[0]-xC,pB[1]-yC)
		#
		vMap=self.vm.vMap
		zoom=self.zoom
		layer=self.layer
		#
		li=0
		for l in self.prj.layers:
			if li!=self.prj.activeLayer:
				if not self._parent._parent.singleLayer:
					self.drawLayer(dc,l)
			li+=1
		self.drawLayer(dc,layer)
		if self.prj.clipboard!=None:
			self.drawLayer(dc,self.prj.clipboard)
		#
		tname="Isometric"
		if self._focus:
			DrawTextActive(dc,tname,5,5)
		else:
			dc.SetTextForeground(wx.Colour(0,0,0,wx.ALPHA_OPAQUE))
			dc.DrawText(tname,5,5)

	def generate(self):
		pass


#####################################################
# OpenGL view

class voxelmapOpenGLView(glcanvas.GLCanvas):
	def __init__(self,parent,ID,prj,zoom=8):
		glcanvas.GLCanvas.__init__(self,parent,attribList=(glcanvas.WX_GL_RGBA,glcanvas.WX_GL_DOUBLEBUFFER))
		self.context = glcanvas.GLContext(self)
		self.init=False
		self.mdl=None
		self.calllist=None
		self.calllistm=None
		self.SetCursor(wx.StockCursor(wx.CURSOR_PENCIL))
		self._parent=parent
		self.xSize=0
		self.ySize=0
		self.xScroll=0
		self.yScroll=0
		self.zScroll=12
		self.xRot=-40
		self.yRot=40
		self.vm=0
		self.prj=prj
		self.zoom=zoom
		self.setLayer(prj.activeLayer)
		self.lclk=False
		#
		self.Bind(wx.EVT_MOUSEWHEEL,self.wheel)
		self.Bind(wx.EVT_PAINT,self.repaint)
		self.Bind(wx.EVT_SIZE,self.resize)
		self.Bind(wx.EVT_WINDOW_DESTROY,self.cleanup)
		self.Bind(wx.EVT_KEY_DOWN,self.keydown)
		self.Bind(wx.EVT_SET_FOCUS,self.sfocus)
		self.Bind(wx.EVT_KILL_FOCUS,self.kfocus)
		self.Bind(wx.EVT_LEFT_DOWN,self.leftclick)
		self.Bind(wx.EVT_LEFT_UP,self.leftunclick)
		self.Bind(wx.EVT_MOTION,self.motion)
		self.Bind(wx.EVT_ERASE_BACKGROUND,self.erase)
		self._focus=False
		self.drawing=False
		#

	def erase(self,evt):
		pass
	
	def leftclick(self,evt):
		self.SetFocus()
		self.lclk=True
		pos=evt.GetPosition()
		self.xclkA=pos.x
		self.yclkA=pos.y
		self.xRotA=self.xRot
		self.yRotA=self.yRot
	def leftunclick(self,evt):
		self.lclk=False
	def motion(self,evt):
		if not self.lclk:
			return
		pos=evt.GetPosition()
		self.xRot = self.xRotA + (pos.x-self.xclkA)*0.2
		self.yRot = self.yRotA + (pos.y-self.yclkA)*0.2
		self.Refresh()
	
	def setProject(self,prj):
		self.prj=prj
		self.setLayer(prj.activeLayer)
		
	def setLayer(self,layer):
		if layer<0 or layer>=len(self.prj.layers):
			print "Invalid layer"
			return
		self.layer=self.prj.layers[self.prj.activeLayer]
		self.vm=self.layer.vMap
	
	def cleanup(self,evt):
		pass
		
	def sfocus(self,evt):
		self._focus=True
		self.Refresh()
	def kfocus(self,evt):
		self._focus=False
		self.Refresh()
	
	def RefreshActive(self):
		self.Refresh()
	
	def wheel(self,evt):
		d=evt.GetWheelRotation()
		if wx.GetKeyState(wx.WXK_CONTROL):
			self.zScroll-=d*0.01
			self.Refresh()
		elif wx.GetKeyState(wx.WXK_SHIFT):
			self.xScroll-=d*0.01
			self.Refresh()
		else:
			self.yScroll-=d*0.01
			self.Refresh()
		
	def keydown(self,evt):
		if self._parent.childKeyDown(evt):
			return
		kc=evt.GetKeyCode()
		if kc==wx.WXK_NUMPAD_ADD:
			self.zScroll-=1.25
			self.draw()
		elif kc==wx.WXK_NUMPAD_SUBTRACT:
			self.zScroll+=1.25
			self.draw()
		elif kc==wx.WXK_RIGHT:
			self.xScroll+=1.25
			self.draw()
		elif kc==wx.WXK_LEFT:
			self.xScroll-=1.25
			self.draw()
		elif kc==wx.WXK_DOWN:
			self.yScroll+=1.25
			self.draw()
		elif kc==wx.WXK_UP:
			self.yScroll-=1.25
			self.draw()
		
	def resize(self,evt):
		size=evt.GetSize()
		self.xSize=size.x
		self.ySize=size.y
		self.init=False
		self.Refresh()
		
	def repaint(self,evt):
		if self.drawing:
			return
		self.draw()
	
	def draw(self):
		if not self.mdl or self.drawing:
			return
		self.drawing=True
		glFlush()
		self.SetCurrent(self.context)
		if not self.init:
			self.init=True
			glViewport(0,0,self.xSize,self.ySize)
			glMatrixMode(GL_PROJECTION)
			glLoadIdentity()
			v=self.ySize/self.xSize
			glFrustum(-0.5,0.5,-0.5*v,0.5*v,0.8,100.0)
			glMatrixMode(GL_MODELVIEW)
			glLoadIdentity()
			glDisable(GL_TEXTURE_2D)
			glEnable(GL_DEPTH_TEST)
			c=wx.SystemSettings.GetColour(wx.SYS_COLOUR_BACKGROUND)
			glClearColor(c[0]/255,c[1]/255,c[2]/255,0)
			glEnable(GL_CULL_FACE);
			glCullFace(GL_FRONT);
			glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA)
			glEnable(GL_BLEND)
		
			glLightfv(GL_LIGHT0,GL_AMBIENT,(0.1,0.1,0.1,1))
			glLightfv(GL_LIGHT0,GL_DIFFUSE,(0.1,0.1,0.1,1))
			glLightfv(GL_LIGHT0,GL_CONSTANT_ATTENUATION,(0.3))
			glLightfv(GL_LIGHT0,GL_LINEAR_ATTENUATION,(0.02))
			glLightfv(GL_LIGHT0,GL_POSITION,(-self.prj.xSize,-self.prj.ySize,-self.prj.zSize,-18.0))
		
		
		glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
		glPushMatrix()
		
		glTranslatef(-self.xScroll,self.yScroll,-self.zScroll)
		glRotatef(self.yRot,1,0,0)
		glRotatef(self.xRot,0,1,0)
		
		glEnable(GL_DEPTH_TEST)
		glScalef(0.2,-0.2,0.2)
		glTranslatef(-self.prj.xSize/2,-self.prj.ySize/2,-self.prj.zSize/2)
		
		if self._parent._parent.useLight:
			glColor4f(1,1,1,1.0)
			glEnable(GL_LIGHTING)
			glEnable(GL_LIGHT0)
		else:
			glDisable(GL_LIGHTING)
		
		if self.calllist and self.calllistm!=self._parent._parent.useLight:
			glDeleteLists(self.calllist,1)
			self.calllist=None
		if not self.calllist:

			time0=time.time()

			self.calllist=glGenLists(1)
			glNewList(self.calllist,GL_COMPILE)
			if self._parent._parent.useLight:
				self.mdl.renderLight()
			else:
				self.mdl.renderFlat()
			glEndList()
			self.calllistm=self._parent._parent.useLight
			
			print "DBG: OpenGL list generation time: ",(time.time()-time0)
			
		if self.calllist:
			glCallList(self.calllist)
		
		glDisable(GL_LIGHTING)
		glColor4f(0,0,0,0.1)
		glBegin(GL_LINES)
		# Top
		glVertex3f(0,0,0)
		glVertex3f(self.prj.xSize,0,0)
		glVertex3f(self.prj.xSize,0,0)
		glVertex3f(self.prj.xSize,0,self.prj.zSize)
		glVertex3f(self.prj.xSize,0,self.prj.zSize)
		glVertex3f(0,0,self.prj.zSize)
		glVertex3f(0,0,self.prj.zSize)
		glVertex3f(0,0,0)
		# Bottom
		glVertex3f(0,self.prj.ySize,0)
		glVertex3f(self.prj.xSize,self.prj.ySize,0)
		glVertex3f(self.prj.xSize,self.prj.ySize,0)
		glVertex3f(self.prj.xSize,self.prj.ySize,self.prj.zSize)
		glVertex3f(self.prj.xSize,self.prj.ySize,self.prj.zSize)
		glVertex3f(0,self.prj.ySize,self.prj.zSize)
		glVertex3f(0,self.prj.ySize,self.prj.zSize)
		glVertex3f(0,self.prj.ySize,0)
		# Sides
		glVertex3f(0,0,0)
		glVertex3f(0,self.prj.ySize,0)
		glVertex3f(self.prj.xSize,0,0)
		glVertex3f(self.prj.xSize,self.prj.ySize,0)
		glVertex3f(self.prj.xSize,0,self.prj.zSize)
		glVertex3f(self.prj.xSize,self.prj.ySize,self.prj.zSize)
		glVertex3f(0,0,self.prj.zSize)
		glVertex3f(0,self.prj.ySize,self.prj.zSize)
		glEnd()

		# Z-axis
		if self._parent.caxis==0:
			glColor4f(0,0,0,0.5)
		else:
			glColor4f(0,0,0,0.1)
		glBegin(GL_LINES)
		glVertex3f(0,0,self._parent.cZ+0.5)
		glVertex3f(0,self.prj.ySize,self._parent.cZ+0.5)
		glVertex3f(0,self.prj.ySize,self._parent.cZ+0.5)
		glVertex3f(self.prj.xSize,self.prj.ySize,self._parent.cZ+0.5)
		glVertex3f(self.prj.xSize,self.prj.ySize,self._parent.cZ+0.5)
		glVertex3f(self.prj.xSize,0,self._parent.cZ+0.5)
		glVertex3f(self.prj.xSize,0,self._parent.cZ+0.5)
		glVertex3f(0,0,self._parent.cZ+0.5)
		glEnd()
		# X-axis
		if self._parent.caxis==1:
			glColor4f(0,0,0,0.5)
		else:
			glColor4f(0,0,0,0.1)
		glBegin(GL_LINES)
		glVertex3f(self._parent.cX+0.5,0,0)
		glVertex3f(self._parent.cX+0.5,self.prj.ySize,0)
		glVertex3f(self._parent.cX+0.5,self.prj.ySize,0)
		glVertex3f(self._parent.cX+0.5,self.prj.ySize,self.prj.zSize)
		glVertex3f(self._parent.cX+0.5,self.prj.ySize,self.prj.zSize)
		glVertex3f(self._parent.cX+0.5,0,self.prj.zSize)
		glVertex3f(self._parent.cX+0.5,0,self.prj.zSize)
		glVertex3f(self._parent.cX+0.5,0,0)
		glEnd()

		# Y-axis
		if self._parent.caxis==2:
			glColor4f(0,0,0,0.5)
		else:
			glColor4f(0,0,0,0.1)
		glBegin(GL_LINES)
		glVertex3f(0,self._parent.cY+0.5,0)
		glVertex3f(self.prj.xSize,self._parent.cY+0.5,0)
		glVertex3f(self.prj.xSize,self._parent.cY+0.5,0)
		glVertex3f(self.prj.xSize,self._parent.cY+0.5,self.prj.zSize)
		glVertex3f(self.prj.xSize,self._parent.cY+0.5,self.prj.zSize)
		glVertex3f(0,self._parent.cY+0.5,self.prj.zSize)
		glVertex3f(0,self._parent.cY+0.5,self.prj.zSize)
		glVertex3f(0,self._parent.cY+0.5,0)
		glEnd()
		
		glPopMatrix()
		self.SwapBuffers()
		self.drawing=False

	def generate(self):
		time0=time.time()
		
		if not self.prj.generated:
			mdl=Model()
			for layer in self.prj.layers:
				vMap=layer.vMap
				mesh=mdl.newMesh()
				mesh.GenerateFromVoxelLayerCython(layer)
				mesh.postProcess()
				layer.generated=True
			self.mdl=mdl
			self.prj.generated=True
			if self.calllist!=None:
				self.SetCurrent()
				glDeleteLists(self.calllist,1)
				self.calllist=None
		else:
			mdl=self.mdl
			ng=False
			i=0
			for layer in self.prj.layers:
				mesh=mdl.meshes[i]
				if not layer.generated:
					mesh.GenerateFromVoxelLayerCython(layer)
					mesh.postProcess()
					layer.generated=True
					ng=True
				i+=1
			if ng and self.calllist!=None:
				self.SetCurrent()
				glDeleteLists(self.calllist,1)
				self.calllist=None
		
		print " - DBG: Model generation"
		print " - - time: ",(time.time()-time0)


#####################################################
# Multi-viewport editor

class voxelmapEdit(wx.Window):
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
		self.clients.append(voxelmapDraw(self,-1,prj,axis=0,zoom=_zoom))
		self.clients.append(voxelmapDraw(self,-1,prj,axis=1,zoom=_zoom))
		self.clients.append(voxelmapDraw(self,-1,prj,axis=2,zoom=_zoom))
		self.clients.append(voxelmapOpenGLView(self,-1,prj,zoom=_zoom))
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
			print "tool"
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
		for z in xrange(zMin,zMax):
			for y in xrange(yMin,yMax):
				for x in xrange(xMin,xMax):
					if mask.getPx([x+layer.xPos,y+layer.yPos,z+layer.zPos]):
						vMap.setPx([x,y,z],[0,0,0,0])
		self._parent.EHAddCandidate()
		
	def selectAll(self):
		b=self.prj.selMask.vMap
		xs=self.prj.selMask.xSize
		ys=self.prj.selMask.ySize
		zs=self.prj.selMask.zSize
		for x in xrange(xs):
			for y in xrange(ys):
				for z in xrange(zs):
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
		for x in xrange(self.sxA,self.sxB):
			for y in xrange(self.syA,self.syB):
				for z in xrange(self.szA,self.szB):
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
	
#	def changed(self):
#		self._parent.changed()
#		self.updateClients()
	
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


#####################################################
# Layer window

layerHeight = 64

class layerWin(wx.Window):
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
			print "Invalid layer"
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
			print "Can't move layer further up."
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
			print "Can't move layer further down."
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
			print "Can't remove bottom layer."
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
		self.Refresh()
		self.draw()

	def repaint(self,evt):
		self.draw(wx.PaintDC(self))
	
	def layerRect(self,ind):
		return [ 0,layerHeight*ind,self.xSize,layerHeight ]
	
	def draw(self,dc=None):
		if not dc:
			dc=wx.PaintDC(self)
		dc.SetFont(self.font)
		i=0
		for l in self.prj.layers:
			r = self.layerRect(i)
			if i==self.prj.activeLayer:
				dc.SetPen(wx.Pen(wx.NamedColour('white'),1,wx.DOT))
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


#####################################################
# Properties window

renderModeNames=['Hard','VPS','VPS+NC']
#renderModeNames=['Hard','Positional smoothing','Positional smoothing with normal compensation']

class propertiesWin(wx.Window):
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

		layerSizer=wx.FlexGridSizer(2,20,0,0)
		layerSizer.AddMany([ (wx.StaticText(self,-1,"Name"),2,wx.GROW|wx.ALIGN_CENTER|wx.LEFT|wx.RIGHT|wx.TOP,6), (self.namer,0,wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL,1) ])
		
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
#		sizer.Add(layerSizer,1,wx.EXPAND)

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
			print "Invalid layer"
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


#####################################################
# Pane window

paneSize = 24
paneMargin = 2
paneWidth = 150

class paneWin(wx.Window):
	def __init__(self,mparent,parent,ID,orientation,openSize):
		wx.Window.__init__(self,parent,ID,pos=wx.DefaultPosition,size=wx.DefaultSize)
		if wx.Platform == '__WXGTK__':
			self.font = wx.Font(10, wx.MODERN, wx.NORMAL, wx.NORMAL)
		else:
			self.font = wx.Font(8, wx.MODERN, wx.NORMAL, wx.NORMAL)
		#
		self.orientation=orientation
		self._parent=mparent
		self.clients=[]
		self.xSize=0
		self.ySize=0
		self.openClient=-1
		self.overClient=-1
		self.openSize=openSize
		self.clkL=False
		self.resizing=False
		self.clkX=0
		self.clkY=0
		self.popenSize=0
		self.isCaptured = False
		#
		self.Bind(wx.EVT_SIZE,self.resize)
		self.Bind(wx.EVT_PAINT,self.repaint)
		self.Bind(wx.EVT_LEFT_DOWN,self.leftclick)
		self.Bind(wx.EVT_LEFT_UP,self.leftunclick)
		self.Bind(wx.EVT_MOTION,self.motion)
	
	def setOpenClient(self,cn):
		if cn==self.openClient:
			return
		if cn<-1 or cn>=len(self.clients):
			print "Invalid pane client index"
			return
		self.openClient=cn
		self._parent.resize()
		self.updateClients()
		if cn!=-1:
			self.clients[cn][1].SetFocus()
	
	def leftclick(self,evt):
		self.clkL=True
		if not self.isCaptured:
			self.CaptureMouse()
			self.isCaptured = True
		self.updateOver(evt)
		if self.overClient==-1:
			if self.openClient!=-1:
				if self.orientation==2:
					self.SetCursor(wx.StockCursor(wx.CURSOR_SIZENS))
				else:
					self.SetCursor(wx.StockCursor(wx.CURSOR_SIZEWE))
				pos=self.ClientToScreen(evt.GetPosition())
				self.clkX=pos.x
				self.clkY=pos.y
				self.popenSize=self.openSize
				self.resizing=True
			else:
				self.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))
		else:
			self.SetCursor(wx.StockCursor(wx.CURSOR_HAND))
	
	def leftunclick(self,evt):
		if self.isCaptured:
			self.ReleaseMouse()
			self.isCaptured = False
		self.clkL=False
		if self.overClient!=-1:
			if self.openClient==self.overClient:
				self.setOpenClient(-1)
			else:
				self.setOpenClient(self.overClient)
		self.resizing=False
		self.updateOver(evt)
	
	def motion(self,evt):
		if self.resizing:
			pos=self.ClientToScreen(evt.GetPosition())
			if self.orientation==0:
				self.openSize=self.popenSize+pos.x-self.clkX
			elif self.orientation==1:
				self.openSize=self.popenSize-pos.x+self.clkX
			elif self.orientation==2:
				self.openSize=self.popenSize-pos.y+self.clkY
			if self.openSize < 32:
				self.openSize = 32
			self._parent.resize()
		else:
			self.updateOver(evt)
			if self.overClient==-1:
				if self.openClient!=-1:
					if self.orientation==2:
						self.SetCursor(wx.StockCursor(wx.CURSOR_SIZENS))
					else:
						self.SetCursor(wx.StockCursor(wx.CURSOR_SIZEWE))
				else:
					self.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))
			else:
				self.SetCursor(wx.StockCursor(wx.CURSOR_HAND))

	def updateOver(self,evt):
		pos=evt.GetPosition()
		oover=self.overClient
		self.overClient=-1
		i=0
		for c in self.clients:
			r = self.clientRect(i)
			if pos.x>=r[0] and pos.x<r[0]+r[2] and pos.y>=r[1] and pos.y<r[1]+r[3]:
				self.overClient=i
			i+=1
		if self.overClient!=oover:
			self.Refresh()
		if self.overClient!=-1:
			if not self.isCaptured:
				self.CaptureMouse()
				self.isCaptured = True
		elif not self.clkL:
			if self.isCaptured:
				self.ReleaseMouse()
				self.isCaptured = False
	
	def addClient(self,cname,client):
		self.clients.append([cname,client])
		self.updateClients()
	
	def clientWRect(self):
		bx=0
		by=0
		sx=self.xSize-paneSize
		sy=self.ySize
		if self.orientation==1:
			bx=paneSize
		elif self.orientation==2:
			by=paneSize
			sx=self.xSize
			sy=self.ySize-paneSize
		return [ bx+1,by+1,sx-2,sy-2 ]
	
	def updateClients(self):
		i=0
		for c in self.clients:
			if i==self.openClient:
				c[1].Show(True)
				c[1].SetRect(self.clientWRect())
			else:
				c[1].Show(False)
			i+=1
	
	def resize(self,evt):
		size=evt.GetSize()
		self.xSize=size.x
		self.ySize=size.y
		self.Refresh()
		self.draw()
		self.updateClients()

	def repaint(self,evt):
		self.draw(wx.PaintDC(self))
	
	def clientRect(self,ind):
		ret=[ 1,0,paneSize,paneWidth+1 ]
		if self.orientation==0:
			ret[0]=self.xSize-paneSize-1
		elif self.orientation==2:
			ret[0]=0
			ret[1]=1
			ret[2]=paneWidth+1
			ret[3]=paneSize
		if self.orientation==2:
			ret[0]+=paneWidth*ind
		else:
			ret[1]+=paneWidth*ind
		return ret
	
	def draw(self,dc=None):
		if not dc:
			dc=wx.PaintDC(self)
		dc.SetFont(self.font)
		if self.openClient!=-1:
			dc.SetPen(wx.Pen(wx.NamedColour('black'),1))
			dc.SetBrush(wx.TRANSPARENT_BRUSH)
			r = self.clientWRect()
			rc = self.clientRect(self.openClient)
			dc.DrawRectangle(r[0]-1,r[1]-1,r[2]+2,r[3]+2)
		i=0
		for c in self.clients:
			r = self.clientRect(i)
			if i==self.overClient or i==self.openClient:
				dc.SetPen(wx.Pen(wx.NamedColour('black'),1))
				dc.SetBrush(wx.TRANSPARENT_BRUSH)
				dc.DrawRectangle(r[0],r[1],r[2],r[3])
				if self.orientation==2:
					dc.SetTextForeground(wx.Colour(0,0,0,wx.ALPHA_OPAQUE))
					for sx in xrange(-1,3):
						for sy in xrange(-1,2):
							if sx!=sy:
								dc.DrawText(c[0],r[0]+5+sx,r[1]+5+sy)
					dc.SetTextForeground(wx.Colour(255,255,255,wx.ALPHA_OPAQUE))
					dc.DrawText(c[0],r[0]+5,r[1]+5)
					dc.DrawText(c[0],r[0]+6,r[1]+5)
				else:
					dc.SetTextForeground(wx.Colour(0,0,0,wx.ALPHA_OPAQUE))
					for sx in xrange(-1,2):
						for sy in xrange(-1,3):
							if sx!=sy:
								dc.DrawRotatedText(c[0],r[0]+19+sx,r[1]+5+sy,-90)
					dc.SetTextForeground(wx.Colour(255,255,255,wx.ALPHA_OPAQUE))
					dc.DrawRotatedText(c[0],r[0]+19,r[1]+5,-90)
					dc.DrawRotatedText(c[0],r[0]+19,r[1]+6,-90)
			else:
				if self.orientation==2:
					dc.SetTextForeground(wx.Colour(255,255,255,wx.ALPHA_OPAQUE))
					for sx in xrange(-1,3):
						for sy in xrange(-1,2):
							if sx!=sy:
								dc.DrawText(c[0],r[0]+5+sx,r[1]+5+sy)
					dc.SetTextForeground(wx.Colour(0,0,0,wx.ALPHA_OPAQUE))
					dc.DrawText(c[0],r[0]+5,r[1]+5)
					dc.DrawText(c[0],r[0]+6,r[1]+5)
				else:
					dc.SetTextForeground(wx.Colour(255,255,255,wx.ALPHA_OPAQUE))
					for sx in xrange(-1,2):
						for sy in xrange(-1,3):
							if sx!=sy:
								dc.DrawRotatedText(c[0],r[0]+19+sx,r[1]+5+sy,-90)
					dc.SetTextForeground(wx.Colour(0,0,0,wx.ALPHA_OPAQUE))
					dc.DrawRotatedText(c[0],r[0]+19,r[1]+5,-90)
					dc.DrawRotatedText(c[0],r[0]+19,r[1]+6,-90)
			i+=1
	
	def cleanup(self,evt):
		pass


#####################################################
# Main frame

class newDialog(wx.Dialog):
	def __init__(self,parent,ID):
		wx.Dialog.__init__(self,parent,ID,"New",size=wx.DefaultSize,pos=wx.DefaultPosition,style=wx.DEFAULT_DIALOG_STYLE)
		sizer=wx.BoxSizer(wx.VERTICAL)
		
		box=wx.BoxSizer(wx.HORIZONTAL)
		label=wx.StaticText(self,-1,"X size")
		box.Add(label,0,wx.ALIGN_CENTRE|wx.ALL,5)
		self.xSizer=wx.SpinCtrl(self,10,"")
		self.xSizer.SetRange(1,1000)
		self.xSizer.SetValue(20)
		box.Add(self.xSizer,1,wx.ALIGN_CENTRE|wx.ALL,5)
		sizer.Add(box,0,wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL,5)

		box=wx.BoxSizer(wx.HORIZONTAL)
		label=wx.StaticText(self,-1,"Y size")
		box.Add(label,0,wx.ALIGN_CENTRE|wx.ALL,5)
		self.ySizer=wx.SpinCtrl(self,10,"")
		self.ySizer.SetRange(1,1000)
		self.ySizer.SetValue(32)
		box.Add(self.ySizer,1,wx.ALIGN_CENTRE|wx.ALL,5)
		sizer.Add(box,0,wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL,5)

		box=wx.BoxSizer(wx.HORIZONTAL)
		label=wx.StaticText(self,-1,"Z size")
		box.Add(label,0,wx.ALIGN_CENTRE|wx.ALL,5)
		self.zSizer=wx.SpinCtrl(self,10,"")
		self.zSizer.SetRange(1,1000)
		self.zSizer.SetValue(20)
		box.Add(self.zSizer,1,wx.ALIGN_CENTRE|wx.ALL,5)
		sizer.Add(box,0,wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL,5)
		
		btnsizer=wx.StdDialogButtonSizer()
		btn=wx.Button(self,wx.ID_OK)
		btn.SetDefault()
		btnsizer.AddButton(btn)

		btn=wx.Button(self,wx.ID_CANCEL)
		btnsizer.AddButton(btn)
		btnsizer.Realize()
		
		sizer.Add(btnsizer,0,wx.ALIGN_CENTER_VERTICAL|wx.ALL,5)
		
		self.SetSizer(sizer)
		sizer.Fit(self)


class voxelmapDataObject(wx.PyDataObjectSimple):
	def __init__(self,vLayer=None,vMask=None):
		wx.PyDataObjectSimple.__init__(self,wx.CustomDataFormat('Katachi3DVMap'))
		if(vLayer==None):
			self.data=""
		else:
			self.data=self.encode(vLayer,vMask)
		self.vMap=None
	def GetDataSize(self):
		if self.data==None:
			return 0
		return len(self.data)
	def GetVMap(self):
		if self.data=="":
			print "Empty data object"
			return
		if not self.vMap:
			self.vMap=self.decode(self.data)
		return self.vMap
	def GetDataHere(self):
		self.vMap=self.decode(self.data)
		return self.data
	def SetData(self,dat):
		self.data=dat
	def encode(self,vLayer,vMask):
		d=""
		vMap=vLayer.vMap
		xMax=0
		yMax=0
		zMax=0
		xMin=vMask.xSize-1
		yMin=vMask.ySize-1
		zMin=vMask.zSize-1
		for x in xrange( max(vLayer.xPos,0), min( vLayer.xPos+vMap.xSize,vMask.xSize ) ):
			for y in xrange( max(vLayer.yPos,0), min( vLayer.yPos+vMap.ySize,vMask.ySize ) ):
				for z in xrange( max(vLayer.zPos,0), min( vLayer.zPos+vMap.zSize,vMap.zSize ) ):
					if vMask.getPx([x,y,z])!=0 and vMap.getPx([x-vLayer.xPos,y-vLayer.yPos,z-vLayer.zPos])[3]!=0:
						xMin=min(x,xMin)
						yMin=min(y,yMin)
						zMin=min(z,zMin)
						xMax=max(x,xMax)
						yMax=max(y,yMax)
						zMax=max(z,zMax)
		xSize=xMax-xMin+1
		ySize=yMax-yMin+1
		zSize=zMax-zMin+1
		if xSize<=0 or ySize<=0 or zSize<=0:
			print "Empty selection"
			return ""
		d=struct.pack(">lll",xSize,ySize,zSize)
		for x in xrange(xMin,xMax+1):
			for y in xrange(yMin,yMax+1):
				for z in xrange(zMin,zMax+1):
					t=[0,0,0,0]
					if vMask.getPx([x,y,z]):
						t=vMap.getPx([x-vLayer.xPos,y-vLayer.yPos,z-vLayer.zPos])
					d+=struct.pack(">BBBB",t[0],t[1],t[2],t[3])
		return d
	def decode(self,d):
		if len(d)==0:
			print "Empty data object"
			return None
		offs=struct.calcsize(">III")
		xs,ys,zs = struct.unpack(">III",d[:offs])
		ret=voxelmap(xs,ys,zs)
		for x in xrange(xs):
			for y in xrange(ys):
				for z in xrange(zs):
					noffs=offs+struct.calcsize(">BBBB")
					r,g,b,a=struct.unpack(">BBBB",d[offs:noffs])
					offs=noffs
					ret.setPx([x,y,z],[r,g,b,a])
		return ret


class mainFrame(wx.Frame):
	def __init__(self,prj):
#		wx.Frame.__init__(self,None,-1,"Katachi3D - By Bjørn André Bredesen, 2013",size=(1400,1000),style=wx.DEFAULT_FRAME_STYLE)
		#wx.Frame.__init__(self,None,-1,"Katachi3D - By Bjørn Bredesen, 2013",size=(1400,1000),style=wx.DEFAULT_FRAME_STYLE)
		wx.Frame.__init__(self,None,-1,"Katachi3D",size=(1400,1000),style=wx.DEFAULT_FRAME_STYLE)
		self.hasChanged=False
		self.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))
		self.control=False
		makeBGBitmap(wx.ClientDC(self))
		self.prj=prj
		self.basepath=os.path.dirname(os.path.realpath(__file__))
		resbase=self.basepath+"/res/"
		self.SetIcon( wx.Icon( resbase+"icon.png", wx.BITMAP_TYPE_PNG ) )
		#
		self.path=False
		self.penColour = [100,100,100,255]
		self.cpenSize = 3
		self.tool = 4
		self.singleLayer = False
		self.useLight=True
		# Menu
		self.CreateStatusBar()
		tb=self.toolbar=self.CreateToolBar(wx.TB_HORIZONTAL|wx.NO_BORDER|wx.TB_FLAT)
		tsize = (24,24)
		filemenu=wx.Menu()
		editmenu=wx.Menu()
		bar=wx.MenuBar()
		bar.Append(filemenu,"&File")
		bar.Append(editmenu,"&Edit")
		self.SetMenuBar(bar)
		
		filemenu.Append(wx.ID_NEW,"&New","Creates a new project")
		tb.AddLabelTool(wx.ID_NEW,"New",wx.ArtProvider.GetBitmap(wx.ART_NEW,wx.ART_TOOLBAR,tsize),shortHelp="New",longHelp="Creates a new project.")
		self.Bind(wx.EVT_MENU,self.newFile,id=wx.ID_NEW)
		self.Bind(wx.EVT_TOOL,self.newFile,id=wx.ID_NEW)
		
		filemenu.Append(wx.ID_OPEN,"&Open ...","Opens a project")
		tb.AddLabelTool(wx.ID_OPEN,"Open ...",wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN,wx.ART_TOOLBAR,tsize),shortHelp="Open",longHelp="Opens a project.")
		self.Bind(wx.EVT_MENU,self.openFile,id = wx.ID_OPEN)
		self.Bind(wx.EVT_TOOL,self.openFile,id=wx.ID_OPEN)

		filemenu.Append(wx.ID_SAVE,"&Save","Saves the current project")
		tb.AddLabelTool(wx.ID_SAVE,"Save",wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE,wx.ART_TOOLBAR,tsize),shortHelp="Save",longHelp="Saves the current project.")
		self.Bind(wx.EVT_MENU,self.saveFile,id = wx.ID_SAVE)
		self.Bind(wx.EVT_TOOL,self.saveFile,id=wx.ID_SAVE)
		
		filemenu.Append(wx.ID_SAVEAS,"Save &as ...","Saves the current project to a diffent file")
		tb.AddLabelTool(wx.ID_SAVEAS,"Save as ...",wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE_AS,wx.ART_TOOLBAR,tsize),shortHelp="Save",longHelp="Saves the current project to a diffent file.")
		self.Bind(wx.EVT_MENU,self.saveFileAs,id = wx.ID_SAVEAS)
		self.Bind(wx.EVT_TOOL,self.saveFileAs,id=wx.ID_SAVEAS)

		tb.AddSeparator()
		editmenu.Append(wx.ID_UNDO,"&Undo\tCtrl+Z","Undo last drawing operation")
		tb.AddLabelTool(wx.ID_UNDO,"Undo",wx.ArtProvider.GetBitmap(wx.ART_UNDO,wx.ART_TOOLBAR,tsize),shortHelp="Undo",longHelp="Undo last drawing operation.")
		self.Bind(wx.EVT_MENU,self.undo,id = wx.ID_UNDO)
		self.Bind(wx.EVT_TOOL,self.undo,id=wx.ID_UNDO)
		editmenu.Append(wx.ID_REDO,"&Redo\tCtrl+Shift+Z","Redo last undone drawing operation")
		tb.AddLabelTool(wx.ID_REDO,"Redo",wx.ArtProvider.GetBitmap(wx.ART_REDO,wx.ART_TOOLBAR,tsize),shortHelp="Redo",longHelp="Redo last undone drawing operation.")
		self.Bind(wx.EVT_MENU,self.redo,id = wx.ID_REDO)
		self.Bind(wx.EVT_TOOL,self.redo,id=wx.ID_REDO)

		editmenu.AppendSeparator()
		tb.AddSeparator()
		editmenu.Append(wx.ID_CUT,"C&ut","Cuts the selection to the clipboard")
		tb.AddLabelTool(wx.ID_CUT,"Cut",wx.ArtProvider.GetBitmap(wx.ART_CUT,wx.ART_TOOLBAR,tsize),shortHelp="Cut",longHelp="Cuts the selection to the clipboard.")
		self.Bind(wx.EVT_MENU,self.cut,id = wx.ID_CUT)
		self.Bind(wx.EVT_TOOL,self.cut,id=wx.ID_CUT)
		editmenu.Append(wx.ID_COPY,"&Copy","Copies the selection to the clipboard")
		tb.AddLabelTool(wx.ID_COPY,"Copy",wx.ArtProvider.GetBitmap(wx.ART_COPY,wx.ART_TOOLBAR,tsize),shortHelp="Copy",longHelp="Copies the selection to the clipboard.")
		self.Bind(wx.EVT_MENU,self.copy,id = wx.ID_COPY)
		self.Bind(wx.EVT_TOOL,self.copy,id=wx.ID_COPY)
		editmenu.Append(wx.ID_PASTE,"&Paste","Pastes from the clipboard")
		tb.AddLabelTool(wx.ID_PASTE,"Paste",wx.ArtProvider.GetBitmap(wx.ART_PASTE,wx.ART_TOOLBAR,tsize),shortHelp="Paste",longHelp="Pastes from the clipboard.")
		self.Bind(wx.EVT_MENU,self.paste,id = wx.ID_PASTE)
		self.Bind(wx.EVT_TOOL,self.paste,id=wx.ID_PASTE)
		editmenu.AppendSeparator()
		tb.AddSeparator()
		editmenu.Append(1000,"Select &all\tCtrl+A","Selects the whole layer area")
		self.Bind(wx.EVT_MENU,self.selectAll,id = 1000)
		editmenu.Append(1001,"C&lear\tDelete","Clears the selected area")
		self.Bind(wx.EVT_MENU,self.clearSelection,id = 1001)

		editmenu.AppendSeparator()
		editmenu.Append(40,"&Add layer","Add another layer")
		self.Bind(wx.EVT_MENU,self.addLayer,id = 40)
		
		filemenu.AppendSeparator()
		eAbout=filemenu.Append(wx.ID_ABOUT,"&About","About this application")
		self.Bind(wx.EVT_MENU,self.about,eAbout)
		eExit=filemenu.Append(wx.ID_EXIT,"E&xit","Closes the application")
		self.Bind(wx.EVT_MENU,self.bye,eExit)
		self.Bind(wx.EVT_CLOSE,self.bye)

		# TB
		tb.AddSeparator()
		
		tb.AddRadioLabelTool(20,"Select",wx.Bitmap(resbase+"select.png",wx.BITMAP_TYPE_PNG),shortHelp="Select",longHelp="Selector tool.")
		self.Bind(wx.EVT_TOOL,self.toolSelect,id=20)
		tb.AddRadioLabelTool(21,"Pick colour",wx.Bitmap(resbase+"colourpicker.png",wx.BITMAP_TYPE_PNG),shortHelp="Pick colour",longHelp="Colour picker tool.")
		self.Bind(wx.EVT_TOOL,self.toolColour,id=21)
		tb.AddRadioLabelTool(22,"Pen",wx.Bitmap(resbase+"pen.png",wx.BITMAP_TYPE_PNG),shortHelp="Pen",longHelp="Pen tool. Draws points. Hold shift to erase. Hold ctrl to pick colours.")
		self.Bind(wx.EVT_TOOL,self.toolPen,id=22)
		tb.AddRadioLabelTool(23,"2D-brush",wx.Bitmap(resbase+"brush2D.png",wx.BITMAP_TYPE_PNG),shortHelp="2D-brush",longHelp="2D-brush tool. The brush is a circle of the specified size. Hold shift to erase. Hold ctrl to pick colours.")
		self.Bind(wx.EVT_TOOL,self.tool2DBrush,id=23)
		tb.AddRadioLabelTool(24,"3D-brush",wx.Bitmap(resbase+"brush3D.png",wx.BITMAP_TYPE_PNG),shortHelp="3D-brush",longHelp="3D-brush tool. The brush is a sphere of the specified size. Hold shift to erase. Hold ctrl to pick colours.")
		self.Bind(wx.EVT_TOOL,self.tool3DBrush,id=24)
		tb.AddRadioLabelTool(25,"2D-fill",wx.ArtProvider.GetBitmap(wx.ART_NEW,wx.ART_TOOLBAR,tsize),shortHelp="2D-fill",longHelp="2D-fill tool. Flood fills in two dimensions. Hold shift to erase. Hold ctrl to pick colours.")
		self.Bind(wx.EVT_TOOL,self.tool2DFill,id=25)
		tb.AddRadioLabelTool(26,"3D-fill",wx.ArtProvider.GetBitmap(wx.ART_NEW,wx.ART_TOOLBAR,tsize),shortHelp="3D-fill",longHelp="3D-fill tool. Flood fills in three dimensions. Hold shift to erase. Hold ctrl to pick colours.")
		self.Bind(wx.EVT_TOOL,self.tool3DFill,id=26)
		
		tb.ToggleTool(20+self.tool,True)
		
		tb.AddSeparator()
#		tb.AddControl( wx.StaticText(tb,-1,"Colour: ") )
		self.colSelect=csel.ColourSelect(tb,-1,"",self.penColour)
		self.Bind(csel.EVT_COLOURSELECT,self.colourSelect,self.colSelect)
		tb.AddControl( self.colSelect )
		
		# Panes
		self.leftPane=paneWin(self,self,-1,0,200)
		self.rightPane=paneWin(self,self,-1,1,280)
		self.bottomPane=paneWin(self,self,-1,2,200)
		
		self.layerwin=layerWin(self,self.leftPane,-1,prj)
		self.leftPane.addClient("Layers",self.layerwin)
		
		self.propertieswin=propertiesWin(self,self.rightPane,-1)
		self.rightPane.addClient("Properties",self.propertieswin)
		
		self.bottomPane.addClient("Python shell",py.shell.Shell(self.bottomPane,-1,
			introText="------------------------------------------------------\n\tKatachi3D\n\tBy Bjørn André Bredesen, 2013\n------------------------------------------------------\nThe open project can be accessed via 'frame.prj'. After making changes to the project, 'frame.ProjectChanged()' can be called to refresh.\n------------------------------------------------------"))
		#
		self.Bind(wx.EVT_SASH_DRAGGED_RANGE,self.sashD)
		self.Bind(wx.EVT_SIZE,self.onsize)
		#
		self.control=voxelmapEdit(self,self,-1,prj)
		#
		self.propertieswin.setLayer(0)
		#
		self.clearEditHistory()
		self.Show(True)
		
		self.GenerateClients()

	def colourSelect(self,evt):
		r=self.colSelect.GetValue()
		if(len(r)==3):
			self.penColour=[r[0],r[1],r[2],255]
		elif(len(r)==4):
			self.penColour=[r[0],r[1],r[2],r[3]]

	def EHCandidateActiveLayer(self):
		self.EHCandidate=EHLayer(self.prj.layers[self.prj.activeLayer],self.prj.activeLayer)
	
	def EHCandidateProject(self):
		self.EHCandidate=EHProject(self.prj)
		
	def EHAddCandidate(self):
		if self.EHCandidate==None:
			print "No edit history candidate"
			return
		self.EHUndo.append(self.EHCandidate)
		self.EHRedo=[]
		self.EHClearCandidate()
		self.ProjectChanged()
		
	def EHClearCandidate(self):
		self.EHCandidate=None
	
	def RefreshClients(self):
#		print "DBG: Refresh clients"
		self.layerwin.Refresh()
		self.control.RefreshClients()
	
	def GenerateClients(self):
#		print "DBG: Generate clients"
		self.control.GenerateClients()
		self.RefreshClients()
	
	def ProjectChanged(self):
		print "DBG: Project changed"
		self.hasChanged=True
		self.GenerateClients()
	
	def undo(self,evt):
		if len(self.EHUndo)==0:
			print "Empty undo list"
			return
		self.EHRedo.append(self.EHUndo.pop().use(self))
		self.ProjectChanged()
#		print "Undo size after undo operation: ",len(self.EHUndo)
		
	def redo(self,evt):
		if len(self.EHRedo)==0:
			print "Empty redo list"
			return
		self.EHUndo.append(self.EHRedo.pop().use(self))
		self.ProjectChanged()
#		print "Redo size after redo operation: ",len(self.EHRedo)
	
	def clearEditHistory(self):
		self.EHUndo=[]
		self.EHRedo=[]
		self.hasChanged=False
		self.EHCandidate=None
	
	def clearSelection(self,evt):
		self.control.emptySelection()
		
	def selectAll(self,evt):
		self.control.selectAll()
	
	def copy(self,evt):
		if (not self.prj.selMask) or self.prj.selMask.empty:
			print "Nothing to copy"
			return
		if wx.TheClipboard.IsOpened():
			print "Clipboard already opened"
			return
		wx.TheClipboard.Open()
		vmo=voxelmapDataObject(self.prj.layers[self.prj.activeLayer],self.prj.selMask)
		wx.TheClipboard.SetData(vmo)
		wx.TheClipboard.Close()
	def cut(self,evt):
		self.copy(None)
		self.control.emptySelection()
	def paste(self,evt):
		wx.TheClipboard.Open()
		vmo=voxelmapDataObject()
		if not wx.TheClipboard.GetData(vmo):
			print "Could not obtain data in the correct format."
			wx.TheClipboard.Close()
			return
		vMap=vmo.GetVMap()
		if vMap==None:
			print "Could not obtain data in the correct format."
			wx.TheClipboard.Close()
			return
		self.prj.clipboard=voxelLayer("Clipboard",vMap)
		self.prj.clipboard.xPos=int(self.control.cX-vMap.xSize/2)
		self.prj.clipboard.yPos=int(self.control.cY-vMap.ySize/2)
		self.prj.clipboard.zPos=int(self.control.cZ-vMap.zSize/2)
		self.control.clearSelection()
		self.control.RefreshClients()
		wx.TheClipboard.Close()
	
	def addLayer(self,evt):
		self.EHCandidateProject() # XXX TEMPORARY! Replace with simpler layer removal operation
		self.prj.newLayer("Layer "+str(len(self.prj.layers)+1))
		self.EHAddCandidate()
	
	def makeSure(self,action):
		if self.hasChanged:
			dlg=wx.MessageDialog(self,
				"There are unsaved changes to the project. Are you sure you want to "+action+"?",
				"Unsaved changes", wx.OK|wx.CANCEL|wx.ICON_QUESTION)
			result = dlg.ShowModal()
			dlg.Destroy()
			if result == wx.ID_OK:
				return True
			else:
				return False
		else:
			return True
	
	def new(self):
		dlg=newDialog(self,-1)
		val=dlg.ShowModal()
		if val==wx.ID_OK:
			global project
			project=voxelImage(dlg.xSizer.GetValue(),dlg.ySizer.GetValue(),dlg.zSizer.GetValue())
			project.newLayer("Layer 1")
			self.setProject(project)
			self.prj.dbgout()
			self.resize()
			self.setLayer(0)
			self.clearEditHistory()
			self.GenerateClients()
			self.path=False
			return True
		else:
			return False
	
	def setProject(self,prj):
		self.prj=prj
		self.control.setProject(prj)
		self.layerwin.setProject(prj)
		self.propertieswin.setProject(prj)
		
	def setLayer(self,layer):
		if layer<0 or layer>=len(self.prj.layers):
			print "Invalid layer"
			return
		self.prj.activeLayer=layer
		self.control.setLayer(layer)
		self.layerwin.setLayer(layer)
		self.propertieswin.setLayer(layer)
		
	def setColour(self,col):
		if len(col)>=3:
			c=[col[0],col[1],col[2]]
		self.colSelect.SetValue(c)
		self.penColour=[col[0],col[1],col[2],255]
	def toolSelect(self,evt):
		self.tool=0
	def toolColour(self,evt):
		self.tool=1
	def toolPen(self,evt):
		self.tool=2
	def tool2DBrush(self,evt):
		self.tool=3
	def tool3DBrush(self,evt):
		self.tool=4
	def tool2DFill(self,evt):
		self.tool=5
	def tool3DFill(self,evt):
		self.tool=6
	def penSize(self,evt):
		self.cpenSize=self.penSizer.GetValue()
	def colourSelect(self,evt):
		r=self.colSelect.GetValue()
		global penColour
		if(len(r)==3):
			self.penColour=[r[0],r[1],r[2],255]
		elif(len(r)==4):
			self.penColour=[r[0],r[1],r[2],r[3]]
	def sashD(self,evt):
		if evt.GetId()==ID_LWIN:
			self.lwin.SetDefaultSize((evt.GetDragRect().width, 1000))
		if evt.GetId()==ID_RWIN:
			self.rwin.SetDefaultSize((evt.GetDragRect().width, 1000))
		wx.LayoutAlgorithm().LayoutMDIFrame(self)
		self.GetClientWindow().Refresh()
	
	def onsize(self,evt):
		self.resize()
	
	def resize(self):
		s=self.GetClientSize()
		lps=paneSize
		if self.leftPane.openClient!=-1:
			lps+=self.leftPane.openSize
		rps=paneSize
		if self.rightPane.openClient!=-1:
			rps+=self.rightPane.openSize
		bps=paneSize
		if self.bottomPane.openClient!=-1:
			bps+=self.bottomPane.openSize
		if self.control:
			self.control.SetRect([ lps+paneMargin, 0, s.x-paneMargin*2-lps-rps, s.y-bps-paneMargin ])
		self.leftPane.SetRect([ 0, 0, lps, s.y ])
		self.rightPane.SetRect([ s.x-rps, 0, rps, s.y ])
		self.bottomPane.SetRect([ lps+paneMargin, s.y-bps, s.x-paneMargin*2-lps-rps, bps ])
	
	def about(self,evt):
		dlg=wx.MessageDialog(self,"Katachi3D\n\nBy Bjørn André Bredesen, 2013\n------------------------------------------------\nKatachi3D is a voxel graphics editor. It has been designed for use in personal game development projects.\n------------------------------------------------\nQuick help:\n\tVertical scroll: Mouse wheel\n\tHorizontal scroll: Mouse wheel + Shift\n\tDepth scroll: Mouse wheel + Alt\n\tZoom: Mouse wheel + Ctrl\n\tPick colour: Drawing tool + Click + Ctrl\n\tErase: Drawing tool + Click + Shift\n\tTab (in viewport): Brings focus to next viewport\n\n\tShift+Tab (in viewport): Brings focus to previous viewport\n\tX (in viewport): Maximized/minimized viewport\n\tC (in viewport): Open colour picker\n\tQ (in viewport): Increase tool size\n\tA (in viewport): Decrease tool size\n\tCtrl+left (in viewport): Focus to layers\n\tCtrl+right (in viewport): Focus to properties\n\tCtrl+down (in viewport): Focus to python shell","About",wx.OK)
		dlg.ShowModal()
		dlg.Destroy()
		
	def bye(self,evt):
		if self.makeSure("exit"):
			self.Destroy()
		
	def newFile(self,evt):
		if self.makeSure("start a new project"):
			self.new()
		
	def openFile(self,evt):
		if self.makeSure("open a file"):
			dirname=self.basepath
			dlg=wx.FileDialog(self,"Open",dirname,"","Katachi3D graphics (*.k3d)|*.k3d|All files|*.*",wx.OPEN)
			if dlg.ShowModal()==wx.ID_OK:
				filename=dlg.GetFilename()
				dirname=dlg.GetDirectory()
				fpath=os.path.join(dirname,filename)
				lprj=voxelImage(1,1,1)
				lprj.load(fpath)
				self.path=fpath
				self.setProject(lprj)
				self.clearEditHistory()
				self.GenerateClients()
			dlg.Destroy()
	
	def saveProject(self,_as):
		path=False
		dirname=self.basepath
		if not _as:
			path=self.path
		if not path:
			dlg=wx.FileDialog(self,"Save as",dirname,"","Katachi3D graphics (*.k3d)|*.k3d",wx.SAVE|wx.FD_OVERWRITE_PROMPT)
			if dlg.ShowModal()==wx.ID_OK:
				filename=dlg.GetFilename()
				dirname=dlg.GetDirectory()
				path=os.path.join(dirname,filename)
			dlg.Destroy()
		if path:
			self.prj.save(path)
			self.path=path
			self.hasChanged=False
	
	def saveFile(self,evt):
		self.saveProject(False)

	def saveFileAs(self,evt):
		self.saveProject(True)


#####################################################
# Entry

print "------------------------------------------------------"
print "\tKatachi3D"
print "\tBy Bjørn Bredesen, 2013"
print "\tE-mail: contact@bjornbredesen.no"
print "------------------------------------------------------"
print "Please see 'About' for instructions."
print "------------------------------------------------------"

project=voxelImage(20,32,20)
project.newLayer("Layer 1")

app=wx.App(False)
frame=mainFrame(project)
app.MainLoop()

