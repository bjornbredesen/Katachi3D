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
# Voxel map

class voxelmask():
	def __init__(self,xSize,ySize,zSize):
		self.xSize=xSize
		self.ySize=ySize
		self.zSize=zSize
		self.vMap=array.array('B',[0]*xSize*ySize*zSize)
		self.clear()
	def clear(self):
		for i in range(self.xSize*self.ySize*self.zSize):
			self.vMap[i]=0
		self.empty=True
	def setPx(self,pos,col):
		if len(pos)!=3:
			print("Illegal voxelmask drawing parameters")
			return
		x=pos[0]
		y=pos[1]
		z=pos[2]
		if x<0 or x>=self.xSize or y<0 or y>=self.ySize or z<0 or z>=self.zSize:
			print("Illegal voxelmap point")
			return
		self.vMap[z*self.ySize*self.xSize+y*self.xSize+x]=col
		self.empty=False
	def getPx(self,pos):
		if self.empty:
			return 0
		if len(pos)!=3:
			print("Illegal voxelmap coordinates")
			return []
		x=pos[0]
		y=pos[1]
		z=pos[2]
		if x<0 or x>=self.xSize or y<0 or y>=self.ySize or z<0 or z>=self.zSize:
			print("Illegal voxelmap point")
			return
		return self.vMap[z*self.ySize*self.xSize+y*self.xSize+x]
	def dbgout(self):
		print("voxelmask:")
		print("\txSize=",self.xSize)
		print("\tySize=",self.ySize)
		print("\tzSize=",self.zSize)

class voxelmap():
	def __init__(self,xSize,ySize,zSize):
		self.xSize=xSize
		self.ySize=ySize
		self.zSize=zSize
		self.vMap=array.array('B',[0]*xSize*ySize*zSize*4)
		self.clear()
	def clear(self):
		for i in range(self.xSize*self.ySize*self.zSize*4):
			self.vMap[i]=0
	def setPx(self,pos,col):
		if len(pos)!=3 or len(col)!=4:
			print("Illegal voxelmap drawing parameters")
			return
		x=pos[0]
		y=pos[1]
		z=pos[2]
		if x<0 or x>=self.xSize or y<0 or y>=self.ySize or z<0 or z>=self.zSize:
			print("Illegal voxelmap point")
			return
		offs=(z*self.ySize*self.xSize+y*self.xSize+x)*4
		self.vMap[offs+0]=col[0]
		self.vMap[offs+1]=col[1]
		self.vMap[offs+2]=col[2]
		self.vMap[offs+3]=col[3]
	def getPx(self,pos):
		if len(pos)!=3:
			print("Illegal voxelmap drawing parameters")
			return []
		x=pos[0]
		y=pos[1]
		z=pos[2]
		if x<0 or x>=self.xSize or y<0 or y>=self.ySize or z<0 or z>=self.zSize:
			print("Illegal voxelmap point")
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
		for x in range( dxA,dxB ):
			sy=dyA-destPos[1]
			for y in range( dyA,dyB ):
				sz=dzA-destPos[2]
				for z in range( dzA,dzB ):
					spx = vMapSource.getPx([ sx, sy, sz ])
					if spx[3]!=0:
						self.setPx([ x, y, z ],spx)
					sz+=1
				sy+=1
			sx+=1
	
	def clone(self):
		ret=voxelmap(self.xSize,self.ySize,self.zSize)
		for i in range(self.xSize*self.ySize*self.zSize*4):
			ret.vMap[i]=self.vMap[i]
		return ret
	
	def dbgout(self):
		print("voxelmap:")
		print("\txSize=",self.xSize)
		print("\tySize=",self.ySize)
		print("\tzSize=",self.zSize)


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
		b.write(b'K3DGv001')
		# Write basic info
		b.write(struct.pack(">IIII",self.xSize,self.ySize,self.zSize,len(self.layers)))
		for l in self.layers:
			b.write(struct.pack(">IIII",l.vMap.xSize,l.vMap.ySize,l.vMap.zSize,len(l.name)))
			b.write(l.name.encode('UTF-8'))
			b.write(struct.pack(">iiiiiiiiii",l.xPos,l.yPos,l.zPos,l.renderMode,l.nSubSurface,l.material,l.normalTolerance,int(l.cartoon),l.smoothPasses,l.smoothRadius))
			# Write voxels
			for j in range(l.vMap.xSize*l.vMap.ySize*l.vMap.zSize*4):
				b.write( struct.pack(">B",l.vMap.vMap[j]) )
		b.close()
		
	def load(self,path):
		# Open and make sure it is compatible.
		with open(path, 'rb') as b:
			s = b.read(4)
			if s.decode('UTF-8')!='K3DG':
				print("Not a Katachi3D graphics file")
				return False
			v=b.read(4)
			if v.decode('UTF-8')=="v001":
				#print("Katachi3D version 0.001 graphics file")
				pass
			else:
				print("Unsupported file version")
				return False
			# Read basic info
			xs,ys,zs,nl = struct.unpack(">IIII",b.read(struct.calcsize(">IIII")))
			#print("\txSize = ",xs)
			#print("\tySize = ",ys)
			#print("\tzSize = ",zs)
			#print("\t# layers = ",nl)
			self.layers=[]
			self.xSize=xs
			self.ySize=ys
			self.zSize=zs
			# Read layers
			for i in range(nl):
				lxs,lys,lzs,nlen = struct.unpack(">IIII",b.read(struct.calcsize(">IIII")))
				lname = ""
				if nlen>0:
					lname = b.read(nlen)
				#print("\tLayer \"",lname,"\"")
				#print("\t\txSize = ",lxs)
				#print("\t\tySize = ",lys)
				#print("\t\tzSize = ",lzs)
				xPos,yPos,zPos,renderMode,nSubSurface,material,normalTolerance,cartoon,smoothPasses,smoothRadius=struct.unpack(">iiiiiiiiii",b.read(struct.calcsize(">iiiiiiiiii")))
				# Read voxels
				vm = voxelmap(lxs,lys,lzs)
				for j in range(lxs*lys*lzs*4):
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
			self.selMask=voxelmask(self.xSize,self.ySize,self.zSize)
		return True
		
	def clone(self):
		ret=voxelImage(self.xSize,self.ySize,self.zSize)
		ret.activeLayer=self.activeLayer
		for l in self.layers:
			ret.layers.append(l.clone())
		return ret
	
	def dbgout(self):
		print("Voxel image:")
		print("\txSize=",self.xSize)
		print("\tySize=",self.ySize)
		print("\tzSize=",self.zSize)
		for l in self.layers:
			print("\tLayer \"",l.name,"\":")
			print("\t\txSize=",l.vMap.xSize)
			print("\t\tySize=",l.vMap.ySize)
			print("\t\tzSize=",l.vMap.zSize)


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
		print("Model:")
		print(" - Center: ",self.center.x,", ",self.center.y,", ",self.center.z)
		print(" - Meshes[",(len(self.meshes)),"]")
		for m in self.meshes:
			m.dbgout()




