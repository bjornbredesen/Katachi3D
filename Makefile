
all: Katachi3Dlib

Katachi3Dlib: ./Katachi3Dlib.pyx
	cython -2 --cplus Katachi3Dlib.pyx
	g++ -c -O3 -O2 -fPIC -I/usr/include/python2.7 -I/usr/include/ Katachi3Dlib.cpp
	g++ -shared Katachi3Dlib.o -o Katachi3Dlib.so
	rm ./Katachi3Dlib.cpp
	rm ./Katachi3Dlib.o
