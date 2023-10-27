# Object detection in geophysical images

The geodesk_tmi module encompasses a system that allows users to define a project area and search for similarities to known mineralization sites using a machine learning algorithm. Key features of this project include user input and project area selection, data extraction and pre-processing, similarity search, similarity score generation, and visualization of the results with explanations. However, the similarity search feature is currently not functioning as intended, producing consistently high similarity scores. Further research into feature identification in TMI images is required.

## Table of Contents

- [Project Overview](#project-overview)
- [Project Structure](#project-structure)
- [Project Instructions](#project_instructions)

## Project Overview

This section outlines features included in the developed framework for providing model input and output visualisation. 

Expanding to the /tmi/compare Page
We have created the Django application named “geodesk_tmi”, which followed Orefox GeoDesk platform general structure. Leveraging the techniques employed on the /gis/tmi page, we created the /tmi/compare page. This new page also utilises a Leaflet map and presents the TMI overlay in a similar fashion and reused some of the tmi_overlay.html code.

Coordinate Conversion Method
We developed a method to convert user-selected coordinates into tile coordinates. This method receives latitude, longitude, and zoom level and converts it into the previously described tile directory structure format (i.e., lat: #, lon #, zoom 5 translates into /{z}/{x}/{y}). This took an iterative approach to develop, as certain parameters of the .tif image were unknown, making it difficult to find a reference point for tile coordinate generation. We also employed this function to convert a collection of coordinates for known mine sites, allowing us to generate positive training image sets for the model.

Image Extraction Method
We subsequently developed an image extraction method, utilising the conversion method described above. This method enabled the retrieval of images corresponding to user-selected coordinates from the img/output/ directory. The coordinates are registered from the user double clicking on the map area. These coordinates then get passed to coordinate conversion function … and then retrieve the corresponding tile image copying it into img/to_display folder. 

Zoom Level Selection 
Zoom level selection buttons (Figure #) were implemented to set zoomLevel and scale variables in compare_tmi.js that are used to define the zoom level for tile extraction and search summary display.  

Selected Image Display 
The selected image, which is passed to the model is then displayed on the /tmi/compare page along with the image form the positive samples folder which has the highest similarity percentage with the selected image. This can be seen in Figure #.

Search Summary Display
The user-selected coordinates and selected zoom level are displayed along with the model result summary. This can be seen in Figure #.

Ranking table visualisation and update
The ranking table is provided to visualise the details of each search performed in the active session. It sorts the results by the similarity score, providing coordinate details for each instance. This feature can be seen in Figure #. 


Framework improvement suggestions 
The framework is allowing to explore a wide range of machine learning models, extending beyond the scope of this project. 
It can assist with investigations into models that require a specific image input and delivering percentage similarity values along with paths to the most similar images (positive image sets for model training). 
It enables result accuracy review and visualisation. This section offers insights into potential improvements to this framework.

Advanced Image Area Extraction Method
To improve the framework's capabilities, we recommend an advanced image area extraction method. Unlike the current implementation, which extracts a single tile when double clicked, the advanced method would capture a user-defined area. It would go a step further by retrieving multiple tiles and stitching them together to generate a high-resolution image of the defined area.

Enhanced Ranking Table Functionality
The ranking table can benefit from improvements. Our recommendation is to make the result instances (rows) functional. This means that when a user clicks on a result in the table, the map will zoom into the corresponding location with a previously placed marker. Achieving this involves the implementation of advanced technology and modifications to the compare_tmi.js script, which will incorporate a function capable of receiving coordinates selected in the table and initialising the map.setView() function.

Improved Functionality of Scale Buttons
Minor adjustments can also improve the functionality of the scale buttons. Currently, clicking on any of these buttons activates map.setView(), which is set to a specific coordinate, resulting in zoom. However, this feature can be improved by modifying the compare_tmi.js script to include an advanced updateMapZoom() method. This method would encompass the map.setView() function, adjusting the coordinates to the center of the current map view.

Implementation of an Automatic Testing Pipeline
A significant aspect that was not implemented in this project is the automatic testing pipeline. Addressing this shortcoming should be prioritised in future revisions, as it offers substantial benefits in terms of efficiency and robustness.

User Input Options
The requirements of this project specified three different input methods, i.e. specifying coordinates by manually entering latitude and longitude, uploading a .shp file, or defining an area on the map. We have provided a single option for specifying the coordinates. This needs to be addressed in the future revisions. 

User Input Validation
This is another area that did not get much attention in this projects. For currently implemented input option, an input validation method needs to be developed to handle coordinate submission out of available TMI range.  

Implementation Of Error Handling
More detailed error handling implementation is required to be able to communicate with the user if there was an error during the search process, image extraction, tile overlay functionality, etc. 



## Project Structure
We have created the Django application tha follows Orefox Geodesk Platform general structure. 
We have followed company Guidelines for Programming: https://drive.google.com/drive/folders/1zdl1Sj5JfqQgwdTPyQeEQtGngYgkfSun?usp=drive_link


```plaintext
web/
│
├── geodesk_tmi (Main folder)
    │
    ├── geodesk_tmi_model (Model-related files)
    │   ├── model_samples (Model samples)
    │   │   ├── 10 (Samples within a 10km radius)
    │   │   │   ├── List of image files
    │   │   ├── 20 (Samples within a 20km radius)
    │   │   │   ├── List of image files
    │   │   ├── 5 (Samples within a 5km radius)
    │   │   │   ├── List of image files
    │   ├── negative_samples (Negative samples)
    │   │   ├── List of image files
    │   ├── positive_samples (Positive samples)
    │   │   ├── 10km (Samples within a 10km radius)
    │   │   │   ├── List of image files
    │   │   ├── 20km (Samples within a 20km radius)
    │   │   │   ├── List of image files
    │   │   ├── 5km (Samples within a 5km radius)
    │   │   │   ├── List of image files
    │   ├── ModelTrainer.py
    │   ├── SampleComparison.py
    │
    │
    ├── static (Static files)
    │   ├── tmi (TMI-related static files)
    │   │   ├── img (Image files)
    │   │   │
    │   │   ├── css (CSS files)
    │   │   │   │    
    │   │   │   ├── data-processor.css
    │   │   │
    │   │   ├── js (JavaScript files)
    │   │       ├── compare_tmi.js
    │   │       ├── image_extraction_for_training.js
    │
    ├── templates (HTML templates for the web application)
    │    ├── tmi (TMI templates)
    │        ├── compare_tmi.html
    │
    ├── admin.py (Admin interface configuration)
    ├── apps.py (App configuration)
    ├── README.md (Readme file)
    ├── requirements.txt (Requirements file for Python packages)
    ├── tests.py (Unit tests)
    ├── urls.py (URL routing configuration)
    ├── views.py (Views for the web application)
    

```



## Project Instructions
Installation:
Our project is integrated with the Orefox Geodesk platform. To get started, follow these steps:
1.	Ensure that the Geodesk platform has been properly installed and configured on your system.
2.	Navigate to the geodesk_tmi directory.
3.	Run the requirements.txt file, located within the geodesk_tmi directory. This step will ensure that all necessary dependencies are installed.
Configuring Overlay Tiles:
If overlay tiles are not included with your installation, you'll need to place them in the img/output folder. Additionally, you'll need to adjust the image bounds parameters within the addTileOverlay function found in the compare_tmi.js script. Please note that a set of tiles generated for NSW is included with this submission for your convenience.
Starting the Server:
Once the above steps are completed, cd into web and run the command to start the server
 
Operational Instructions:
After the installation and server startup, you can begin using the project. Here's a quick guide on how to operate it:
1.	Open your preferred web browser and navigate to http://127.0.0.1:8000/.
2.	On the side menu bar, select the reference name relevant to your task.
3.	Choose your desired zoom level using one of the three provided zoom buttons. Selecting a zoom level will define the level for image extraction and model search. Once a zoom level is set, it remains in effect for double-click actions on the map.
4.	Navigate to the location of interest on the map and double-click to define location coordinates. This action also initiates the model to start the comparison.
5.	The location details and a summary of the results are displayed in the bottom right corner of the page.
6.	The selected image and the most similar image are presented in the top right corner of the page.
7.	To view the ranking table and get a comprehensive summary of the results, click the "See Results" button.
8.	Use the "Back" and "Forward" buttons to cycle through the results displayed on the map.
9.	To clear the stored results, click the "Clear All" button.
By following these instructions, you'll be able to use our project within the Orefox Geodesk platform. If you encounter any issues or have further questions, please do not hesitate to contact us for assistance.
