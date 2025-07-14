# DBS_Monitoring_App
Instrument for monitoring and managing experimental data at a scientific facility.

## Basic functionality
- Simple and intuitive interface for users with minimal technical skills.
- Customize folder paths, file templates, and file types through a two-column interface.
- Dynamic selection of file types from JSON settings.
- Error handling with clear messages and color coding (green for success, red for errors).
- Save only new experiment numbers with the ability to edit them.
- Editing JSON settings via the interface with the "Back", "Reset" and "Save" buttons.

## Build ```.exe```
1. Run in terminal ```pip install pyinstaller``` (pip required)
2. Then go to ```cd {dir of the app}``` and build by ```pyinstaller --onefile --add-data "templates;templates" app.py```
```.exe``` file will be in the ```\dist``` dir.

## Technology
- Programming language: Python.
- Framework: Flask.
- Interface: HTML, CSS, JavaScript.
- Packaging: PyInstaller for creating an executable file (.exe).

## Future improvements
- Automatic folder monitoring by timer.
- Localization of the interface (Russian/English).
- Adding data preprocessing functionality.

This project was created for scientific groups to simplify the process of monitoring and managing experimental data.