# Microsoft Developer Studio Project File - Name="crotor" - Package Owner=<4>
# Microsoft Developer Studio Generated Build File, Format Version 6.00
# ** DO NOT EDIT **

# TARGTYPE "Win32 (x86) External Target" 0x0106

CFG=crotor - Win32 Release
!MESSAGE This is not a valid makefile. To build this project using NMAKE,
!MESSAGE use the Export Makefile command and run
!MESSAGE 
!MESSAGE NMAKE /f "crotor.mak".
!MESSAGE 
!MESSAGE You can specify a configuration when running NMAKE
!MESSAGE by defining the macro CFG on the command line. For example:
!MESSAGE 
!MESSAGE NMAKE /f "crotor.mak" CFG="crotor - Win32 Release"
!MESSAGE 
!MESSAGE Possible choices for configuration are:
!MESSAGE 
!MESSAGE "crotor - Win32 Release" (based on "Win32 (x86) External Target")
!MESSAGE "crotor - Win32 Debug" (based on "Win32 (x86) External Target")
!MESSAGE 

# Begin Project
# PROP AllowPerConfigDependencies 0
# PROP Scc_ProjName ""
# PROP Scc_LocalPath ""

!IF  "$(CFG)" == "crotor - Win32 Release"

# PROP BASE Use_MFC 0
# PROP BASE Use_Debug_Libraries 0
# PROP BASE Output_Dir ""
# PROP BASE Intermediate_Dir ""
# PROP BASE Cmd_Line "MAKE /f crotor.mak"
# PROP BASE Rebuild_Opt "/a"
# PROP BASE Target_File "crotor.exe"
# PROP BASE Bsc_Name "crotor.bsc"
# PROP BASE Target_Dir ""
# PROP Use_MFC 0
# PROP Use_Debug_Libraries 0
# PROP Output_Dir ""
# PROP Intermediate_Dir ""
# PROP Cmd_Line "make -f crotor.mak"
# PROP Rebuild_Opt "/a"
# PROP Target_File ".\crotor.exe"
# PROP Bsc_Name ""
# PROP Target_Dir ""

!ELSEIF  "$(CFG)" == "crotor - Win32 Debug"

# PROP BASE Use_MFC 0
# PROP BASE Use_Debug_Libraries 1
# PROP BASE Output_Dir "Debug"
# PROP BASE Intermediate_Dir "Debug"
# PROP BASE Cmd_Line "NMAKE /f crotor.mak"
# PROP BASE Rebuild_Opt "/a"
# PROP BASE Target_File "crotor.exe"
# PROP BASE Bsc_Name "crotor.bsc"
# PROP BASE Target_Dir ""
# PROP Use_MFC 0
# PROP Use_Debug_Libraries 1
# PROP Output_Dir "Debug"
# PROP Intermediate_Dir "Debug"
# PROP Cmd_Line "make -f   crotor.mak"
# PROP Rebuild_Opt "/a"
# PROP Target_File "gtest.exe"
# PROP Bsc_Name ""
# PROP Target_Dir ""

!ENDIF 

# Begin Target

# Name "crotor - Win32 Release"
# Name "crotor - Win32 Debug"

!IF  "$(CFG)" == "crotor - Win32 Release"

!ELSEIF  "$(CFG)" == "crotor - Win32 Debug"

!ENDIF 

# Begin Group "crotor"

# PROP Default_Filter "cpp;c;cxx;rc;def;r;odl;idl;hpj;bat;f90;for;f;fpp"
# Begin Source File

SOURCE="..\src\crotor.f"
# End Source File
# Begin Source File

SOURCE=..\src\esloftx.f
# End Source File
# Begin Source File

SOURCE=..\src\espara.f
# End Source File
# Begin Source File

SOURCE=..\src\esxfsubs.f
# End Source File
# Begin Source File

SOURCE=..\src\modify.f
# End Source File
# Begin Source File

SOURCE=..\src\plotdata.f
# End Source File
# Begin Source File

SOURCE=..\src\plutil.f
# End Source File
# Begin Source File

SOURCE=..\src\spline.f
# End Source File
# Begin Source File

SOURCE=..\src\srclin.f
# End Source File
# Begin Source File

SOURCE=..\src\vortex.f
# End Source File
# Begin Source File

SOURCE=..\src\xaero.f
# End Source File
# Begin Source File

SOURCE=..\src\xbend.f
# End Source File
# Begin Source File

SOURCE=..\src\xcasepl.f
# End Source File
# Begin Source File

SOURCE=..\src\xdesi.f
# End Source File
# Begin Source File

SOURCE=..\src\xinte.f
# End Source File
# Begin Source File

SOURCE=..\src\xio.f
# End Source File
# Begin Source File

SOURCE=..\src\xjmap.f
# End Source File
# Begin Source File

SOURCE=..\src\xmodi.f
# End Source File
# Begin Source File

SOURCE=..\src\xnoise.f
# End Source File
# Begin Source File

SOURCE=..\src\xoper.f
# End Source File
# Begin Source File

SOURCE=..\src\xrotor.f
# End Source File
# Begin Source File

SOURCE=..\src\xrotpl.f
# End Source File
# End Group
# Begin Group "jplot/e esprop"

# PROP Default_Filter "cpp;c;cxx;rc;def;r;odl;idl;hpj;bat;f90;for;f;fpp"
# Begin Source File

SOURCE="..\src\esplots.f"
# End Source File
# Begin Source File

SOURCE="..\src\esprop.f"
# End Source File
# Begin Source File

SOURCE="..\src\jplot.f"
# End Source File
# Begin Source File

SOURCE="..\src\jplote.f"
# End Source File
# Begin Source File

SOURCE="..\src\jputil.f"
# End Source File
# Begin Source File

SOURCE="..\src\userio.f"
# End Source File
# Begin Source File

SOURCE="..\src\xutils.f"
# End Source File
# End Group
# Begin Group "Header"

# PROP Default_Filter "h;inc"
# End Group
# Begin Group "Resource Files"

# PROP Default_Filter "ico;cur;bmp;dlg;rc2;rct;bin;rgs;gif;jpg;jpeg;jpe"
# End Group
# End Target
# End Project
