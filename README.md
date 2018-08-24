# Katachi3D

Copyright Bjørn Bredesen, 2013
E-mail: contact@bjornbredesen.no


About
----------------
Katachi3D is a voxel-graphics editor, implemented in Python using wxPython and OpenGL. 
Screenshots and other projects can be found at: bjornbredesen.no


License
----------------
This program is free software, distributed under the GNU General Public License version 3. Please see the full copy of the license, given in COPYING.

The icons provided with this program (see the "res" folder) are the work of Bjørn Bredesen, and may not be redistributed independently of Katachi3D without acquiring the permission to do so from Bjørn Bredesen.


Installing
----------------
Last tested to be working on Ubuntu 16.04 with the following dependencies:
 * Python 2.7.12
 * WxPython 3.0.2.0
 * PyOpenGL 3.1.0
 * Cython 0.27.3

To install:
```
sudo apt-get install python2.7
sudo apt-get install python-wxgtk3.0
pip install PyOpenGL PyOpenGL_accelerate
sudo apt-get install cython
make all
```

To run:
```
python Katachi3D.py
```


Quick help
----------------
| Action                       | Reaction                                     |
| ---------------------------- | -------------------------------------------- |
| Mouse wheel                  | Vertical scroll                              |
| Mouse wheel + Shift          | Horizontal scroll                            |
| Mouse wheel + Alt            | Depth scroll                                 |
| Mouse wheel + Ctrl           | Zoom                                         |
| Drawing tool + Click + Ctrl  | Pick colour                                  |
| Drawing tool + Click + Shift | Erase                                        |
| Tab (in viewport)            | Brings focus to next viewport                |
| Shift+Tab (in viewport)      | Brings focus to previous viewport            |
| X (in viewport)              | Maximized/minimized viewport                 |
| C (in viewport)              | Open colour picker                           |
| Q (in viewport)              | Increase tool size                           |
| A (in viewport)              | Decrease tool size                           |
| Ctrl+left (in viewport)      | Focus to layers                              |
| Ctrl+right (in viewport)     | Focus to properties                          |
| Ctrl+down (in viewport)      | Focus to python shell                        |

