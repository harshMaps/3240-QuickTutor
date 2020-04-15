var map;
function createMap(){
    var options = {
        center: {lat: 43.654, lng: -79.383},
        zoom = 10
    };

    map = new google.map.Maps(document.getElementById('map'), options);
}