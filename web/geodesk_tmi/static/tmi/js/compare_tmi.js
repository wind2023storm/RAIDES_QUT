var map;

function addTileOverlay() {
    L.tileLayer('/static/tmi/img/output/{z}/{x}/{y}.png', {
        minZoom: 2,
        maxZoom: 18,
        attribution: 'ESO/INAF-VST/OmegaCAM',
        tms: true,
        bounds: [
            new L.LatLng(-37.368002734080335, 140.5029985763527),
            new L.LatLng(-28.145396997322745, 153.61338977456407)
        ]
    }).addTo(map);
    imageBounds = [[-29, 138], [-11.9, 153.6]];
    L.control.scale().addTo(map);

}

function convertLatLngToTile(lat, lng, zoom) {
  var tileSize = 256;
  var scale = Math.pow(2, zoom);

  var latRad = lat * (Math.PI / 180);
  var lngRad = lng * (Math.PI / 180);
  var pixelX = ((lng + 180) / 360) * tileSize * scale;
  var pixelY = (1 - Math.log(Math.tan(latRad) + 1 / Math.cos(latRad)) / Math.PI) * (tileSize / 2) * scale;
  var tileX = Math.floor(pixelX / tileSize);
  var tileY = Math.floor(pixelY / tileSize);
  tileY = (Math.pow(2, zoom) - 1) - tileY;
  return { x: tileX, y: tileY, z: zoom };
}

function updateImages(comp_img_path) {
    const randomNumber1 = Math.floor(Math.random() * 1000);
    const selectedImageUrl = `/static/tmi/img/to_display/img.png?rand=${randomNumber1}`;
    document.getElementById('selectedImage').src = selectedImageUrl;

    const randomNumber2 = Math.floor(Math.random() * 1000);
    const comparedImageUrl = `/static/tmi/img/to_compare/img.png?rand=${randomNumber2}`;
    document.getElementById('comparedImage').src = comparedImageUrl;
    }

var zoomLevel;
var scale;
var selected_latitude;
var selected_longitude;

document.getElementById('zoom5km').addEventListener('click', function () {
    zoomLevel = 11;
    scale = "5km";
    console.log("5km selected")
    updateMapZoom(zoomLevel);
});

document.getElementById('zoom10km').addEventListener('click', function () {
    zoomLevel = 10;
    scale = "10km";
    console.log("10km selected")
    updateMapZoom(zoomLevel);
});

document.getElementById('zoom20km').addEventListener('click', function () {
      zoomLevel = 9;
      scale = "20km";
      console.log("20km selected")
      updateMapZoom(zoomLevel);
});

document.getElementById('back').addEventListener('click', function () {
      console.log("back selected")
      updateMapZoomAndCoords(prev_lat, prev_long, pre_zoom)

});


function updateMapZoom(zoomLevel) {
    map.setView(new L.LatLng(-33.888677964124916, 143.99230957031253), zoomLevel);
}

function updateMapZoomAndCoords(latitude, longitude, zoomLevel) {
    map.setView(new L.LatLng(selected_latitude, selected_longitude), zoomLevel);
}


$(window).on("map:init", function (event) {
    map = event.detail.map;
    map.doubleClickZoom.disable();

    map.setView(new L.LatLng(-32.372035, 143.67483653), 6);

    addTileOverlay();


    map.on('dblclick', function(event) {

        document.getElementById('startMessage').style.display = 'none';

        selected_latitude = event.latlng.lat;
        selected_longitude = event.latlng.lng;

        console.log("Lat, Lon : " + selected_latitude + ", " + selected_longitude);

        var lat = selected_latitude;
        var lng = selected_longitude;

        var tileCoordinates = convertLatLngToTile(selected_latitude, selected_longitude, zoomLevel);
        console.log('Tile Coordinates - X:', tileCoordinates.x, 'Y:', tileCoordinates.y, 'Z:', tileCoordinates.z);


        var similarityResult;

        $.ajax({
            url: 'http://127.0.0.1:8000/tmi/output_model_result',
            type: 'POST',
            data: {
                'latitude': selected_latitude,
                'longitude': selected_longitude,
                "scale" : scale,
                'csrfmiddlewaretoken': csrf_token
            },
            dataType: "json",
            success: function(response) {
                var modelResult = response.model_result;
                var path_to_compared_image = response.path_to_compared_image;
                similarityResult = response.similarity_result;

                console.log("Model Result:", modelResult);
                console.log("SIM Model Result:", similarityResult); //works

                if (modelResult) {
                    var modelResultTextElement = document.getElementById('modelResultText');
                    modelResultTextElement.textContent = "Model Result: " + modelResult;
                    updateImages(path_to_compared_image);
                    document.getElementById('scale').textContent = scale;
                    document.getElementById('latitude').textContent = selected_latitude;
                    document.getElementById('longitude').textContent = selected_longitude;

                    var tileMarker = L.icon({
                        iconUrl: '/static/tmi/img/location_marker_4.png',
                        iconSize: [64, 64],
                        iconAnchor: [16, 32],
                        popupAnchor: [0, -32]
                    });


                    var marker = L.marker([selected_latitude, selected_longitude], {
                        icon: tileMarker
                    }).addTo(map);

                    marker.bindPopup(modelResult).openPopup();

                    map.setView(new L.LatLng(selected_latitude, selected_longitude), zoomLevel);
                }


                console.log("3SIM Model Result:", similarityResult);

                $.ajax({
                    url: 'http://127.0.0.1:8000/tmi/store_results',
                    type: 'POST',
                    data: {
                        'latitude_to_store': selected_latitude,
                        'longitude_to_store': selected_longitude,
                        'similarity_to_store': similarityResult,
                        "scale_to_store" : scale,
                        'csrfmiddlewaretoken': csrf_token
                    },
                    dataType: "json",
                    success: function(response) {
                        updateTable(response.searchResults);
                        console.log("data is sent");
                        console.log("2SIM Model Result:", similarityResult);
                    },
                    error: function(xhr, errmsg, err) {
                        console.log("Error:", errmsg);
                    }
                });

            },
            error: function(xhr, errmsg, err) {
                console.log("Error:", errmsg);
            }
        });

        $.ajax({
            url: 'http://127.0.0.1:8000/tmi/extract_image',
            type: 'POST',
            data: {
                'tile_X': tileCoordinates.x,
                'tile_Y': tileCoordinates.y,
                'zoom_lvl' : zoomLevel,
                'csrfmiddlewaretoken': csrf_token
            },
            dataType: "json",
            success: function(response) {
                console.log("coordinates are sent");
            },
            error: function(xhr, errmsg, err) {
                console.log("Error:", errmsg);
            }
        });






            // result section
            var resultSection = document.getElementById("instanceResults");
            resultSection.style.display = "block";

            // placeholder text
            document.getElementById('latitude').textContent = "Loading...";
            document.getElementById('longitude').textContent = "Loading...";


            const showResultsButton = document.getElementById('showResultsButton');




    })
})

function updateTable(searchResults) {
  const tableBody = document.querySelector('#resultsTableContainer tbody');
  tableBody.innerHTML = '';
  searchResults.forEach(function(result) {
    const row = document.createElement('tr');
    const cell1 = document.createElement('td');
    cell1.textContent = result.latitude;
    const cell2 = document.createElement('td');
    cell2.textContent = result.longitude;

    const cell3 = document.createElement('td');
    cell3.textContent = result.scale;

    const cell4 = document.createElement('td');
    cell4.textContent = result.similarity;

    row.appendChild(cell1);
    row.appendChild(cell2);
    row.appendChild(cell3);
    row.appendChild(cell4);

    tableBody.appendChild(row);
  });
}



function showRankingTable() {
  const showResultsButton = document.getElementById('showResultsButton');
  const resultsTableContainer = document.getElementById('resultsTableContainer');
  showResultsButton.addEventListener('click', function () {
    if (resultsTableContainer.style.display === 'none') {
      resultsTableContainer.style.display = 'block';
    } else {
      resultsTableContainer.style.display = 'none';
    }
  });
}



