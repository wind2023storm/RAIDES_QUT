# PLATFORM SETUP INSTRUCTIONS
Company Guidelines for Programming: https://drive.google.com/drive/folders/1zdl1Sj5JfqQgwdTPyQeEQtGngYgkfSun?usp=drive_link

## Contents

* [Install PostGIS Database](#install-postgis-database)
* [Using Terminal](#using-terminal)
* [VS CODE EXPLORER](#vs-code-explorer)
* [MacOS GDAL Installation](#macos-gdal-installation)
* [Errors Installing Requirements](#errors-installing-requirements)
* [MacOS Installation Issues](#macos-installation-issues)

## Install PostGIS Database
1. Install the latest version of PostgreSQL from https://www.postgresql.org/download/
2. Go with the default settings for everything except for things mentioned below.
3. Check “ADD TO PYTHON PATH” or something similar on one of the pages.
4. When on this page, select PostGIS in spatial extensions:

![gisExtension](https://github.com/OreFox/project_orefox_d4/assets/92376489/d99aa759-81ab-4218-a292-c6a34283aca2)

5. After the page above, you might encounter a checkbox to create a spatial database, no need to check that.
6. SQL Shell and pgAdmin4 will be installed automatically once the installation above finishes.
7. Open `SQL Shell`. Everything in square brackets is the default value. Hit enter to keep the default values. Only change the default value of Database to `django` and Password to `pass`.

  ![Untitled](https://github.com/OreFox/project_orefox_d4/assets/92376489/b3e91702-cd51-4690-898d-77572643c2a6)

8. Open `pgAdmin4` and log in with the password from above
9. Go to `Servers -> PostgreSQL 15 -> Databases -> django -> extensions`
10. Right-click on extensions and select `create -> extension`
 
 ![Screenshot (3)](https://github.com/OreFox/project_orefox_d4/assets/92376489/54b48055-914b-42f6-a4a7-64f2ad9c0b76)

11. Search and select `postgis` extension from the options(option not available in the image as already added)
  
  ![Screenshot 2023-08-02 171834](https://github.com/OreFox/project_orefox_d4/assets/92376489/434a7042-ab8e-490f-9290-a9e4db27cba7)


## Using Terminal
1. Clone this repo and change directory in the terminal to where the repo is stored. Install Python version 3.8 from https://www.python.org/downloads/release/python-3810/.
2. Use `py -0`	to check if Python version 3.8 is installed.
3. Execute the following (use command prompt in Windows):
 ```shell
py -3.8 -m venv venv
.\venv\Scripts\activate.bat
py -m pip install --upgrade pip
pip install -U setuptools
pip install -U wheel
pip install -r requirements.txt
cd web
pip install GDAL-3.3.3-cp38-cp38-win_amd64.whl
pip install pyopenssl --upgrade
pip install daphne
pip install --upgrade attrs
pip install --upgrade channels
pip install psycopg2 
python manage.py makemigrations
python manage.py migrate
```
4. The second last command might give some yellow warnings that you can ignore.
5. Use `pip list` to check if packages are installed in the virtual environment created using the first two commands above.
6. Install `Firefox` web browser		(contains drivers needed for the platform)

Do the next steps after the steps mentioned below
1. `python manage.py runserver`
2. Visit this link http://127.0.0.1:8000/ and register for a new account.

Now you are ready to use the application

## VS CODE EXPLORER
1. Navigate to the project's web folder and rename `.env_defaults` to `.env` file.
2. Make the below changes in .env
  
![Screenshot 2023-08-03 093340](https://github.com/OreFox/project_orefox_d4/assets/92376489/96889e36-eea9-4e87-b3e8-0356d3d3eca7)

3. Then go to your virtual environment folder (venv) outside the web folder and move to `venv -> Lib -> djconfig -> admin.py` and edit line 29.
  	Change
                  `from django.conf.urls import url`
        to
                  `from django.urls import re_path as url`

## MacOS GDAL Installation
1. Install brew (https://brew.sh/)
2. Run the following command in your terminal: `brew install gdal`
3. Open web/main/settings.py and add the following lines at the end of the file:

```shell
GDAL_LIBRARY_PATH = '/opt/homebrew/Cellar/gdal/3.5.3/lib/libgdal.31.dylib'
GEOS_LIBRARY_PATH = '/opt/homebrew/Cellar/geos/3.11.0/lib/libgeos_c.1.dylib'
```

4. Replace the version numbers with the versions you have installed

# Installation Errors
The following are solutions to the most common problems with the setup.
In case you are still unable to set up the platform, email sahaj@orefox.com with a screenshot of the issue to help you out.

## Errors Installing Requirements
In case you are having issues with particular packages:
- get the name of the package from the error displayed in the terminal
- final that package name in the requirements.txt file
- add `#` to the left of the package name (this comments the package out of the installation process)
- save the requirements.txt file using `ctrl + s`
- install the requirements file again `pip install -r requirements.txt`
- repeat the process for all packages that give errors
- Install the packages that have been commented out using `pip install <package name and version from the requirements.txt file`, e.g. `pip install Pillow==8.4.0`

## MacOS Installation Issues
In case you are facing an issue installing gssapi
- try fixing the missing GSSAPI_MAIN_LIB variable using the command: `export GSSAPI_MAIN_LIB=/System/Library/Frameworks/GSS.framework/Versions/Current/GSS`
- Install Pillow package: `pip install Pillow==8.4.0`
