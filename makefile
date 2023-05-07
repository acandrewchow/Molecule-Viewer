CC = clang
CFLAGS = -Wall -std=c99 -pedantic
LIBS = -lm
PYTHON_INCLUDE_LOCAL = -I/Library/Frameworks/Python.framework/Versions/3.10/include/python3.10 -I/Library/Frameworks/Python.framework/Versions/3.10/include/python3.10
PYTHON_LIB_LOCAL = /Library/Frameworks/Python.framework/Versions/3.10/lib/python3.10/config-3.10-darwin -ldl -framework CoreFoundation

# python3-config --includes
# python3-config --prefix
# python3-config --libs

all: _molecule.so

clean:
	rm -rf *.o *.so main

libmol.so: mol.o
	$(CC) mol.o -shared -o libmol.so $(LIBS)

_molecule.so: molecule_wrap.o libmol.so
	$(CC) molecule_wrap.o -shared -o _molecule.so libmol.so -L$(PYTHON_LIB_LOCAL) -lpython3.10 $(LIBS) -dynamiclib

mol.o: mol.c mol.h
	$(CC) $(CFLAGS) -c mol.c -fPIC -o mol.o 

molecule_wrap.c: molecule.i 
	swig -python molecule.i

molecule_wrap.o: molecule_wrap.c mol.c
	$(CC) $(CFLAGS) -I$(PYTHON_INCLUDE_LOCAL) -c molecule_wrap.c -fPIC -o molecule_wrap.o