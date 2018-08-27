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
from editHistory import *


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
		self.Bind(wx.EVT_MOUSE_CAPTURE_LOST,self.captureLost)
	
	def setOpenClient(self,cn):
		if cn==self.openClient:
			return
		if cn<-1 or cn>=len(self.clients):
			print("Invalid pane client index")
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
					self.SetCursor(wx.Cursor(wx.CURSOR_SIZENS))
				else:
					self.SetCursor(wx.Cursor(wx.CURSOR_SIZEWE))
				pos=self.ClientToScreen(evt.GetPosition())
				self.clkX=pos.x
				self.clkY=pos.y
				self.popenSize=self.openSize
				self.resizing=True
			else:
				self.SetCursor(wx.Cursor(wx.CURSOR_ARROW))
		else:
			self.SetCursor(wx.Cursor(wx.CURSOR_HAND))
	
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
	
	def captureLost(self,evt):
		self.isCaptured = False
	
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
						self.SetCursor(wx.Cursor(wx.CURSOR_SIZENS))
					else:
						self.SetCursor(wx.Cursor(wx.CURSOR_SIZEWE))
				else:
					self.SetCursor(wx.Cursor(wx.CURSOR_ARROW))
			else:
				self.SetCursor(wx.Cursor(wx.CURSOR_HAND))

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
		try:
			self.draw(wx.BufferedPaintDC(self))
		except wx._core.wxAssertionError as e:
			print('Exception: ' + str(e))
	
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
		if self.openClient!=-1:
			dc.SetPen(wx.Pen(wx.Colour('black'),1))
			dc.SetBrush(wx.TRANSPARENT_BRUSH)
			r = self.clientWRect()
			rc = self.clientRect(self.openClient)
			dc.DrawRectangle(r[0]-1,r[1]-1,r[2]+2,r[3]+2)
		i=0
		for c in self.clients:
			r = self.clientRect(i)
			if i==self.overClient or i==self.openClient:
				dc.SetPen(wx.Pen(wx.Colour('black'),1))
				dc.SetBrush(wx.TRANSPARENT_BRUSH)
				dc.DrawRectangle(r[0],r[1],r[2],r[3])
				if self.orientation==2:
					dc.SetTextForeground(wx.Colour(0,0,0,wx.ALPHA_OPAQUE))
					for sx in range(-1,3):
						for sy in range(-1,2):
							if sx!=sy:
								dc.DrawText(c[0],r[0]+5+sx,r[1]+5+sy)
					dc.SetTextForeground(wx.Colour(255,255,255,wx.ALPHA_OPAQUE))
					dc.DrawText(c[0],r[0]+5,r[1]+5)
					dc.DrawText(c[0],r[0]+6,r[1]+5)
				else:
					dc.SetTextForeground(wx.Colour(0,0,0,wx.ALPHA_OPAQUE))
					for sx in range(-1,2):
						for sy in range(-1,3):
							if sx!=sy:
								dc.DrawRotatedText(c[0],r[0]+19+sx,r[1]+5+sy,-90)
					dc.SetTextForeground(wx.Colour(255,255,255,wx.ALPHA_OPAQUE))
					dc.DrawRotatedText(c[0],r[0]+19,r[1]+5,-90)
					dc.DrawRotatedText(c[0],r[0]+19,r[1]+6,-90)
			else:
				if self.orientation==2:
					dc.SetTextForeground(wx.Colour(255,255,255,wx.ALPHA_OPAQUE))
					for sx in range(-1,3):
						for sy in range(-1,2):
							if sx!=sy:
								dc.DrawText(c[0],r[0]+5+sx,r[1]+5+sy)
					dc.SetTextForeground(wx.Colour(0,0,0,wx.ALPHA_OPAQUE))
					dc.DrawText(c[0],r[0]+5,r[1]+5)
					dc.DrawText(c[0],r[0]+6,r[1]+5)
				else:
					dc.SetTextForeground(wx.Colour(255,255,255,wx.ALPHA_OPAQUE))
					for sx in range(-1,2):
						for sy in range(-1,3):
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


#class voxelmapDataObject(wx.PyDataObjectSimple):
#class voxelmapDataObject:
class voxelmapDataObject(wx.DataObjectSimple):
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
			print("Empty data object")
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
		for x in range( max(vLayer.xPos,0), min( vLayer.xPos+vMap.xSize,vMask.xSize ) ):
			for y in range( max(vLayer.yPos,0), min( vLayer.yPos+vMap.ySize,vMask.ySize ) ):
				for z in range( max(vLayer.zPos,0), min( vLayer.zPos+vMap.zSize,vMap.zSize ) ):
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
			print("Empty selection")
			return ""
		d=struct.pack(">lll",xSize,ySize,zSize)
		for x in range(xMin,xMax+1):
			for y in range(yMin,yMax+1):
				for z in range(zMin,zMax+1):
					t=[0,0,0,0]
					if vMask.getPx([x,y,z]):
						t=vMap.getPx([x-vLayer.xPos,y-vLayer.yPos,z-vLayer.zPos])
					d+=struct.pack(">BBBB",t[0],t[1],t[2],t[3])
		return d
	def decode(self,d):
		if len(d)==0:
			print("Empty data object")
			return None
		offs=struct.calcsize(">III")
		xs,ys,zs = struct.unpack(">III",d[:offs])
		ret=voxelmap(xs,ys,zs)
		for x in range(xs):
			for y in range(ys):
				for z in range(zs):
					noffs=offs+struct.calcsize(">BBBB")
					r,g,b,a=struct.unpack(">BBBB",d[offs:noffs])
					offs=noffs
					ret.setPx([x,y,z],[r,g,b,a])
		return ret


class mainFrame(wx.Frame):
	def __init__(self,prj):
		wx.Frame.__init__(self,None,-1,"Katachi3D",size=(1400,1000),style=wx.DEFAULT_FRAME_STYLE)
		self.hasChanged=False
		self.SetCursor(wx.Cursor(wx.CURSOR_ARROW))
		self.control=False
		self.prj=prj
		
		if getattr(sys, 'frozen', False):
			cpath = sys.executable
			print('sys.executable = ' + sys.executable)
		else:
			cpath = __file__
    	
		self.basepath=os.path.dirname(os.path.realpath(cpath))
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
		tb.AddTool(toolId = wx.ID_NEW, label = "New", bitmap = wx.ArtProvider.GetBitmap(wx.ART_NEW,wx.ART_TOOLBAR,tsize), bmpDisabled = wx.NullBitmap, shortHelp = "New", longHelp = "Creates a new project.", clientData = None)
		self.Bind(wx.EVT_MENU,self.newFile,id=wx.ID_NEW)
		self.Bind(wx.EVT_TOOL,self.newFile,id=wx.ID_NEW)
		
		filemenu.Append(wx.ID_OPEN,"&Open ...","Opens a project")
		tb.AddTool(toolId = wx.ID_OPEN, label = "Open ...", bitmap = wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN,wx.ART_TOOLBAR,tsize), bmpDisabled = wx.NullBitmap, shortHelp = "Open", longHelp = "Opens a project.", clientData = None)
		self.Bind(wx.EVT_MENU,self.openFile,id = wx.ID_OPEN)
		self.Bind(wx.EVT_TOOL,self.openFile,id=wx.ID_OPEN)

		filemenu.Append(wx.ID_SAVE,"&Save","Saves the current project")
		tb.AddTool(toolId = wx.ID_SAVE, label = "Save", bitmap = wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE,wx.ART_TOOLBAR,tsize), bmpDisabled = wx.NullBitmap, shortHelp = "Save", longHelp = "Saves the current project.", clientData = None)
		self.Bind(wx.EVT_MENU,self.saveFile,id = wx.ID_SAVE)
		self.Bind(wx.EVT_TOOL,self.saveFile,id=wx.ID_SAVE)
		
		filemenu.Append(wx.ID_SAVEAS,"Save &as ...","Saves the current project to a diffent file")
		tb.AddTool(toolId = wx.ID_SAVEAS, label = "Save as ...", bitmap = wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE_AS,wx.ART_TOOLBAR,tsize), bmpDisabled = wx.NullBitmap, kind = wx.ITEM_NORMAL, shortHelp = "Save", longHelp = "Saves the current project to a diffent file.", clientData = None)
		self.Bind(wx.EVT_MENU,self.saveFileAs,id = wx.ID_SAVEAS)
		self.Bind(wx.EVT_TOOL,self.saveFileAs,id=wx.ID_SAVEAS)

		tb.AddSeparator()
		editmenu.Append(wx.ID_UNDO,"&Undo\tCtrl+Z","Undo last drawing operation")
		tb.AddTool(toolId = wx.ID_UNDO, label = "Undo", bitmap = wx.ArtProvider.GetBitmap(wx.ART_UNDO,wx.ART_TOOLBAR,tsize), bmpDisabled = wx.NullBitmap, kind = wx.ITEM_NORMAL, shortHelp = "Undo", longHelp = "Undo last drawing operation.", clientData = None)
		self.Bind(wx.EVT_MENU,self.undo,id = wx.ID_UNDO)
		self.Bind(wx.EVT_TOOL,self.undo,id=wx.ID_UNDO)
		editmenu.Append(wx.ID_REDO,"&Redo\tCtrl+Shift+Z","Redo last undone drawing operation")
		tb.AddTool(toolId = wx.ID_REDO, label = "Redo", bitmap = wx.ArtProvider.GetBitmap(wx.ART_REDO,wx.ART_TOOLBAR,tsize), bmpDisabled = wx.NullBitmap, kind = wx.ITEM_NORMAL, shortHelp = "Redo", longHelp = "Redo last undone drawing operation.", clientData = None)
		self.Bind(wx.EVT_MENU,self.redo,id = wx.ID_REDO)
		self.Bind(wx.EVT_TOOL,self.redo,id=wx.ID_REDO)

		editmenu.AppendSeparator()
		tb.AddSeparator()
		editmenu.Append(wx.ID_CUT,"C&ut","Cuts the selection to the clipboard")
		tb.AddTool(toolId = wx.ID_CUT, label = "Cut", bitmap = wx.ArtProvider.GetBitmap(wx.ART_CUT,wx.ART_TOOLBAR,tsize), bmpDisabled = wx.NullBitmap, kind = wx.ITEM_NORMAL, shortHelp = "Cut", longHelp = "Cuts the selection to the clipboard.", clientData = None)
		self.Bind(wx.EVT_MENU,self.cut,id = wx.ID_CUT)
		self.Bind(wx.EVT_TOOL,self.cut,id=wx.ID_CUT)
		editmenu.Append(wx.ID_COPY,"&Copy","Copies the selection to the clipboard")
		tb.AddTool(toolId = wx.ID_COPY, label = "Copy", bitmap = wx.ArtProvider.GetBitmap(wx.ART_COPY,wx.ART_TOOLBAR,tsize), bmpDisabled = wx.NullBitmap, kind = wx.ITEM_NORMAL, shortHelp = "Copy", longHelp = "Copies the selection to the clipboard.", clientData = None)
		self.Bind(wx.EVT_MENU,self.copy,id = wx.ID_COPY)
		self.Bind(wx.EVT_TOOL,self.copy,id=wx.ID_COPY)
		editmenu.Append(wx.ID_PASTE,"&Paste","Pastes from the clipboard")
		tb.AddTool(toolId = wx.ID_PASTE, label = "Paste", bitmap = wx.ArtProvider.GetBitmap(wx.ART_PASTE,wx.ART_TOOLBAR,tsize), bmpDisabled = wx.NullBitmap, kind=wx.ITEM_NORMAL, shortHelp = "Paste", longHelp = "Pastes from the clipboard.", clientData = None)
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
		tb.AddTool(toolId = 20, label = "Select", bitmap = wx.Bitmap(resbase+"select.png",wx.BITMAP_TYPE_PNG), bmpDisabled = wx.NullBitmap, kind = wx.ITEM_RADIO, shortHelp = "Select", longHelp = "Selector tool.", clientData = None)
		self.Bind(wx.EVT_TOOL,self.toolSelect,id=20)
		#
		tb.AddTool(toolId = 21, label = "Pick colour", bitmap = wx.Bitmap(resbase+"colourpicker.png",wx.BITMAP_TYPE_PNG), bmpDisabled = wx.NullBitmap, kind = wx.ITEM_RADIO, shortHelp = "Pick colour", longHelp = "Colour picker tool.", clientData = None)
		self.Bind(wx.EVT_TOOL,self.toolColour,id=21)
		#
		tb.AddTool(toolId = 22, label = "Pen", bitmap = wx.Bitmap(resbase+"pen.png",wx.BITMAP_TYPE_PNG), bmpDisabled = wx.NullBitmap, kind = wx.ITEM_RADIO, shortHelp = "Pen", longHelp = "Pen tool. Draws points. Hold shift to erase. Hold ctrl to pick colours.", clientData = None)
		self.Bind(wx.EVT_TOOL,self.toolPen,id=22)
		#
		tb.AddTool(toolId = 23, label = "2D-brush", bitmap = wx.Bitmap(resbase+"brush2D.png",wx.BITMAP_TYPE_PNG), bmpDisabled = wx.NullBitmap, kind = wx.ITEM_RADIO, shortHelp = "2D-brush", longHelp = "2D-brush tool. The brush is a circle of the specified size. Hold shift to erase. Hold ctrl to pick colours.", clientData = None)
		self.Bind(wx.EVT_TOOL,self.tool2DBrush,id=23)
		#
		tb.AddTool(toolId = 24, label = "3D-brush", bitmap = wx.Bitmap(resbase+"brush3D.png",wx.BITMAP_TYPE_PNG), bmpDisabled = wx.NullBitmap, kind = wx.ITEM_RADIO, shortHelp = "3D-brush", longHelp = "3D-brush tool. The brush is a sphere of the specified size. Hold shift to erase. Hold ctrl to pick colours.", clientData = None)
		self.Bind(wx.EVT_TOOL,self.tool3DBrush,id=24)
		#
		tb.AddTool(toolId = 25, label = "2D-fill", bitmap = wx.Bitmap(resbase+"fill2D.png",wx.BITMAP_TYPE_PNG), bmpDisabled = wx.NullBitmap, kind = wx.ITEM_RADIO, shortHelp = "2D-fill", longHelp = "2D-fill tool. Flood fills in two dimensions. Hold shift to erase. Hold ctrl to pick colours.", clientData = None)
		self.Bind(wx.EVT_TOOL,self.tool2DFill,id=25)
		#
		tb.AddTool(toolId = 26, label = "3D-fill", bitmap = wx.Bitmap(resbase+"fill3D.png",wx.BITMAP_TYPE_PNG), bmpDisabled = wx.NullBitmap, kind = wx.ITEM_RADIO, shortHelp = "3D-fill", longHelp = "3D-fill tool. Flood fills in three dimensions. Hold shift to erase. Hold ctrl to pick colours.", clientData = None)
		self.Bind(wx.EVT_TOOL,self.tool3DFill,id=26)
		#
		tb.ToggleTool(20+self.tool,True)
		tb.AddSeparator()
		self.colSelect=csel.ColourSelect(tb,-1,"",self.penColour)
		self.Bind(csel.EVT_COLOURSELECT,self.colourSelect,self.colSelect)
		tb.AddControl( self.colSelect )
		tb.Realize()
		
		# Panes
		self.leftPane=paneWin(self,self,-1,0,200)
		self.rightPane=paneWin(self,self,-1,1,280)
		self.bottomPane=paneWin(self,self,-1,2,200)
		
		self.layerwin=layerWindow(self,self.leftPane,-1,prj)
		self.leftPane.addClient("Layers",self.layerwin)
		
		self.propertieswin=propertiesWindow(self,self.rightPane,-1)
		self.rightPane.addClient("Properties",self.propertieswin)
		
		self.bottomPane.addClient("Python shell",py.shell.Shell(self.bottomPane,-1,
			introText="------------------------------------------------------\n\tKatachi3D\n\tBy Bjørn André Bredesen, 2013\n------------------------------------------------------\nThe open project can be accessed via 'frame.prj'. After making changes to the project, 'frame.ProjectChanged()' can be called to refresh.\n------------------------------------------------------"))
		#
		#self.Bind(wx.EVT_SASH_DRAGGED_RANGE,self.sashD)
		self.Bind(wx.EVT_SIZE,self.onsize)
		#
		self.control=viewportContainer(self,self,-1,prj)
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
			print("No edit history candidate")
			return
		self.EHUndo.append(self.EHCandidate)
		self.EHRedo=[]
		self.EHClearCandidate()
		self.ProjectChanged()
		
	def EHClearCandidate(self):
		self.EHCandidate=None
	
	def RefreshClients(self):
		self.layerwin.Refresh()
		self.control.RefreshClients()
	
	def GenerateClients(self):
		self.control.GenerateClients()
		self.RefreshClients()
	
	def ProjectChanged(self):
		self.hasChanged=True
		self.GenerateClients()
	
	def undo(self,evt):
		if len(self.EHUndo)==0:
			print("Empty undo list")
			return
		self.EHRedo.append(self.EHUndo.pop().use(self))
		self.ProjectChanged()
		
	def redo(self,evt):
		if len(self.EHRedo)==0:
			print("Empty redo list")
			return
		self.EHUndo.append(self.EHRedo.pop().use(self))
		self.ProjectChanged()
	
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
			print("Nothing to copy")
			return
		if wx.TheClipboard.IsOpened():
			print("Clipboard already opened")
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
			print("Could not obtain data in the correct format.")
			wx.TheClipboard.Close()
			return
		vMap=vmo.GetVMap()
		if vMap==None:
			print("Could not obtain data in the correct format.")
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
			print("Invalid layer")
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
			dlg=wx.FileDialog(self,"Open",dirname,"","Katachi3D graphics (*.k3d)|*.k3d|All files|*.*",wx.FD_OPEN)
			if dlg.ShowModal()==wx.ID_OK:
				filename=dlg.GetFilename()
				dirname=dlg.GetDirectory()
				fpath=os.path.join(dirname,filename)
				lprj=voxelImage(1,1,1)
				if not lprj.load(fpath):
					self.new()
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
			#wildcard="XYZ files (*.xyz)|*.xyz"
			with wx.FileDialog(self,"Save as", wildcard = "Katachi3D graphics (*.k3d)|*.k3d", style = wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT) as dlg:
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

