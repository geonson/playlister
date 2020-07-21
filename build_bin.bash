#!/bin/bash

mkdir -p bin
cython --embed -3 playlister.pyx
if [[ "$OSTYPE" == "linux-gnu" ]]
then
  #Linux compile
  mkdir -p bin
  gcc -Os -I /usr/include/python3.8 -L /usr/lib -o bin/playlister playlister.c -lpython3.8 -lpthread -lm -lutil -ldl
elif [[ "$OSTYPE" == "darwin"* ]]
then
  #Mac OS compile
  gcc -Os -I ~/.pyenv/versions/3.8.3/include/python3.8 -L ~/.pyenv/versions/3.8.3/lib -o bin/playlister playlister.c -lpython3.8 -lpthread -lm -lutil -ldl
fi
