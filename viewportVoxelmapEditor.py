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
import time

# Internal
from Katachi3Dlib import *
from extra import *


#####################################################
# Voxel editor

# Axes:
#	Z-axis: X/Y for editing, stepping through Z
#	X-axis: Z/Y for editing, stepping through X
#	Y-axis: X/Z for editing, stepping through Y
axisName=["Z-axis","X-axis","Y-axis"]

class viewportVoxelmapEditor(wx.Window):
	def __init__(self,parent,ID,prj,axis=2,zoom=8):
		wx.Window.__init__(self,parent,ID,pos=wx.DefaultPosition,size=wx.DefaultSize)
		self.SetCursor(wx.Cursor(wx.CURSOR_PENCIL))
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
		self.bgDC = makeBGBitmap(wx.ClientDC(self))
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
			print("Invalid layer")
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
					for cx in range(minX,maxX):
						for cy in range(minY,maxY):
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
		elif kc==wx.WXK_PAGEDOWN:
			self.setZ(max(min(self.zInd+1,limits[2]-1),0))
			self._parent.RefreshClientsActive()
			if self._parent._parent.tool==0 and self.clkMode==0 and self.clkL:
				self.czb=self.zInd
				self.updateSelRect()
			else:
				self.Refresh()
		elif kc==wx.WXK_PAGEUP:
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
		try:
			self.draw(wx.AutoBufferedPaintDCFactory(self))
		except wx._core.wxAssertionError as e:
			print('Exception: ' + str(e))
	
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
			for x in range(max(0,-pos[0]),min(limits[0],plimits[0]-pos[0])):
				for y in range(max(0,-pos[1]),min(limits[1],plimits[1]-pos[1])):
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
							dc.SetPen(wx.Pen(wx.Colour('white'),1,wx.DOT))
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
			try:
				dc = wx.AutoBufferedPaintDCFactory(self)
			except wx._core.wxAssertionError as e:
				#print('Exception: ' + str(e))
				return
		dc.SetFont(self.font)
		#
		zoom=self.zoom
		dc.SetPen(wx.Pen(wx.Colour('black'),1))
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
		dc.Blit(_wx,_wy,_wxs,_wys,self.bgDC,0,0)
		dc.DrawRectangle(x1-1,y1-1,pxs+2,pys+2)
		dc.DrawRectangle(x1-2-self.zoom-8,z1-1,self.zoom+2,pzs+2)

		dc.DrawRectangle(x1-1+pos[0]*zoom,y1-1+pos[1]*zoom,xs+2,ys+2)
		dc.DrawRectangle(x1-2-self.zoom-8,z1-1+pos[2]*zoom,self.zoom+2,zs+2)
		#
		dc.SetBrush(wx.Brush(wx.Colour('red')))
		dc.DrawRectangle(x1-self.zoom-10,z1-1+self.zInd*self.zoom,self.zoom+2,self.zoom+2)
		#
		dc.SetBrush(wx.Brush(wx.Colour('grey')))
		#
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
			dc.SetPen(wx.Pen(wx.Colour('white'),1,wx.DOT))
			dc.SetBrush(wx.TRANSPARENT_BRUSH)
			for x in range(plimits[0]):
				for y in range(plimits[1]):
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
			dc.SetPen(wx.Pen(wx.Colour('white'),1,wx.DOT))
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
	def generate(self):
		pass



