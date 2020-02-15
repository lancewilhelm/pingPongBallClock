function loadWebSettings(){
	var xhttp = new XMLHttpRequest();
	xhttp.onreadystatechange = function() {
		if (this.readyState == 4 && this.status == 200) {
			webPageSettings = JSON.parse(this.responseText)
			document.getElementById("pageTitle").innerHTML = webPageSettings.title;
			document.title = webPageSettings.title;
			document.documentElement.style.setProperty('--main-bg-color', webPageSettings.mainBGColor);
		}
	};

	xhttp.open("GET", "/api/webpagesettings", true);
	xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
	xhttp.send("");
}

function setPageTitle(){
	var title = document.getElementById('titleInput').value;
	document.getElementById("pageTitle").innerHTML = title;
	document.title = title;

	sendWebPageSettings();
}

function setCustomPageColor(){
	var color = document.querySelector('.page-color-preview').style.background
	document.documentElement.style.setProperty('--main-bg-color', color);
	console.log("set the color to " + color);

	sendWebPageSettings();
}

function sendWebPageSettings(){
	var xhttp = new XMLHttpRequest();

	var settings = {
		title: document.getElementById("pageTitle").innerHTML,
		mainBGColor: document.querySelector('.page-color-preview').style.background
	}

	settingsString = JSON.stringify(settings)
	console.log(settingsString)

	xhttp.open("POST", "/api/webpagesettings", true);
	xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
	xhttp.send("settings="+settingsString);
}

function setCustomBGColor(color){
	var xhttp = new XMLHttpRequest();
	var red = document.querySelector('.bg-color-picker .bg-red-slider').value;
	var green = document.querySelector('.bg-color-picker .bg-green-slider').value;
	var blue = document.querySelector('.bg-color-picker .bg-blue-slider').value;
	xhttp.open("POST", "/api/bgcolor", true);
	xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
	xhttp.send("color="+color+"&red="+red+"&green="+green+"&blue="+blue);
}

function setCustomTextColor(color){
	var xhttp = new XMLHttpRequest();
	var red = document.querySelector('.text-color-picker .text-red-slider').value;
	var green = document.querySelector('.text-color-picker .text-green-slider').value;
	var blue = document.querySelector('.text-color-picker .text-blue-slider').value;
	xhttp.open("POST", "/api/textcolor", true);
	xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
	xhttp.send("color="+color+"&red="+red+"&green="+green+"&blue="+blue);
}

function setBGGreen(){
	var xhttp = new XMLHttpRequest();
	var red = 0;
	var green = 255;
	var blue = 0;
	xhttp.open("POST", "/api/bgcolor", true);
	xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
	xhttp.send("color=solid&red="+red+"&green="+green+"&blue="+blue);
}

function setBGRed(){
	var xhttp = new XMLHttpRequest();
	var red = 255;
	var green = 0;
	var blue = 0;
	xhttp.open("POST", "/api/bgcolor", true);
	xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
	xhttp.send("color=solid&red="+red+"&green="+green+"&blue="+blue);
}

function setBGBlue(){
	var xhttp = new XMLHttpRequest();
	var red = 0;
	var green = 0;
	var blue = 255;
	xhttp.open("POST", "/api/bgcolor", true);
	xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
	xhttp.send("color=solid&red="+red+"&green="+green+"&blue="+blue);
}

function setBGBlack(){
	var xhttp = new XMLHttpRequest();
	var red = 0;
	var green = 0;
	var blue = 0;
	xhttp.open("POST", "/api/bgcolor", true);
	xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
	xhttp.send("color=solid&red="+red+"&green="+green+"&blue="+blue);
}

function setTextWhite(){
	var xhttp = new XMLHttpRequest();
	var red = 255;
	var green = 255;
	var blue = 255;
	xhttp.open("POST", "/api/textcolor", true);
	xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
	xhttp.send("color=solid&red="+red+"&green="+green+"&blue="+blue);
}

function setTextBlack(){
	var xhttp = new XMLHttpRequest();
	var red = 0;
	var green = 0;
	var blue = 0;
	xhttp.open("POST", "/api/textcolor", true);
	xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
	xhttp.send("color=solid&red="+red+"&green="+green+"&blue="+blue);
}

function setFont(font){
	var xhttp = new XMLHttpRequest();
	xhttp.open("POST", "/api/font", true);
	xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
	xhttp.send("font="+font);
}

function setContent(content, lineNum){
	var xhttp = new XMLHttpRequest();
	var checked = document.getElementById(content).checked;
	xhttp.open("POST", "/api/setcontent", true);
	xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
	xhttp.send("content="+content+"&lineNum="+lineNum+"&checked="+checked);
}

function configureTime(){
	var xhttp = new XMLHttpRequest();
	var timeFormat = document.getElementById("timeFormat").value;
	xhttp.open("POST", "/api/timeformat", true);
	xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
	xhttp.send("timeFormat="+timeFormat);
}

function setWeather(){
	var xhttp = new XMLHttpRequest();
	var unit = document.getElementById("tempUnit").value;
	var zip = document.getElementById("zipInput").value;
	var city = document.getElementById("cityInput").value;
	xhttp.open("POST", "/api/weather", true);
	xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
	xhttp.send("unit="+unit+"&zip="+zip+"&city="+city);
}

function setCustomText(){
	var xhttp = new XMLHttpRequest();
	var text = document.getElementById('textInput').value;
	xhttp.open("POST", "/api/setcustomtext", true);
	xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
	xhttp.send("text="+text);
}

function setBrightness(brightness){
	var xhttp = new XMLHttpRequest();
	if(brightness == undefined) {
		var brightness = document.getElementById('brightnessSlider').value;
	} else {
		document.getElementById('brightnessSlider').value = brightness;
	}
	xhttp.open("POST", "/api/brightness", true);
	xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
	xhttp.send("brightness="+brightness);
}

function settings(action){
	var xhttp = new XMLHttpRequest();
	xhttp.open("POST", "/api/settings", true);
	xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
	xhttp.send("action="+action);
}

function setTextAnimation(animation){
	var xhttp = new XMLHttpRequest();
	var speed = document.getElementById('speedInput').value;
	if (speed == ''){
		speed = 5;
	}
	if (animation == 'static'){
		document.getElementById('speedInput').value = 0;
	}
	console.log(speed);
	xhttp.open("POST", "/api/textanimation", true);
	xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
	xhttp.send("animation="+animation+"&speed="+speed);
}

function openXLSettings(){
	var boardType = document.getElementById('boardType').value
	if(boardType == 'xl'){
		document.getElementById('xl-settings').style.display = 'block';
	} else {
		document.getElementById('xl-settings').style.display = 'none';
	}
}

function openLineSettings(){
	var lineCount = document.getElementById('lineCount').value
	if(lineCount == 2){
		document.getElementById('line-settings').style.display = 'block';
	} else {
		document.getElementById('line-settings').style.display = 'none';
	}
}

function sendBoardType(){
	var boardType = document.getElementById('boardType').value
	var xhttp = new XMLHttpRequest();
	xhttp.open("POST", "/api/boardtype", true);
	xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
	xhttp.send("boardType="+boardType);
}

function sendXLSettings(){
	var lineCount = document.getElementById('lineCount').value
	var xhttp = new XMLHttpRequest();
	xhttp.open("POST", "/api/xlsettings", true);
	xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
	xhttp.send("lineCount="+lineCount);
}
// Color picker
function setBGRgb () {
	var red = document.querySelector('.bg-color-picker .bg-red-slider').value;
	var green = document.querySelector('.bg-color-picker .bg-green-slider').value;
	var blue = document.querySelector('.bg-color-picker .bg-blue-slider').value;
	var color = "rgb(" + red + "," + green + "," + blue + ")";
	document.querySelector('.bg-color-preview').style.background = color;
}
	setBGRgb();

// Color picker
function setTextRgb () {
	var red = document.querySelector('.text-color-picker .text-red-slider').value;
	var green = document.querySelector('.text-color-picker .text-green-slider').value;
	var blue = document.querySelector('.text-color-picker .text-blue-slider').value;
	var color = "rgb(" + red + "," + green + "," + blue + ")";
	document.querySelector('.text-color-preview').style.background = color;
}
	setTextRgb();

// Color picker
function setPageRgb () {
	var red = document.querySelector('.modal-body .page-color-picker .page-red-slider').value;
	var green = document.querySelector('.modal-body .page-color-picker .page-green-slider').value;
	var blue = document.querySelector('.modal-body .page-color-picker .page-blue-slider').value;
	var color = "rgb(" + red + "," + green + "," + blue + ")";
	document.querySelector('.modal-body .page-color-preview').style.background = color;
}
	setPageRgb();

// Time Modal
// Get the modal
var timemodal = document.getElementById("timeModal");

// Get the button that opens the modal
var timebtn = document.getElementById("configureTimeBtn");

// Get the <span> element that closes the modal
var timespan = document.getElementById("timeclose");

// When the user clicks on the button, open the modal
timebtn.onclick = function() {
	timemodal.style.display = "block";
}

// When the user clicks on <span> (x), close the modal
timespan.onclick = function() {
	timemodal.style.display = "none";
}

// Weather Modal
// Get the modal
var weathermodal = document.getElementById("weatherModal");

// Get the button that opens the modal
var weatherbtn = document.getElementById("configureWeatherBtn");

// Get the <span> element that closes the modal
var weatherspan = document.getElementById("weatherclose");

// When the user clicks on the button, open the modal
weatherbtn.onclick = function() {
	weathermodal.style.display = "block";
}

// When the user clicks on <span> (x), close the modal
weatherspan.onclick = function() {
	weathermodal.style.display = "none";
}

// Custom Text Modal
// Get the modal
var textmodal = document.getElementById("customTextModal");

// Get the button that opens the modal
var textbtn = document.getElementById("configureTextBtn");

// Get the <span> element that closes the modal
var textspan = document.getElementById("textclose");

// When the user clicks on the button, open the modal
textbtn.onclick = function() {
	textmodal.style.display = "block";
}

// When the user clicks on <span> (x), close the modal
textspan.onclick = function() {
	textmodal.style.display = "none";
}

// Web Page Settings Modal
// Get the modal
var pageSettingsModal = document.getElementById("webPageSettingsModal");

// Get the button that opens the modal
var pageSettingsBtn = document.getElementById("settingsIcon");

// Get the <span> element that closes the modal
var pageSettingsSpan = document.getElementById("settingsclose");

// When the user clicks on the button, open the modal
pageSettingsBtn.onclick = function() {
	pageSettingsModal.style.display = "block";
}

// When the user clicks on <span> (x), close the modal
pageSettingsSpan.onclick = function() {
	pageSettingsModal.style.display = "none";
}

// Odd-Sized Board Modal
// Get the modal
var oddBoardModal = document.getElementById("oddBoardModal");

// Get the button that opens the modal
var oddBoardBtn = document.getElementById("oddBoardBtn");

// Get the <span> element that closes the modal
var oddBoardSpan = document.getElementById("oddboardclose");

// When the user clicks on the button, open the modal
oddBoardBtn.onclick = function() {
	oddBoardModal.style.display = "block";
}

// When the user clicks on <span> (x), close the modal
oddBoardSpan.onclick = function() {
	oddBoardModal.style.display = "none";
}