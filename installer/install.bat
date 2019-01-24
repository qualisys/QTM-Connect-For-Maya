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

set "MAYA_64_ROOT_PATH=C:\Program Files\Autodesk"
set "MAYA_32_ROOT_PATH=C:\Program Files (x86)\Autodesk"
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

:while_version_not_decided

rem Ask user which version of unreal to install to
echo.
echo "Installed versions:"
dir /A:D /B "%MAYA_ROOT_PATH%"
echo.
set /p MAYA_VERSION_FOLDER="Select Maya version to install to: "

rem If nothing was typed by user
if "%MAYA_VERSION_FOLDER%"=="" (
    goto :while_version_not_decided
)

set "MAYA_ROOT_PATH=%MAYA_ROOT_PATH%\%MAYA_VERSION_FOLDER%"

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

rem Get 'My documents' path
powershell "[environment]::getfolderpath(\"mydocuments\")" > temp.txt
set /p MY_DOCS_PATH=<temp.txt
set "MAYA_PROJECT_PATH=%MY_DOCS_PATH%\maya\projects\qualisys-example"

rem Copy example project to 'My Documents'\maya\projects\.
xcopy  "%MAYA_PLUGIN_SOURCE_PATH%\example" "%MAYA_PROJECT_PATH%\"  /e /i /h /Y
set "QUALISYS_EXAMPLE_SCENE=%MAYA_PROJECT_PATH%\QAvatar.mb"

rem Run maya from command line and execute install script

echo "Installing plugin..."
start /b "Install plugin..." "%MAYA_EXE_PATH%" -file "%QUALISYS_EXAMPLE_SCENE%" -command "python("""import qtm_connect_maya;import qtm_connect_maya.mayaui;qtm_connect_maya.mayaui.install();""");"

rem Wait let it install (hack)
ping 127.0.0.1 -n 10 > nul

start "" "%MAYA_PROJECT_PATH%"

echo "DONE!"
pause