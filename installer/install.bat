@echo off

fltmc >nul 2>&1 && (
  rem Running as admin.
) || (
  echo "ERROR: Installer must be run as admin."
  pause
  exit 1
)

rem Change working directory to directory of batch file using (not always same as script dir)
cd /D "%~dp0"

set "MAYA_64_ROOT_PATH=C:\Program Files\Autodesk\Maya2018"
set "MAYA_32_ROOT_PATH=C:\Program Files (x86)\Autodesk\Maya2018"
set MAYA_ROOT_PATH=""
set CUSTOM_MAYA_ROOT_PATH=""

:while

rem Localize Maya root path:

if exist "%MAYA_64_ROOT_PATH%" (
    echo "Found 64bit"
    set "MAYA_ROOT_PATH=%MAYA_64_ROOT_PATH%"
) else if exist "%MAYA_32_ROOT_PATH%" (
    echo "Found 32bit"
    set "MAYA_ROOT_PATH=%MAYA_32_ROOT_PATH%"
) else if exist "%CUSTOM_MAYA_ROOT_PATH%" (
    echo "Found custom path %CUSTOM_MAYA_ROOT_PATH%"
    set "MAYA_ROOT_PATH=%CUSTOM_MAYA_ROOT_PATH%"
)

if exist "%MAYA_ROOT_PATH%" (
    echo "Maya root found: %MAYA_ROOT_PATH%"
) else ( 
    echo "Maya installation folder not found: %MAYA_ROOT_PATH%"
    set /p CUSTOM_MAYA_ROOT_PATH="Please enter Maya installation path: "
    goto :while
)

set "MAYA_EXE_PATH=%MAYA_ROOT_PATH%\bin\maya.exe"

if exist "%MAYA_EXE_PATH%" (
    echo "Maya.exe found: %MAYA_EXE_PATH%"
) else (
    echo "Maya.exe NOT found at: %MAYA_EXE_PATH%"
    pause
    exit 1
)

rem Localize "QTM Connect Maya" plugin root path:

set "MAYA_PLUGIN_SOURCE_PATH=%cd%\.."
set "VERIFY_IF_CORRECT_FOLDER=%MAYA_PLUGIN_SOURCE_PATH%\mayaui.py"

if exist "%VERIFY_IF_CORRECT_FOLDER%" (
    echo "QTM Connect Maya plugin found."
) else (
    echo "QTM Connect Maya plugin not found. Installer must be in plugin root."
    pause
    exit 1
)

rem Copy "QTM Connect Maya" plugin to maya_root_path/bin:

set "QTM_CONNECT_MAYA_FOLDER_NAME=qtm_connect_maya"
set "MAYA_PLUGIN_DEST_PATH=%MAYA_ROOT_PATH%\bin\%QTM_CONNECT_MAYA_FOLDER_NAME%"
echo "Copying folder %MAYA_PLUGIN_SOURCE_PATH% to %MAYA_PLUGIN_DEST_PATH%..."

xcopy  "%MAYA_PLUGIN_SOURCE_PATH%" "%MAYA_PLUGIN_DEST_PATH%" /e /i /h /Y

rem Run maya from command line and execute install script

echo "Installing plugin..."
start /wait "Install plugin..." "%MAYA_EXE_PATH%" -command "python("""import qtm_connect_maya;import qtm_connect_maya.mayaui;qtm_connect_maya.mayaui.install()""");"

echo "DONE!"
pause