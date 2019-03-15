#!/bin/bash

cython --embed -3 playlister.pyx
#Mac OS compile
gcc -Os -I /usr/local/Cellar/python/3.6.5/Frameworks/Python.framework/Versions/3.6/include/python3.6m -L /usr/local/Cellar/python/3.6.5/Frameworks/Python.framework/Versions/3.6/lib -o playlister playlister.c -lpython3.6 -lpthread -lm -lutil -ldl
