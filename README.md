# project_orefox_d4
django 4 upgrade for project_orefox

## How to run this app in Local Machine (Linux Recommended)  
- Clone this project
- Create and activate virtual environment (venv)
- Goto 'web' directory and install requirements with through pip ```pip install -r requirements.txt```
- Goto your virtual environment and find the following file, `(venv)/Lib/site-packages/djconfig/admin.py` and change `from django.conf.urls import url` to `from django.urls import re_path as url`
- Create a .env file in 'web' directory and put all the default variables from .env.structure.txt
- In the 'web' directory, install GDAL using `pip install GDAL-3.3.3-cp38-cp38-win_amd64.whl`
- Clone this fork of the Spirit package outside of this repo: https://github.com/GeorgeKandamkolathy/Spirit
- Within this repo take the spirit file and replace the installed spirit folder within the `(venv)/lib/python3.8/site-packages`.
- Then install tensorflow using `pip install tensorflow`
- Run `python manage.py makemigrations`
- Make sure you have the latest project version and run `python manage.py spiritinstall`
- Migrate the database with `python manage.py migrate`
- Now start the application with `python manage.py runserver` and visit this link http://127.0.0.1:8000/
- Change the url to `http://127.0.0.1:8000/debug/` to load dummy data. It will take around 30 seconds for the data to load.
- Log into the platform using `username: admin@email.com` and `password: admin`
- Now you are ready to use the application

# Windows Installation Guide for GDAL
If installing gdal via pip either doesn't work or isnt recognized, doing the following will work on both Windows 10 and 11:

- Run `pip debug --verbose`  and look for compatible tags, e.g., *cp38-cp38-win_amd64*
- First, download the GDAL wheel from [Christoph Gohlke's Unofficial Windows Binaries for Python Extension Packages](https://www.lfd.uci.edu/~gohlke/pythonlibs/#gdal). Use the tags found above to determine which wheel you download.
- Install via `pip install '/path/to/GDAL-3.3.3‑cp38-cp38-win_amd64.whl'` (or whatever wheel it was you downloaded)
- Navigate to `/path/to/venv/Lib/site-packages/osgeo/` and take note of the gdalXXX.dll files name e.g., gdal304.dll
- The version name of the dll found above needs to be added to the `/path/to/venv/lib/site-packages/django/contrib/gis/gdal/libgdal.py` file here:
```python
elif os.name == 'nt':
    # Windows NT shared libraries
    lib_names = ['gdal304', 'gdal300', 'gdal204', 'gdal203', 'gdal202', 'gdal201', 'gdal20']
	# ^ add dll name to this array if its not there
```
- Add the following code block to your django settings.py (within the main folder project folder, not site-packages) before the initialization of any packages:
```python
if os.name == 'nt':
    VENV_BASE = os.environ['VIRTUAL_ENV']
    os.environ['PATH'] = os.path.join(VENV_BASE, 'Lib\\site-packages\\osgeo') + ';' + os.environ['PATH']
    os.environ['PROJ_LIB'] = os.path.join(VENV_BASE, 'Lib\\site-packages\\osgeo\\data\\proj') + ';' + os.environ['PATH']
```
- Finished! Now continue with the regular setup of django.

Note: If there are still issues, it's possible you might need to install GDAL on windows. As there aren't any binaries available on the GDAL website and you have to build it yourself. The easiest way to install it is by using the network installer for [OSGeo4W](https://trac.osgeo.org/osgeo4w/), just do an express installation but make sure to select GDAL as an additional package.

# Migration Error

In case you are facing some kind of migration error, 
- Go to web directory
- Delete db.sqlite3(only within web)
- Delete __pycache__ folders in each folder
- Delete all files and folders (except __init__.py) within migration folder present in most app folders 
- Run `python manage.py makemigrations`
- Then run `python manage.py spiritinstall`
- Migrate the database with `python manage.py migrate`
- Now start the application with `python manage.py runserver` and visit this link http://127.0.0.1:8000/
- Change the url to `http://127.0.0.1:8000/debug/` to load dummy data. It will take around 30 seconds for the data to load.
- Log into the platform using `username: admin@email.com` and `password: admin`
- Now you are ready to use the application