////////// image extraction for model training:

// 1. Create a mapping of mine names to coordinates
function extract_images_for_training() {
    const mineCoordinates = [
        { name: 'MineA', lat: 12.345, lng: 67.890 },
        { name: 'MineB', lat: 34.567, lng: 123.456 },
        // Western Australia Mines
        { name: 'Paddington Gold Mine', lat: -30.486926838092423, lng: 121.34965320007612 },
        { name: 'Jundee Mine Site', lat: -26.35855929832597, lng: 120.61993639829684 },
        { name: 'Yarrie mine', lat: -20.613825889520538, lng: 120.30428194110846 },
        { name: 'Marvel Loch Gold Mine', lat: -31.46987566845665, lng: 119.5039658588994 },
        { name: 'Red 5 Darlot Gold Mine', lat: -27.89631771473762, lng: 121.27266435889938 },
        { name: 'Fortnum Gold Mine', lat: -25.329454687825642, lng: 118.3561401588994 },
        { name: 'Mount Tom Price mine', lat: -22.75127439405091, lng: 117.76861502945167 },
        { name: 'Nicolsons Gold Mine', lat: -18.408848436238237, lng: 127.3550782588994 },
        { name: 'Maitland Mine', lat: -26.599909500422388, lng: 120.18420332945166 },
        { name: 'Warriedar Mine', lat: -29.102346914103425, lng: 117.00640587055616 },
        { name: 'Kailis Mine Site', lat: -28.840010287383674, lng: 121.28875964110847 },
        { name: 'Mulgarrie Mine', lat: -30.382666121536882, lng: 121.51359732945166 },
        { name: 'Whundo Mine', lat: -21.08024582296821, lng: 116.92805752945168 },
        { name: 'Western Queen Mine', lat: -27.52271903201436, lng: 117.12482935889939 },
        { name: 'Mount Caudan Mine', lat: -31.61943318697541, lng: 119.55333955889937 },
        { name: 'Tuckabianna Gold Mine', lat: -27.455271044742403, lng: 118.14536145889939 },
        { name: 'Reid Find Mine', lat: -31.067534979424256, lng: 121.1073727588994 },
        // NSW Mines
        { name: 'Evolution Mining/Barrick Gold Mine', lat: -33.64161929078166, lng: 147.3956318088059 },
        { name: 'Tarrawonga Coal Mine', lat: -30.63931356958991, lng: 150.1674814989051 },
        { name: 'Centennial Cooranbong Mine', lat: -33.05994536930686, lng: 151.5025607721257 },
        { name: 'Golden Gate Gold Mine', lat: -31.45333558228203, lng: 151.18502663900847 },
        { name: 'Peakhill Open Cut Gold Mine', lat: -32.72278873586718, lng: 148.1948194883326 },
        { name: 'Canbelego Mine', lat: -31.555330899999994, lng: 146.31854808219822 },
        { name: 'Ravensworth Mine', lat: -32.46078189999999, lng: 151.0191393294371 },
        { name: 'Cadia Hill Gold Mine', lat: -33.45795684338745, lng: 148.99655962943706 },
        { name: 'Integra Underground Coal Mine', lat: -32.46473900272108, lng: 151.1307366294371 },
        { name: 'Springvale Coal Mine', lat: -33.404937700000005, lng: 150.10656931164598 },
        { name: 'Bulga Open Cut Mine', lat: -32.6777944355827, lng: 151.0927310821982 },
        { name: 'Manuka Mine', lat: -32.22992859999998, lng: 145.73731199998932 },
        { name: 'CSA Mine', lat: -31.409104156838456, lng: 145.79988100835322 },
        { name: 'BHP Mt Arthur Coal', lat: -32.34244005851337, lng: 150.8870185937751 },
        { name: 'Drayton Mine', lat: -32.35511333355271, lng: 150.90074562943707 },
        { name: 'Whitehaven - Rocglen Coal Mine', lat: -30.769708652207772, lng: 150.27045794405353 },
        { name: 'Cordeaux Mine', lat: -34.32476283264475, lng: 150.76802021005184 },
        { name: 'Atlas Mine', lat: -33.93893223106299, lng: 143.39627594722813 },
        { name: 'Beltana Highwall Mine', lat: -32.7088078715575, lng: 151.1099126588849 },
        { name: 'Glencore - Mount Owen', lat: -32.4126679100384, lng: 151.09067633643411 },
        { name: 'Boggabri Coal Mine', lat: -30.62945705303399, lng: 150.1448102294371 },
        { name: 'Swamp Creek Mine', lat: -35.89648738400334, lng: 147.63256069998934 },
        { name: 'Clean Teq Sunrise Mine', lat: -32.78201549199584, lng: 147.43456724658586 },
        { name: 'Endeavor Mine', lat: -31.162616231035297, lng: 145.6552043999893 },
        { name: 'Snapper Mineral Sands Mine', lat: -33.440019280897715, lng: 142.14843622943712 },
        { name: 'Hunter Valley Operations', lat: -32.50080533275013, lng: 150.98917365304214 },
        { name: 'Hera Mine', lat: -32.10540725997068, lng: 146.31015945888487 },
        { name: 'Ginkgo Mine', lat: -33.37299988003401, lng: 142.21490134722814 },
        { name: 'Duralie Coal', lat: -32.317872533360834, lng: 151.9201602588848 },
        { name: 'Bulga-Warkworth Mine', lat: -32.64997263540696, lng: 151.07915708833264 },
        { name: 'Narrabri Coal Mine', lat: -30.520239134117404, lng: 149.8964524588848 },
        { name: 'Moolarben coal mine', lat: -32.24886380133537, lng: 149.77485625888482 }
    ];

    const zoomLevel = 10; // Set your desired zoom level

    // Iterate through the mineCoordinates array and convert each coordinate to tile coordinates
    const tileCoordinates = mineCoordinates.map(coord => {
        const { name, lat, lng } = coord;
        return {
            name: name,
            tile: convertLatLngToTile(lat, lng, zoomLevel)
        };
    });

    // Print or log the tile coordinates for each mine
    tileCoordinates.forEach(coord => {
        console.log(`Mine Name: ${coord.name}`);
        console.log(`Tile Coordinates: X: ${coord.tile.x}, Y: ${coord.tile.y}, Zoom: ${coord.tile.z}`);
    });
}