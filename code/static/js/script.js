function setAllGateColors(color){
  origin = window.location.origin
  // gateColorURL = "{{ url_for('index') }}?color="+color
  // alert("sending POST call to "+gateColorUrl);
  var xhttp = new XMLHttpRequest();
  var red = document.querySelector('.color-picker .red-slider').value;
  var green = document.querySelector('.color-picker .green-slider').value;
  var blue = document.querySelector('.color-picker .blue-slider').value;
  // event.preventDefault();
  //xhttp.open("POST", "{{ url_for('index')}}", true);
  xhttp.open("POST", "/api/gates/color", true);
  xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
  xhttp.send("color="+color+"&gateID=all&red="+red+"&green="+green+"&blue="+blue);
}

function setGatesGreen(){
  origin = window.location.origin
  // gateColorURL = "{{ url_for('index') }}?color="+color
  // alert("sending POST call to "+gateColorUrl);
  var xhttp = new XMLHttpRequest();
  var red = 0;
  var green = 255;
  var blue = 0;
  // event.preventDefault();
  //xhttp.open("POST", "{{ url_for('index')}}", true);
  xhttp.open("POST", "/api/gates/color", true);
  xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
  xhttp.send("color=solid&gateID=all&red="+red+"&green="+green+"&blue="+blue);
}

function setGatesRed(){
  origin = window.location.origin
  // gateColorURL = "{{ url_for('index') }}?color="+color
  // alert("sending POST call to "+gateColorUrl);
  var xhttp = new XMLHttpRequest();
  var red = 255;
  var green = 0;
  var blue = 0;
  // event.preventDefault();
  //xhttp.open("POST", "{{ url_for('index')}}", true);
  xhttp.open("POST", "/api/gates/color", true);
  xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
  xhttp.send("color=solid&gateID=all&red="+red+"&green="+green+"&blue="+blue);
}

function setGatesBlue(){
  origin = window.location.origin
  // gateColorURL = "{{ url_for('index') }}?color="+color
  // alert("sending POST call to "+gateColorUrl);
  var xhttp = new XMLHttpRequest();
  var red = 0;
  var green = 0;
  var blue = 255;
  // event.preventDefault();
  //xhttp.open("POST", "{{ url_for('index')}}", true);
  xhttp.open("POST", "/api/gates/color", true);
  xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
  xhttp.send("color=solid&gateID=all&red="+red+"&green="+green+"&blue="+blue);
}

function setGatesYellow(){
  origin = window.location.origin
  // gateColorURL = "{{ url_for('index') }}?color="+color
  // alert("sending POST call to "+gateColorUrl);
  var xhttp = new XMLHttpRequest();
  var red = 125;
  var green = 125;
  var blue = 0;
  // event.preventDefault();
  //xhttp.open("POST", "{{ url_for('index')}}", true);
  xhttp.open("POST", "/api/gates/color", true);
  xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
  xhttp.send("color=solid&gateID=all&red="+red+"&green="+green+"&blue="+blue);
}

function setGatesWhite(){
  origin = window.location.origin
  // gateColorURL = "{{ url_for('index') }}?color="+color
  // alert("sending POST call to "+gateColorUrl);
  var xhttp = new XMLHttpRequest();
  var red = 50;
  var green = 50;
  var blue = 50;
  // event.preventDefault();
  //xhttp.open("POST", "{{ url_for('index')}}", true);
  xhttp.open("POST", "/api/gates/color", true);
  xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
  xhttp.send("color=solid&gateID=all&red="+red+"&green="+green+"&blue="+blue);
}

function sendElementCommand(command){
  origin = window.location.origin
  // gateColorURL = "{{ url_for('index') }}?color="+color
  // alert("sending POST call to "+gateColorUrl);
  var xhttp = new XMLHttpRequest();
  var branch = document.getElementById('branchInput').value;
  if(command == "update"){
      if(branch==""){
          updateModal.style.display = "none";
          branchAlertModal.style.display = "block";
      }
      else{
          xhttp.open("POST", "/api/gates/system", true);
          xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
          xhttp.send("command="+command+"&gateID=all&branch="+branch);
      }
  }
  else {
      // event.preventDefault();
      xhttp.open("POST", "/api/gates/system", true);
      xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
      xhttp.send("command="+command+"&gateID=all&branch="+branch);
  }
}

var responseTextArray = [];

function getGateList(){
  origin = window.location.origin
  // gateColorURL = "{{ url_for('index') }}?color="+color
  // alert("sending POST call to "+gateColorUrl);
  var xhttp = new XMLHttpRequest();
  var re = /'(\S*)'/g;
  // event.preventDefault();
  xhttp.onreadystatechange = function() {
    if (this.readyState == 4 && this.status == 200) {
      responseTextArray = this.responseText.match(re);
      var text = "";
      for (i = 0; i < responseTextArray.length; i++){
          text += "<div class=\"gate-address id=\"element" + i + "\" onclick=\"gateClick(" + i + ")\">" + i + ": " + responseTextArray[i] + "</div>";
      }
      document.getElementById("gates-list").innerHTML = text;
    }
  };
  xhttp.open("GET", "/api/server/gates", true);
  xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
  xhttp.send("");
}

function gateClick(gate) {
    origin = window.location.origin
    var xhttp = new XMLHttpRequest();
    var id = " element" + gate;
    console.log(responseTextArray[gate]);
    // xhttp.open("POST", "/api/gates/color", true);
    // xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    // xhttp.send("color=solid&gateID=all&red="+red+"&green="+green+"&blue="+blue);
}

// Get the modal
var updateModal = document.getElementById('updateModal');
var powerModal = document.getElementById('powerModal');
var branchAlertModal = document.getElementById('branchAlertModal');

// Get the button that opens the modal
var updateBtn = document.getElementById("updateBtn");
var powerBtn = document.getElementById("powerBtn");
var rebootBtn = document.getElementById("rebootBtn");
var shutdownBtn = document.getElementById("shutdownBtn");

// Get the <span> element that closes the modal
var updateSpan = document.getElementById("updateSpan");
var powerSpan = document.getElementById("powerSpan");
var branchAlertSpan = document.getElementById("branchAlertSpan");

var updatenoBtn = document.getElementsByClassName("no")[0];
var updateyesBtn = document.getElementsByClassName("yes")[0];

// When the user clicks the button, open the modal
updateBtn.onclick = function() {
    updateModal.style.display = "block";
}
powerBtn.onclick = function() {
    powerModal.style.display = "block";
}

// When the user clicks on <span> (x), close the modal
updateSpan.onclick = function() {
    updateModal.style.display = "none";
}
powerSpan.onclick = function() {
    powerModal.style.display = "none";
}
branchAlertSpan.onclick = function() {
    branchAlertModal.style.display = "none";
}

updatenoBtn.onclick = function() {
    updateModal.style.display = "none";
}
updateyesBtn.onclick = function() {
    sendElementCommand('update');
    updateModal.style.display = "none";
}
rebootBtn.onclick = function() {
    sendElementCommand('reboot');
    powerModal.style.display = "none";
}
shutdownBtn.onclick = function() {
    sendElementCommand('shutdown');
    powerModal.style.display = "none";
}

// When the user clicks anywhere outside of the modal, close it
window.onclick = function(event) {
    if (event.target == updateModal) {
        updateModal.style.display = "none";
    }
    else if (event.target == powerModal) {
        powerModal.style.display = "none";
    }
}

// Color picker

function setRgb () {
  var red = document.querySelector('.color-picker .red-slider').value;
  var green = document.querySelector('.color-picker .green-slider').value;
  var blue = document.querySelector('.color-picker .blue-slider').value;
  var color = "rgb(" + red + "," + green + "," + blue + ")";
  document.querySelector('.color-preview').style.background = color;
}
  setRgb();
