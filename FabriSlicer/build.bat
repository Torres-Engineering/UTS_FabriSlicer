@echo off
echo Installing PyInstaller and Pillow...
"%~dp0..\.venv\Scripts\pip.exe" install pyinstaller pillow

echo.
echo Converting PNG icon to ICO format...
"%~dp0..\.venv\Scripts\python.exe" -c "from PIL import Image; img = Image.open('%~dp0icon\slicer_icon.png'); img.save('%~dp0icon\slicer_icon.ico', format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])"

echo.
echo Building FabriSlicer into a single .exe...
"%~dp0..\.venv\Scripts\pyinstaller.exe" --noconfirm --onefile --windowed --name "FabriSlicer v1" --icon="%~dp0icon\slicer_icon.ico" --distpath "%~dp0release" --add-data "%~dp0icon;icon" --add-data "%~dp0..\gcode_gen\profiles\default.uam;." "%~dp0src\fabrigui.py"

echo.
echo =======================================================
echo Build complete! 
echo Your executable is located in the "release" folder.
echo.
echo =======================================================
pause
