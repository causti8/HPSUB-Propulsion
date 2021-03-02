#*********************************************************
# Makefile for XROTOR Version 6.80
# M.Drela
# H.Youngren 11/28/98
#*********************************************************
# crotor, espara, esprop targets added
# PJC, Esotec Developments, 18 July 2011
# esloft, eslplots, esxfsubs targets added Aug 2011
#*********************************************************
PLTLIB = ../plotlib/libPlt.a
#PLTLIB = ../plotlib/libPltDP.a

SRC = ../src

##--------------------------
## mingw  gfortran
#BDIR = d:\gcc452\bin
#FC = $(BDIR)\gfortran.exe
#CC  = $(BDIR)\gfortran.exe 
FC = gfortran
CC = gfortran
DP =
FFLAGS  = -O -pipe $(DP)
CFLAGS  = -O -pipe
#AR = $(BDIR)\ar.exe r
#RANLIB = $(BDIR)\ranlib.exe 
AR = ar r
RANLIB = ranlib
LINKLIB = -lgdi32
LFLAGS = -Wl,--strip-debug  -static-libgfortran -static-libgcc 
LIBS =
###================================================

PROGS = xrotor jplot jplote esprop
#PROGS = xrotor

XROTOROBJS = xrotor.o xoper.o xdesi.o \
             xmodi.o  xaero.o xjmap.o xio.o \
             xnoise.o xrotpl.o xcasepl.o xbend.o \
             xinte.o xutils.o jputil.o \
             plutil.o modify.o srclin.o spline.o userio.o vortex.o \
             plotdata.o espara.o crotor.o \
             esloftx.o eslplots.o esxfsubs.o 

JPLOTOBJS  = jplot.o  xutils.o jputil.o userio.o
JPLOTEOBJS = jplote.o xutils.o jputil.o userio.o
ESPROPOBJS = esprop.o esplots.o userio.o


all:	 $(PROGS)

install: 
	$(INSTALLCMD) $(PROGS) $(BINDIR)

clean:
	-/bin/rm *.o
	-/bin/rm $(PROGS)
	-/bin/rm plot.ps


### Make targets

xrotor: $(XROTOROBJS)
	$(FC) -v -o xrotor.exe $(LFLAGS) $(XROTOROBJS) $(PLTLIB) $(LINKLIB)

jplot: $(JPLOTOBJS)
	$(FC) -v -o jplot.exe  $(LFLAGS) $(JPLOTOBJS) $(PLTLIB) $(LINKLIB)

jplote: $(JPLOTEOBJS)
	$(FC) -v -o jplote.exe $(LFLAGS) $(JPLOTEOBJS) $(PLTLIB) $(LINKLIB)

esprop: $(ESPROPOBJS)
	$(FC) -v -o esprop.exe $(LFLAGS) $(ESPROPOBJS) $(PLTLIB) $(LINKLIB)


xrotor.o: $(SRC)/xrotor.f $(SRC)/XROTOR.INC
	$(FC) -c -I$(SRC) $(FFLAGS) $(SRC)/xrotor.f
xoper.o: $(SRC)/xoper.f $(SRC)/XROTOR.INC
	$(FC) -c -I$(SRC) $(FFLAGS) $(SRC)/xoper.f
xio.o: $(SRC)/xio.f $(SRC)/XROTOR.INC
	$(FC) -c -I$(SRC) $(FFLAGS) $(SRC)/xio.f
xdesi.o: $(SRC)/xdesi.f $(SRC)/XROTOR.INC
	$(FC) -c -I$(SRC) $(FFLAGS) $(SRC)/xdesi.f
xmodi.o: $(SRC)/xmodi.f $(SRC)/XROTOR.INC
	$(FC) -c -I$(SRC) $(FFLAGS) $(SRC)/xmodi.f
xaero.o: $(SRC)/xaero.f $(SRC)/XROTOR.INC
	$(FC) -c -I$(SRC) $(FFLAGS) $(SRC)/xaero.f
xjmap.o: $(SRC)/xjmap.f $(SRC)/XROTOR.INC
	$(FC) -c -I$(SRC) $(FFLAGS) $(SRC)/xjmap.f
xnoise.o: $(SRC)/xnoise.f $(SRC)/XROTOR.INC
	$(FC) -c -I$(SRC) $(FFLAGS) $(SRC)/xnoise.f
xrotpl.o: $(SRC)/xrotpl.f $(SRC)/XROTOR.INC
	$(FC) -c -I$(SRC) $(FFLAGS) $(SRC)/xrotpl.f
xcasepl.o: $(SRC)/xcasepl.f $(SRC)/XROTOR.INC
	$(FC) -c -I$(SRC) $(FFLAGS) $(SRC)/xcasepl.f
xbend.o: $(SRC)/xbend.f $(SRC)/XROTOR.INC
	$(FC) -c -I$(SRC) $(FFLAGS) $(SRC)/xbend.f
xinte.o: $(SRC)/xinte.f $(SRC)/XROTOR.INC
	$(FC) -c -I$(SRC) $(FFLAGS) $(SRC)/xinte.f
xutils.o: $(SRC)/xutils.f
	$(FC) -c -I$(SRC) $(FFLAGS) $(SRC)/xutils.f
srclin.o: $(SRC)/srclin.f
	$(FC) -c -I$(SRC) $(FFLAGS) $(SRC)/srclin.f
plutil.o: $(SRC)/plutil.f
	$(FC) -c -I$(SRC) $(FFLAGS) $(SRC)/plutil.f
modify.o: $(SRC)/modify.f
	$(FC) -c -I$(SRC) $(FFLAGS) $(SRC)/modify.f
spline.o: $(SRC)/spline.f
	$(FC) -c -I$(SRC) $(FFLAGS) $(SRC)/spline.f
userio.o: $(SRC)/userio.f
	$(FC) -c -I$(SRC) $(FFLAGS) $(SRC)/userio.f
vortex.o: $(SRC)/vortex.f
	$(FC) -c -I$(SRC) $(FFLOPT) $(SRC)/vortex.f
plotdata.o: $(SRC)/plotdata.f
	$(FC) -c -I$(SRC) $(FFLAGS) $(SRC)/plotdata.f
espara.o: $(SRC)/espara.f $(SRC)/ESPARA.INC
	$(FC) -c -I$(SRC) $(FFLAGS) $(SRC)/espara.f
crotor.o: $(SRC)/crotor.f $(SRC)/XROTOR.INC
	$(FC) -c -I$(SRC) $(FFLAGS) $(SRC)/crotor.f
esloftx.o: $(SRC)/esloftx.f $(SRC)/XROTOR.INC
	$(FC) -c -I$(SRC) $(FFLAGS) $(SRC)/esloftx.f
eslplots.o: $(SRC)/eslplots.f $(SRC)/XROTOR.INC
	$(FC) -c -I$(SRC) $(FFLAGS) $(SRC)/eslplots.f
esxfsubs.o: $(SRC)/esxfsubs.f $(SRC)/XROTOR.INC
	$(FC) -c -I$(SRC) $(FFLAGS) $(SRC)/esxfsubs.f

jplot.o: $(SRC)/jplot.f
	$(FC) -c -I$(SRC) -std=legacy $(FFLAGS) $(SRC)/jplot.f
jplote.o: $(SRC)/jplote.f
	$(FC) -c -I$(SRC) $(FFLAGS) $(SRC)/jplote.f
jputil.o: $(SRC)/jputil.f
	$(FC) -c -I$(SRC) $(FFLAGS) $(SRC)/jputil.f

esprop.o: $(SRC)/esprop.f
	$(FC) -c -I$(SRC) $(FFLAGS) $(SRC)/esprop.f
esplots.o: $(SRC)/esplots.f
	$(FC) -c -I$(SRC) $(FFLAGS) $(SRC)/esplots.f






