# FabriSlicer v1

FabriSlicer is a custom GUI slicer tool designed for generating toolpaths and GCODE for the FabriSonic Soniclayer 1200 at UTS. It allows you to import STL files, customize build dimensions, apply offsets, and generate ready-to-run GCODE files with custom weld and texturising speeds.

---

## Getting Started (Using the Pre-Compiled Executable)

The easiest way to use FabriSlicer is by running the standalone Windows executable. You do not need to install Python or any dependencies to use this method.

1. Navigate to the `FabriSlicer\release` directory.
2. Double-click **`FabriSlicer v1.exe`** to launch the application.
3. Upon running the application for the first time, it will automatically generate two new folders right next to the executable:
   - `profiles/`: This is where your custom `.uam` slicing profiles are saved and loaded from.
   - `settings/`: This contains `fabri.set`, which remembers GUI settings.

---

## Building from Source

If you make modifications to the Python source code (located in the `FabriSlicer/src` folder) and want to generate a new `.exe`, follow these steps:

1. Open the `FabriSlicer` directory.
2. Double-click the **`build.bat`** script.
3. The script will automatically:
   - Install `pyinstaller` and `Pillow` into your virtual environment (if not already installed).
   - Convert the PNG icon into a Windows-compatible `.ico` format.
   - Compile the entire application into a single `.exe` file.
4. Once the terminal window says "Build complete!", you will find your new executable inside the `FabriSlicer\release` folder.

---

## Directory Structure Overview

- **`FabriSlicer\release\`**: Contains the compiled executable and generated `profiles`/`settings` directories.
- **`FabriSlicer\src\`**: Contains the core Python scripts (`fabrigui.py`, `fabrislicer.py`, etc.).
- **`FabriSlicer\build.bat`**: The automated script for compiling the Python source into an executable.
- **`FabriSlicer\icon\`**: Contains the logo/icon files used by the application and the executable.
