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

# Internal
from Katachi3Dlib import *
from extra import *
from project import *


#####################################################
# OpenGL view

class viewportVoxelmapOpenGL(glcanvas.GLCanvas):
	def __init__(self,parent,ID,prj,zoom=8):
		#glcanvas.GLCanvas.__init__(self,parent,attribList=(glcanvas.WX_GL_RGBA, glcanvas.WX_GL_DOUBLEBUFFER))
		glcanvas.GLCanvas.__init__(self, parent, -1,attribList=[glcanvas.WX_GL_RGBA, glcanvas.WX_GL_DOUBLEBUFFER, WX_GL_DEPTH_SIZE,16,0,0])
		self.context = glcanvas.GLContext(self)
		self.init=False
		self.mdl=None
		self.calllist=None
		self.calllistm=None
		self.SetCursor(wx.Cursor(wx.CURSOR_PENCIL))
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
		self.Refresh(eraseBackground=False)	
	
	def setProject(self,prj):
		self.prj=prj
		self.setLayer(prj.activeLayer)
		
	def setLayer(self,layer):
		if layer<0 or layer>=len(self.prj.layers):
			print("Invalid layer")
			return
		self.layer=self.prj.layers[self.prj.activeLayer]
		self.vm=self.layer.vMap
	
	def cleanup(self,evt):
		pass
		
	def sfocus(self,evt):
		self._focus=True
		self.Refresh(eraseBackground=False)
	def kfocus(self,evt):
		self._focus=False
		self.Refresh(eraseBackground=False)
	
	def RefreshActive(self):
		self.Refresh(eraseBackground=False)
	
	def wheel(self,evt):
		d=evt.GetWheelRotation()
		if wx.GetKeyState(wx.WXK_CONTROL):
			self.zScroll-=d*0.01
			self.Refresh(eraseBackground=False)
		elif wx.GetKeyState(wx.WXK_SHIFT):
			self.xScroll-=d*0.01
			self.Refresh(eraseBackground=False)
		else:
			self.yScroll-=d*0.01
			self.Refresh(eraseBackground=False)
		
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
		self.Refresh(eraseBackground=False)
		
	def repaint(self,evt):
		if self.drawing:
			return
		self.draw()
	
	def draw(self):
		if not self.mdl or self.drawing:
			return
		self.drawing=True
		self.SetCurrent(self.context)
		glFlush()
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
			#c=wx.Colour(wx.SYS_COLOUR_WINDOW)
			c=wx.SystemSettings.GetColour(wx.SYS_COLOUR_MENU)
			#print(c)
			glClearColor(c[0]/256.,c[1]/256.,c[2]/256.,0)
			glEnable(GL_CULL_FACE);
			glCullFace(GL_FRONT);
			glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA)
			glEnable(GL_BLEND)
		
			glLightfv(GL_LIGHT0,GL_AMBIENT,(0.1,0.1,0.1,1))
			glLightfv(GL_LIGHT0,GL_DIFFUSE,(0.1,0.1,0.1,1))
			glLightfv(GL_LIGHT0,GL_CONSTANT_ATTENUATION,(0.3))
			glLightfv(GL_LIGHT0,GL_LINEAR_ATTENUATION,(0.02))
			glLightfv(GL_LIGHT0,GL_POSITION,(-self.prj.xSize,-self.prj.ySize,-self.prj.zSize,-18.0))
		
		#c=wx.SystemSettings.GetColour(wx.SYS_COLOUR_MENU)
		#glClearColor(c[0]/256.,c[1]/256.,c[2]/256.,0)
		glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
		glDisable(GL_CULL_FACE)
		glEnable(GL_DEPTH_TEST)
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
		#################################
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
			
			#print("DBG: OpenGL list generation time: ",(time.time()-time0))
			
		if self.calllist:
			glCallList(self.calllist)
		#################################
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
				self.SetCurrent(self.context)
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
				self.SetCurrent(self.context)
				glDeleteLists(self.calllist,1)
				self.calllist=None
		
		#print(" - DBG: Model generation")
		#print(" - - time: ",(time.time()-time0))

