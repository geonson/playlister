#!/bin/bash

cython --embed -3 playlister.pyx
if [[ "$OSTYPE" == "linux-gnu" ]]
then
  #Linux compile
  mkdir -p bin
  gcc -Os -I /usr/include/python3.7m -L /usr/lib -o bin/playlister playlister.c -lpython3.7m -lpthread -lm -lutil -ldl
elif [[ "$OSTYPE" == "darwin"* ]]
then
  #Mac OS compile
  gcc -Os -I /usr/local/Cellar/python/3.7.4_1/Frameworks/Python.framework/Versions/3.7/include/python3.7m -L /usr/local/Cellar/python/3.7.4_1/Frameworks/Python.framework/Versions/3.7/lib -o bin/playlister playlister.c -lpython3.7 -lpthread -lm -lutil -ldl
fi
