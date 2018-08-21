# -*- coding: latin-1 -*-
#####################################################
# Katachi3D
# Copyright Bjørn André Bredesen, 2013
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

# The procedures here are to be compiled with Cython.
# This is due to the need for low-level memory access for reasonable performance.

import cython
from libc.math cimport sqrt
import array
import time

#####################################################
# Editing

# brush3D_cython
#	For 3D brush tool. Using Cython and direct buffer manipulation is considerably
#	more fast than manipulating the array with regular Python.
def brush3D_cython(arr, cr,cg,cb,ca, axis, arrxSize,arrySize,arrzSize, minX,maxX,minY,maxY,minZ,maxZ, penSize, _lx, _ly, _zI, selMask,lxp,lyp,lzp,smX,smY,smZ ):
	cdef unsigned int _addr=arr.buffer_info()[0]
	cdef unsigned char* _arr=<unsigned char*> (&_addr)[0]
	cdef unsigned char _cr=cr
	cdef unsigned char _cg=cg
	cdef unsigned char _cb=cb
	cdef unsigned char _ca=ca
	cdef bint ch=False
	cdef float ps=penSize
	cdef int lx=_lx
	cdef int ly=_ly
	cdef int zI=_zI
	cdef int _axis=axis
	cdef int sX=arrxSize
	cdef int sXY=sX*arrySize
	cdef int sZ=arrzSize
	cdef int gvx
	cdef int gvy
	cdef int gvz
	cdef int cx
	cdef int cy
	cdef int cz
	cdef int d1
	cdef double df
	cdef double md = ps+0.2
	md*=md
	cdef unsigned char*_selMask=NULL
	if selMask!=None:
		_addr=selMask.buffer_info()[0]
		_selMask=<unsigned char*> (&_addr)[0]
	cdef int _lxp=lxp
	cdef int _lyp=lyp
	cdef int _lzp=lzp
	cdef int _smX=smX
	cdef int _smXY=_smX*smY
	for cx in xrange(minX,maxX):
		for cy in xrange(minY,maxY):
			for cz in xrange(minZ,maxZ):
				d1=lx-cx
				d1*=d1
				df=d1
				d1=ly-cy
				d1*=d1
				df+=d1
				d1=zI-cz
				d1*=d1
				df+=d1
				if df<=md:
					if _axis==0:
						gvx=cx
						gvy=cy
						gvz=cz
					elif _axis==1:
						gvx=cz
						gvy=cy
						gvz=sZ-cx-1
					elif _axis==2:
						gvx=cx
						gvy=cz
						gvz=cy
					editable=True
					if _selMask!=NULL:
						if _selMask[(gvz+lzp)*_smXY+(gvy+lyp)*_smX+(gvx+lxp)] == 0:
							editable=False
					if editable:
						offs=(gvz*sXY+gvy*sX+gvx)*4
						_arr[offs+0]=_cr
						_arr[offs+1]=_cg
						_arr[offs+2]=_cb
						_arr[offs+3]=_ca
						ch=True
	return ch


#####################################################
# 3D Model

def GenerateFromVoxelLayerCythonC(mesh,layer):
	vMap=layer.vMap
	
	cdef int bxSize=vMap.xSize+1
	cdef int bySize=vMap.ySize+1
	cdef int bxySize=bxSize*(vMap.ySize+1)
	cdef int bzSize=vMap.zSize+1

	_imap=array.array('I',[0]*bxySize*bzSize)

	cdef unsigned int _addr=_imap.buffer_info()[0]
	cdef unsigned int* imap=<unsigned int*> (&_addr)[0]

	cdef unsigned int _addr2=vMap.vMap.buffer_info()[0]
	cdef unsigned char* vm=<unsigned char*> (&_addr2)[0]
	
	vertices=[None]*(bxySize*bzSize)
	faces=mesh.faces
	cdef int nvi=1
	cdef int vmxSize=vMap.xSize
	cdef int vmySize=vMap.ySize
	cdef int vmxySize=vmxSize*vMap.ySize
	cdef int vmzSize=vMap.zSize

	cdef int x,_x,		y,_y,		z,_z
	cdef float cr,cg,cb,ca
	cdef unsigned int offs
	
	for x in xrange(vmxSize):
		for y in xrange(vmySize):
			for z in xrange(vmzSize):
				offs=(z*vmxySize+y*vmxSize+x)*4
				if vm[offs+3]==0:
					continue
				v = [vm[offs+0],vm[offs+1],vm[offs+2],vm[offs+3]]
				dxa = x==0 or vm[(z*vmxySize+y*vmxSize+x-1)*4+3]==0
				dxb = x==vmxSize-1 or vm[(z*vmxySize+y*vmxSize+x+1)*4+3]==0
				dya = y==0 or vm[(z*vmxySize+(y-1)*vmxSize+x)*4+3]==0
				dyb = y==vmySize-1 or vm[(z*vmxySize+(y+1)*vmxSize+x)*4+3]==0
				dza = z==0 or vm[((z-1)*vmxySize+y*vmxSize+x)*4+3]==0
				dzb = z==vmzSize-1 or vm[((z+1)*vmxySize+y*vmxSize+x)*4+3]==0
				if not (dxa or dya or dza or dxb or dyb or dzb):
					continue
				cr=v[0]/255.0
				cg=v[1]/255.0
				cb=v[2]/255.0
				ca=v[3]/255.0
				_x=x+layer.xPos
				_y=y+layer.yPos
				_z=z+layer.zPos
				if dxa:
					i1 = imap[ z*bxySize+y*bxSize+x ]
					if i1 == 0:
						i1=imap[ z*bxySize+y*bxSize+x ] = nvi
						vertices[nvi-1] = mesh.newVertex( _x,_y,_z ) 
						nvi+=1
					i2 = imap[ z*bxySize+(y+1)*bxSize+x ]
					if i2 == 0:
						i2=imap[ z*bxySize+(y+1)*bxSize+x ] = nvi
						vertices[nvi-1] = mesh.newVertex( _x,_y+1,_z) 
						nvi+=1
					i3 = imap[ (z+1)*bxySize+(y+1)*bxSize+x ]
					if i3 == 0:
						i3=imap[ (z+1)*bxySize+(y+1)*bxSize+x ] = nvi
						vertices[nvi-1] = mesh.newVertex( _x,_y+1,_z+1) 
						nvi+=1
					i4 = imap[ (z+1)*bxySize+y*bxSize+x ]
					if i4 == 0:
						i4=imap[ (z+1)*bxySize+y*bxSize+x ] = nvi
						vertices[nvi-1] = mesh.newVertex( _x,_y,_z+1)  
						nvi+=1
					faces.append( mesh.newFace4(i1-1,i4-1,i3-1,i2-1,  -1,0,0,  cr,cg,cb,ca) )
				if dxb:
					i1 = imap[ z*bxySize+y*bxSize+x+1 ]
					if i1 == 0:
						i1=imap[ z*bxySize+y*bxSize+x+1 ] = nvi
						vertices[nvi-1] = mesh.newVertex( _x+1,_y,_z) 
						nvi+=1
					i2 = imap[ z*bxySize+(y+1)*bxSize+x+1 ]
					if i2 == 0:
						i2=imap[ z*bxySize+(y+1)*bxSize+x+1 ] = nvi
						vertices[nvi-1] = mesh.newVertex( _x+1,_y+1,_z) 
						nvi+=1
					i3 = imap[ (z+1)*bxySize+(y+1)*bxSize+x+1 ]
					if i3 == 0:
						i3=imap[ (z+1)*bxySize+(y+1)*bxSize+x+1 ] = nvi
						vertices[nvi-1] = mesh.newVertex( _x+1,_y+1,_z+1) 
						nvi+=1
					i4 = imap[ (z+1)*bxySize+y*bxSize+x+1 ]
					if i4 == 0:
						i4=imap[ (z+1)*bxySize+y*bxSize+x+1 ] = nvi
						vertices[nvi-1] = mesh.newVertex( _x+1,_y,_z+1) 
						nvi+=1
					faces.append( mesh.newFace4(i1-1,i2-1,i3-1,i4-1,  1,0,0,  cr,cg,cb,ca) )
				if dya:
					i1 = imap[ z*bxySize+y*bxSize+x ]
					if i1 == 0:
						i1=imap[ z*bxySize+y*bxSize+x ] = nvi
						vertices[nvi-1] = mesh.newVertex( _x,_y,_z) 
						nvi+=1
					i2 = imap[ z*bxySize+y*bxSize+x+1 ]
					if i2 == 0:
						i2=imap[ z*bxySize+y*bxSize+x+1 ] = nvi
						vertices[nvi-1] = mesh.newVertex( _x+1,_y,_z) 
						nvi+=1
					i3 = imap[ (z+1)*bxySize+y*bxSize+x+1 ]
					if i3 == 0:
						i3=imap[ (z+1)*bxySize+y*bxSize+x+1 ] = nvi
						vertices[nvi-1] = mesh.newVertex( _x+1,_y,_z+1) 
						nvi+=1
					i4 = imap[ (z+1)*bxySize+y*bxSize+x ]
					if i4 == 0:
						i4=imap[ (z+1)*bxySize+y*bxSize+x ] = nvi
						vertices[nvi-1] = mesh.newVertex( _x,_y,_z+1) 
						nvi+=1
					faces.append( mesh.newFace4(i1-1,i2-1,i3-1,i4-1,  0,-1,0,  cr,cg,cb,ca) )
				if dyb:
					i1 = imap[ z*bxySize+(y+1)*bxSize+x ]
					if i1 == 0:
						i1=imap[ z*bxySize+(y+1)*bxSize+x ] = nvi
						vertices[nvi-1] = mesh.newVertex( _x,_y+1,_z) 
						nvi+=1
					i2 = imap[ z*bxySize+(y+1)*bxSize+x+1 ]
					if i2 == 0:
						i2=imap[ z*bxySize+(y+1)*bxSize+x+1 ] = nvi
						vertices[nvi-1] = mesh.newVertex( _x+1,_y+1,_z) 
						nvi+=1
					i3 = imap[ (z+1)*bxySize+(y+1)*bxSize+x+1 ]
					if i3 == 0:
						i3=imap[ (z+1)*bxySize+(y+1)*bxSize+x+1 ] = nvi
						vertices[nvi-1] = mesh.newVertex( _x+1,_y+1,_z+1) 
						nvi+=1
					i4 = imap[ (z+1)*bxySize+(y+1)*bxSize+x ]
					if i4 == 0:
						i4=imap[ (z+1)*bxySize+(y+1)*bxSize+x ] = nvi
						vertices[nvi-1] = mesh.newVertex( _x,_y+1,_z+1) 
						nvi+=1
					faces.append( mesh.newFace4(i1-1,i4-1,i3-1,i2-1,  0,1,0,  cr,cg,cb,ca) )
				if dza:
					i1 = imap[ z*bxySize+y*bxSize+x ]
					if i1 == 0:
						i1=imap[ z*bxySize+y*bxSize+x ] = nvi
						vertices[nvi-1] = mesh.newVertex( _x,_y,_z) 
						nvi+=1
					i2 = imap[ z*bxySize+y*bxSize+x+1 ]
					if i2 == 0:
						i2=imap[ z*bxySize+y*bxSize+x+1 ] = nvi
						vertices[nvi-1] = mesh.newVertex( _x+1,_y,_z) 
						nvi+=1
					i3 = imap[ z*bxySize+(y+1)*bxSize+x+1 ]
					if i3 == 0:
						i3=imap[ z*bxySize+(y+1)*bxSize+x+1 ] = nvi
						vertices[nvi-1] = mesh.newVertex( _x+1,_y+1,_z) 
						nvi+=1
					i4 = imap[ z*bxySize+(y+1)*bxSize+x ]
					if i4 == 0:
						i4=imap[ z*bxySize+(y+1)*bxSize+x ] = nvi
						vertices[nvi-1] = mesh.newVertex( _x,_y+1,_z) 
						nvi+=1
					faces.append( mesh.newFace4(i1-1,i4-1,i3-1,i2-1,  0,0,-1,  cr,cg,cb,ca) )
				if dzb:
					i1 = imap[ (z+1)*bxySize+y*bxSize+x ]
					if i1 == 0:
						i1=imap[ (z+1)*bxySize+y*bxSize+x ] = nvi
						vertices[nvi-1] = mesh.newVertex( _x,_y,_z+1) 
						nvi+=1
					i2 = imap[ (z+1)*bxySize+y*bxSize+x+1 ]
					if i2 == 0:
						i2=imap[ (z+1)*bxySize+y*bxSize+x+1 ] = nvi
						vertices[nvi-1] = mesh.newVertex( _x+1,_y,_z+1) 
						nvi+=1
					i3 = imap[ (z+1)*bxySize+(y+1)*bxSize+x+1 ]
					if i3 == 0:
						i3=imap[ (z+1)*bxySize+(y+1)*bxSize+x+1 ] = nvi
						vertices[nvi-1] = mesh.newVertex( _x+1,_y+1,_z+1) 
						nvi+=1
					i4 = imap[ (z+1)*bxySize+(y+1)*bxSize+x ]
					if i4 == 0:
						i4=imap[ (z+1)*bxySize+(y+1)*bxSize+x ] = nvi
						vertices[nvi-1] = mesh.newVertex( _x,_y+1,_z+1) 
						nvi+=1
					faces.append( mesh.newFace4(i1-1,i2-1,i3-1,i4-1,  0,0,1,  cr,cg,cb,ca) )
	mesh.vertices=vertices[0:nvi-1]


def CalculateVertexNormalsCython(v,f):
	cdef float nx,ny,nz,s
	cdef Face _f
	cdef FaceIndex i
	cdef Vertex v1
	cdef Vector3D vn
	for _f in f:
		for i in _f.indices:
			vn=v[i.index].normal
			fn=_f.normal
			vn.x+=fn.x
			vn.y+=fn.y
			vn.z+=fn.z
	for v1 in v:
		vn=v1.normal
		nx=vn.x
		ny=vn.y
		nz=vn.z
		s = sqrt( nx*nx + ny*ny + nz*nz )
		if s!=0:
			vn.x=nx/s
			vn.y=ny/s
			vn.z=nz/s

def CalculateFaceNormalsCython(v,f):
	cdef double crossx,crossy,crossz,s
	cdef Vector3D vi1,vi2,vi3,vi4,n
	cdef list ind
	for _f in f:
		ind=_f.indices
		if len(ind)==4:
			vi1=v[ind[0].index].pos
			vi2=v[ind[1].index].pos
			vi3=v[ind[2].index].pos
			vi4=v[ind[3].index].pos
			crossx = ((vi2.y-vi1.y)*(vi4.z-vi1.z) - (vi2.z-vi1.z)*(vi4.y-vi1.y)) + ((vi3.y-vi2.y)*(vi4.z-vi2.z) - (vi3.z-vi2.z)*(vi4.y-vi2.y))
			crossy = ((vi2.z-vi1.z)*(vi4.x-vi1.x) - (vi2.x-vi1.x)*(vi4.z-vi1.z)) + ((vi3.z-vi2.z)*(vi4.x-vi2.x) - (vi3.x-vi2.x)*(vi4.z-vi2.z))
			crossz = ((vi2.x-vi1.x)*(vi4.y-vi1.y) - (vi2.y-vi1.y)*(vi4.x-vi1.x)) + ((vi3.x-vi2.x)*(vi4.y-vi2.y) - (vi3.y-vi2.y)*(vi4.x-vi2.x))
			s = ( crossx*crossx + crossy*crossy + crossz*crossz )**0.5
			n=_f.normal
			n.x=crossx/s
			n.y=crossy/s
			n.z=crossz/s


cdef class Vector3D:
	cdef double x
	cdef double y
	cdef double z
	def __init__(self,x,y,z):
		self.x=x
		self.y=y
		self.z=z
	property x:
		def __get__(self):
			return self.x
		def __set__(self, value):
			self.x=value
	property y:
		def __get__(self):
			return self.y
		def __set__(self, value):
			self.y=value
	property z:
		def __get__(self):
			return self.z
		def __set__(self, value):
			self.z=value
	def __add__(self,other):
		return Vector3D(self.x+other.x,self.y+other.y,self.z+other.z)
	def __sub__(self,other):
		return Vector3D(self.x-other.x,self.y-other.y,self.z-other.z)
	def __mul__(self,other):
		return Vector3D(self.x*other,self.y*other,self.z*other)
	def normalize(self):
		s=( self.x**2 + self.y**2 + self.z**2 )**(1/2)
		if s==0:
			return self
		return Vector3D( self.x/s, self.y/s, self.z/s )
	def dot(self,other):
		return self.x*other.x+self.y*other.y+self.z*other.z

cdef class RGB:
	cdef double r
	cdef double g
	cdef double b
	cdef double a
	def __init__(self,r,g,b,a=1):
		self.r=r
		self.g=g
		self.b=b
		self.a=a
	property r:
		def __get__(self):
			return self.r
		def __set__(self,v):
			self.r=v
	property g:
		def __get__(self):
			return self.g
		def __set__(self,v):
			self.g=v
	property b:
		def __get__(self):
			return self.b
		def __set__(self,v):
			self.b=v
	property a:
		def __get__(self):
			return self.a
		def __set__(self,v):
			self.a=v

cdef class Vertex:
	cdef Vector3D pos
	cdef Vector3D normal
	cdef double ox,oy,oz
	cdef set neighbours
	def __init__(self,pos,normal=Vector3D(0,0,0)):
		self.pos=pos
		self.normal=normal
	property pos:
		def __get__(self):
			return self.pos
		def __set__(self,v):
			self.pos=v
	property normal:
		def __get__(self):
			return self.normal
		def __set__(self,v):
			self.normal=v
	property neighbours:
		def __get__(self):
			return self.neighbours
		def __set__(self,v):
			self.neighbours=v
	property ox:
		def __get__(self):
			return self.ox
		def __set__(self,v):
			self.ox=v
	property oy:
		def __get__(self):
			return self.oy
		def __set__(self,v):
			self.oy=v
	property oz:
		def __get__(self):
			return self.oz
		def __set__(self,v):
			self.oz=v

cdef class FaceIndex:
	cdef int index
	cdef Vector3D normal
	def __init__(self,index,normal):
		self.index=index
		self.normal=normal
	property index:
		def __get__(self):
			return self.index
		def __set__(self,v):
			self.index=v
	property normal:
		def __get__(self):
			return self.normal
		def __set__(self,v):
			self.normal=v

cdef class Face:
	cdef list indices
	cdef Vector3D normal
	cdef RGB colour
	def __init__(self,ind=[],normal=Vector3D(0,0,0),colour=RGB(0,0,0)):
		self.indices=ind
		self.normal=normal
		self.colour=colour
	def addIndex(self,ind,normal=None):
		if normal==None:
			normal=self.normal
		self.indices.append( FaceIndex(ind,normal) )
	property colour:
		def __get__(self):
			return self.colour
		def __set__(self,v):
			self.colour=v
	property indices:
		def __get__(self):
			return self.indices
		def __set__(self,v):
			self.indices=v
	property normal:
		def __get__(self):
			return self.normal
		def __set__(self,v):
			self.normal=v

cdef class Mesh:
	cdef list faces
	cdef list vertices
	cdef object layer
	property faces:
		def __get__(self):
			return self.faces
		def __set__(self,v):
			self.faces=v
	property vertices:
		def __get__(self):
			return self.vertices
		def __set__(self,v):
			self.vertices=v
	property layer:
		def __get__(self):
			return self.layer
		def __set__(self,v):
			self.layer=v
	
	def __init__(self):
		self.clearMesh()
	def newFace(self,ind=[],normal=Vector3D(0,0,0),colour=RGB(0,0,0)):
		r=Face(ind,normal,colour)
		self.faces.append(r)
		return r
	def addPoly(self,points,normal=Vector3D(0,0,0),colour=RGB(0,0,0)):
		face=self.newFace([],normal,colour)
		for p in points:
			i=len(self.vertices)
			self.vertices.append( Vertex(p) )
			face.addIndex(i)
	
	def clearMesh(self):
		self.vertices=[]
		self.faces=[]
		self.layer=None
	
	def newFace4(self,i1,i2,i3,i4,nx,ny,nz,r,g,b,a):
		n=Vector3D(nx,ny,nz)
		return Face( [ FaceIndex(i1,n),FaceIndex(i2,n),FaceIndex(i3,n),FaceIndex(i4,n) ], normal=n, colour=RGB(r,g,b,a) )
	
	def newVertex(self,x,y,z):
		return Vertex(Vector3D(x,y,z))
	
	def GenerateFromVoxelLayerCython(self,layer):
		time0=time.time()
		self.clearMesh()
		self.layer=layer
		#
		GenerateFromVoxelLayerCythonC(self,layer)
		#
		print "DBG: Mesh from voxel image layer (cython)"
		print " - - - time: ",(time.time()-time0)
	
	def postProcess(self):
		print " - DBG: Post process model"
		if self.layer.renderMode==0:
			self.CalculateFaceNormals()
			self.CalculateVertexNormals()
		elif self.layer.renderMode==1:
			self.SmoothPositional(self.layer.smoothPasses)
			self.CalculateFaceNormals()
			self.CalculateVertexNormals()
			v=self.vertices
			for f in self.faces:
				for i in f.indices:
					i.normal=v[i.index].normal
		elif self.layer.renderMode==2:
			self.SmoothNormal(self.layer.smoothPasses)
			self.CalculateFaceNormals()
			self.CalculateVertexNormals()
			v=self.vertices
			for f in self.faces:
				for i in f.indices:
					i.normal=v[i.index].normal
	
	def RemoveDoubleVertices(self):
		print " - DBG: Remove double vertices"
		time0=time.time()
		v=self.vertices
		newv=[]
		nv=len(v)
		for v1 in v:
			v1.original=None
		# Find unique vertices based on positions
		oi=0
		for v1i in xrange(0,nv-1):
			v1=v[v1i]
			if v1.original!=None:
				continue
			v1.index=oi	# Mark index of unique vertex (which it will have after removing doubles)
			newv.append(v1) # Add to new vertex list
			oi+=1
			# Find and mark doubles
			for v2i in xrange(v1i+1,nv):
				v2=v[v2i]
				if v2.original!=None:
					continue
				if v1.pos.x==v2.pos.x and v1.pos.y==v2.pos.y and v1.pos.z==v2.pos.z:
					v2.original=v1
		# Update face indices
		for f in self.faces:
			for ind in f.indices:
				fv=v[ind.index]
				if fv.original!=None:
					fv=fv.original
				ind.index=fv.index
		self.vertices=newv # Use the new vertex list
		print " - - - time: ",(time.time()-time0)
	
	def CalculateFaceNormals(self):
		print " - - DBG: Calculate face normals"
		time0=time.time()
		CalculateFaceNormalsCython(self.vertices,self.faces)
		print " - - - time: ",(time.time()-time0)
	
	def CalculateVertexNormals(self):
		print " - - DBG: Calculate vertex normals"
		time0=time.time()
		v=self.vertices
		for v1 in v:
			v1.normal = Vector3D(0,0,0)
		CalculateVertexNormalsCython(v,self.faces)
		print " - - - time: ",(time.time()-time0)

	def SmoothNormal(self,passes):
		print " - - DBG: Normal smoothing - ",passes," passes"
		time0=time.time()
		
		cdef Vertex v1
		cdef Face f
		cdef int ni, _i, _pass, nn, nmproj
		cdef double tx,ty,tz, mproj
		
		v=self.vertices
		for v1 in v:
			v1.neighbours=set()
			v1.normal = Vector3D(0,0,0)
		for f in self.faces:
			ni=len(f.indices)
			for _i in xrange(ni):
				v1=v[f.indices[(_i+1)%ni].index]
				v1.neighbours.add( f.indices[_i%ni].index )
				v1.neighbours.add( f.indices[(_i+2)%ni].index )
		for _pass in xrange(passes):
			for v1 in v:
				v1.normal=Vector3D(0,0,0)
				v1.ox=v1.pos.x
				v1.oy=v1.pos.y
				v1.oz=v1.pos.z
			for v1 in v:
				nn=len(v1.neighbours)
				if nn>0:
					tx=0
					ty=0
					tz=0
					for v2i in v1.neighbours:
						v2=v[v2i]
						tx+=v2.ox
						ty+=v2.oy
						tz+=v2.oz
					v1.pos=Vector3D( tx/nn, ty/nn, tz/nn )
			CalculateFaceNormalsCython(v,self.faces)
			CalculateVertexNormalsCython(v,self.faces)
			mproj=0
			nmproj=0
			# Find mean projection of new positions to the normals from the old positions
			for v1 in v:
				mproj+=(v1.pos.x-v1.ox)*v1.normal.x + (v1.pos.y-v1.oy)*v1.normal.y + (v1.pos.z-v1.oz)*v1.normal.z
				nmproj+=1
			if nmproj<1:
				continue
			mproj/=nmproj
			# Move points based on the mean projection. The idea is that this will give
			# a more similar volume of the overall shape to the original, while maintaining
			# the smootheness.
			for v1 in v:
				v1.pos.x -= mproj*v1.normal.x
				v1.pos.y -= mproj*v1.normal.y
				v1.pos.z -= mproj*v1.normal.z
		print " - - - time: ",(time.time()-time0)
					
	def SmoothPositional(self,passes):
		print " - - DBG: Positional smoothing - ",passes," passes"
		time0=time.time()
		v=self.vertices
		for v1 in v:
			v1.neighbours=set()
		for f in self.faces:
			ni=len(f.indices)
			for _i in xrange(ni):
				v1=v[f.indices[(_i+1)%ni].index]
				v1.neighbours.add( f.indices[_i%ni].index )
				v1.neighbours.add( f.indices[(_i+2)%ni].index )
		for _pass in xrange(passes):
			for v1 in v:
				v1.ox=v1.pos.x
				v1.oy=v1.pos.y
				v1.oz=v1.pos.z
			for v1 in v:
				nn=len(v1.neighbours)
				if nn>0:
					tx=0
					ty=0
					tz=0
					for v2i in v1.neighbours:
						v2=v[v2i]
						tx+=v2.ox
						ty+=v2.oy
						tz+=v2.oz
					p=v1.pos
					p.x=tx/nn
					p.y=ty/nn
					p.z=tz/nn
		print " - - - time: ",(time.time()-time0)
	
	def dbgout(self):
		print " - - Vertices: ",(len(self.vertices))
		print " - - Faces: ",(len(self.faces))


cdef extern from "GL/gl.h":
	ctypedef float GLfloat
	ctypedef unsigned int GLenum
	int GL_QUADS
	int GL_FRONT
	int GL_DIFFUSE
	cdef void glBegin(GLenum mode)
	cdef void glEnd()
	cdef void glVertex3f(GLfloat x,GLfloat y,GLfloat z)
	cdef void glNormal3f(GLfloat x,GLfloat y,GLfloat z)
	cdef void glColor4f(GLfloat r,GLfloat g,GLfloat b,GLfloat a)
	cdef void glMaterialfv(GLenum f,GLenum,GLfloat*)

def renderFlatCython(mdl):
	cdef Mesh m
	cdef list v
	cdef Face f
	cdef RGB col
	cdef Vector3D p1,p2,p3,p4
	for m in mdl.meshes:
		v=m.vertices
		for f in m.faces:
			col=f.colour
			glColor4f(col.r,col.g,col.b,col.a)
			i=f.indices
			if len(i)==4:
				p1=v[i[0].index].pos
				p2=v[i[1].index].pos
				p3=v[i[2].index].pos
				p4=v[i[3].index].pos
				glBegin(GL_QUADS)
				glVertex3f(p1.x,p1.y,p1.z)
				glVertex3f(p2.x,p2.y,p2.z)
				glVertex3f(p3.x,p3.y,p3.z)
				glVertex3f(p4.x,p4.y,p4.z)
				glEnd()
			else:
				print "DBG: Invalid face"

def renderLightCython(mdl):
	cdef Mesh m
	cdef list v
	cdef Face f
	cdef list i
	cdef Vector3D p1,p2,p3,p4,n1,n2,n3,n4
	cdef RGB col
	cdef float _col[4]
	for m in mdl.meshes:
		v=m.vertices
		for f in m.faces:
			col=f.colour
			_col[0]=col.r
			_col[1]=col.g
			_col[2]=col.b
			_col[3]=col.a
			glMaterialfv(GL_FRONT,GL_DIFFUSE,_col)
			i=f.indices
			if len(i)==4:
				p1=v[i[0].index].pos
				p2=v[i[1].index].pos
				p3=v[i[2].index].pos
				p4=v[i[3].index].pos
				n1=i[0].normal
				n2=i[1].normal
				n3=i[2].normal
				n4=i[3].normal
				glBegin(GL_QUADS)
				glNormal3f(n1.x,n1.y,n1.z)
				glVertex3f(p1.x,p1.y,p1.z)
				glNormal3f(n2.x,n2.y,n2.z)
				glVertex3f(p2.x,p2.y,p2.z)
				glNormal3f(n3.x,n3.y,n3.z)
				glVertex3f(p3.x,p3.y,p3.z)
				glNormal3f(n4.x,n4.y,n4.z)
				glVertex3f(p4.x,p4.y,p4.z)
				glEnd()
			else:
				print "DBG: Invalid face"


