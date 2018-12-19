@echo off

rem Change working directory to directory of batch file using (not always same as script dir)
cd /D "%~dp0"

set "CURRENT_DIR=%cd%"

set "ARCHIVE_NAME=qtm_connect_maya.7z"
set "CONFIG_FILE=config.txt"
set "INSTALLER_FILE=install.bat"

set "CONFIG_FILE_PATH=%CURRENT_DIR%\%CONFIG_FILE%"
set "INSTALLER_FILE_PATH=%CURRENT_DIR%\%INSTALLER_FILE%"

set "ZIP_DIR=%CURRENT_DIR%\7zip"
set "ZIP_EXE=%ZIP_DIR%\7za.exe"
set "ZIP_SFX=%ZIP_DIR%\7zS.sfx"

set "OUT_DIR=%CURRENT_DIR%\output"

rem Create archive
"%ZIP_EXE%" a "%OUT_DIR%\%ARCHIVE_NAME%" ../* "-xr!*.git"

rem Copy install-script & config file
xcopy "%CONFIG_FILE_PATH%" "%OUT_DIR%\" /i /h /Y
xcopy "%INSTALLER_FILE_PATH%" "%OUT_DIR%\" /i /h /Y

rem Create installer
copy /b "%ZIP_SFX%" + "%CONFIG_FILE_PATH%" + "%OUT_DIR%\%ARCHIVE_NAME%" "%OUT_DIR%\QTMConnectForMayaInstaller.exe"

del "%OUT_DIR%\%ARCHIVE_NAME%" /s
del "%OUT_DIR%\%CONFIG_FILE%" /s
del "%OUT_DIR%\%INSTALLER_FILE%" /s