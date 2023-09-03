var map;

$(window).on("map:init", function (event) {
    map = event.detail.map;
    map.setView(new L.LatLng(-32.37203571087116, 143.67483653628386), 3);

    if (longitude && latitude && modelResult) {
        var textIcon = L.divIcon({
        className: 'text-icon',
        html: '<div class="text-label" ><img src="/static/gis/img/location_marker_2.png" alt="Marker Image">' + modelResult + '</div>'
    });

    var marker = L.marker([longitude, latitude], { icon: textIcon }).addTo(map);
    map.setView(new L.LatLng(longitude, latitude), 7);

    }

});




function handleInputSelection() {
    event.preventDefault();

    var selectedMethod = document.querySelector('input[name="area_selection_js"]:checked');
    var outputDiv = document.getElementById("selected-option-output_js");

    if (selectedMethod) {
        var selectedValue = selectedMethod.value;
        if (selectedValue === "Upload_js") {
            outputDiv.innerHTML = "You have selected to upload .shp file";
        } else if (selectedValue === "Enter_js") {
            outputDiv.innerHTML = "You have selected to enter the coordinates";

        } else if (selectedValue === "Select_js") {
            outputDiv.innerHTML = "You have selected to select area on the map";
        }
    }
     else {
        outputDiv.innerHTML = "No selection has been made";
    }
}

document.getElementById("submit3").addEventListener("click", handleInputSelection);





