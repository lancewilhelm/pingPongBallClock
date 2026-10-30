let requestQueue = Promise.resolve();

function showError(message) {
	document.getElementById('requestStatus').textContent = message;
}

async function post(path, values) {
	const response = await fetch(path, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
			'X-Requested-With': 'XMLHttpRequest'
		},
		body: new URLSearchParams(values)
	});
	if (!response.ok) throw new Error((response.text && await response.text()) || `${path} returned ${response.status}`);
}

function enqueue(requests) {
	requestQueue = requestQueue.then(async () => {
		showError('');
		for (const [path, values] of requests) await post(path, values);
		return true;
	}).catch(error => {
		showError(`Could not update settings: ${error.message}`);
		return false;
	});
	return requestQueue;
}

function pageSettings() {
	const get = id => document.getElementById(id);
	return {
		title: get('pageTitle').textContent,
		mainBGColor: document.querySelector('.page-color-preview').style.background,
		boardType: get('boardType').value,
		lineCount: get('lineCount').value,
		brightness: get('brightnessSlider').value,
		line1Speed: get('line1SpeedInput').value,
		line2Speed: get('line2SpeedInput').value,
		customText: get('textInput').value,
		...Object.fromEntries(['line1time', 'line1date', 'line1weather', 'line1text',
			'line2time', 'line2date', 'line2weather', 'line2text'].map(id => [id, get(id).checked]))
	};
}

function update(requests, savePage = false) {
	const fields = new Set();
	for (const [path, values] of requests) {
		const ids = {'/api/brightness':['brightnessSlider'], '/api/textanimation':[`line${Number(values.lineNum) + 1}SpeedInput`],
			'/api/setcontent':[`line${Number(values.lineNum) + 1}${values.content}`], '/api/setcustomtext':['textInput'],
			'/api/weather':['zipInput','cityInput','tempUnit'], '/api/timeformat':['timeFormat'],
			'/api/boardtype':['boardType'], '/api/xlsettings':['lineCount']}[path] || [];
		for (const id of ids) fields.add(id);
	}
	const submitted = [...fields].map(id => { const field = document.getElementById(id); return [id, field.type === 'checkbox' ? field.checked : field.value]; });
	if (savePage) requests.push(['/api/webpagesettings', {settings: JSON.stringify(pageSettings())}]);
	requests.push(['/api/settings', {action: 'save'}]);
	return enqueue(requests).then(ok => {
		if (ok) for (const [id, value] of submitted) { const field = document.getElementById(id); if ((field.type === 'checkbox' ? field.checked : field.value) === value) editedFields.delete(id); }
		return ok;
	});
}

async function loadWebSettings() {
	try {
		const response = await fetch('/api/webpagesettings');
		if (!response.ok) throw new Error(`/api/webpagesettings returned ${response.status}`);
		const data = await response.json();
		document.getElementById('pageTitle').textContent = data.title;
		document.title = data.title;
		document.documentElement.style.setProperty('--main-bg-color', data.mainBGColor);
		document.querySelector('.page-color-preview').style.background = data.mainBGColor;
		for (const [id, key] of Object.entries({boardType:'boardType', lineCount:'lineCount', brightnessSlider:'brightness', line1SpeedInput:'line1Speed', line2SpeedInput:'line2Speed', textInput:'customText'})) {
			document.getElementById(id).value = data[key];
		}
		for (const id of ['line1time', 'line1date', 'line1weather', 'line1text', 'line2time', 'line2date', 'line2weather', 'line2text']) {
			document.getElementById(id).checked = data[id];
		}
		await refreshState();
		openLineSettings();
		openXLSettings();
	} catch (error) {
		showError(`Could not load settings: ${error.message}`);
	}
}

function setPageTitle() {
	const title = document.getElementById('titleInput').value;
	document.getElementById('pageTitle').textContent = title;
	document.title = title;
	update([], true);
}
function setCustomPageColor() {
	document.documentElement.style.setProperty('--main-bg-color', document.querySelector('.page-color-preview').style.background);
	update([], true);
}
function colorRequest(path, color, red, green, blue) {
	return update([[path, {color, red, green, blue}]]);
}
function setCustomBGColor(color) {
	colorRequest('/api/bgcolor', color, ...['red','green','blue'].map(c => document.querySelector(`.bg-${c}-slider`).value));
}
function setCustomTextColor(color) {
	colorRequest('/api/textcolor', color, ...['red','green','blue'].map(c => document.querySelector(`.text-${c}-slider`).value));
}
function setBGGreen() { colorRequest('/api/bgcolor', 'solid', 0, 255, 0); }
function setBGRed() { colorRequest('/api/bgcolor', 'solid', 255, 0, 0); }
function setBGBlue() { colorRequest('/api/bgcolor', 'solid', 0, 0, 255); }
function setBGBlack() { colorRequest('/api/bgcolor', 'solid', 0, 0, 0); }
function setTextWhite() { colorRequest('/api/textcolor', 'solid', 255, 255, 255); }
function setTextBlack() { colorRequest('/api/textcolor', 'solid', 0, 0, 0); }
function setFont(font) { update([['/api/font', {font}]]); }
function setContent(id, content, lineNum) {
	update([['/api/setcontent', {content, lineNum, checked: document.getElementById(id).checked}]], true);
}
function configureTime() { update([['/api/timeformat', {timeFormat: document.getElementById('timeFormat').value}]]); }
function setWeather() {
	update([['/api/weather', {unit: document.getElementById('tempUnit').value, zip: document.getElementById('zipInput').value, city: document.getElementById('cityInput').value}]]);
}
function setCustomText() { update([['/api/setcustomtext', {text: document.getElementById('textInput').value}]], true); }
function setBrightness(brightness) {
	const slider = document.getElementById('brightnessSlider');
	if (brightness === undefined) brightness = slider.value;
	else slider.value = brightness;
	update([['/api/brightness', {brightness}]], true);
}
function setTextAnimation(animation, lineNum) {
	const input = document.getElementById(`line${Number(lineNum) + 1}SpeedInput`);
	const speed = input.value || 0;
	if (animation === 'static') input.value = 0;
	update([['/api/textanimation', {animation, speed, lineNum}]], true);
}
function openXLSettings() {
	document.getElementById('xl-settings').style.display = document.getElementById('boardType').value === 'xl' ? 'block' : 'none';
}
function openLineSettings() {
	document.getElementById('line2-settings').style.display = document.getElementById('lineCount').value === '2' ? 'block' : 'none';
}
function sendBoardType() {
	const boardType = document.getElementById('boardType').value;
	const requests = [];
	if (boardType === 'normal') {
		document.getElementById('lineCount').value = '1';
		openLineSettings();
		requests.push(['/api/xlsettings', {lineCount: '1'}]);
	}
	requests.push(['/api/boardtype', {boardType}]);
	update(requests, true).then(success => {
		if (success) showError('Board settings saved. The service will restart shortly. Refresh this page after it reconnects to see the new board configuration.');
	});
}
function sendXLSettings() {
	const lineCount = document.getElementById('lineCount').value;
	openLineSettings();
	update([['/api/xlsettings', {lineCount}]], true);
}
function setColorPreview(prefix) {
	const color = ['red', 'green', 'blue'].map(c => document.querySelector(`.${prefix}-${c}-slider`).value);
	document.querySelector(`.${prefix}-color-preview`).style.background = `rgb(${color.join(',')})`;
}
function setBGRgb() { setColorPreview('bg'); }
function setTextRgb() { setColorPreview('text'); }
function setPageRgb() { setColorPreview('page'); }
setBGRgb();
setTextRgb();
setPageRgb();

for (const [modalId, buttonIds, closeId] of [
	['timeModal', ['configureTimeBtn', 'configureTimeBtn2'], 'timeclose'],
	['weatherModal', ['configureWeatherBtn', 'configureWeatherBtn2'], 'weatherclose'],
	['customTextModal', ['configureTextBtn', 'configureTextBtn2'], 'textclose'],
	['webPageSettingsModal', ['settingsIcon'], 'settingsclose']
]) {
	const modal = document.getElementById(modalId);
	const close = document.getElementById(closeId);
	let opener;
	function hide() { modal.style.display = 'none'; if (opener) opener.focus(); }
	for (const id of buttonIds) document.getElementById(id).addEventListener('click', event => {
		opener = event.currentTarget;
		modal.style.display = 'block';
		close.focus();
	});
	close.addEventListener('click', hide);
	modal.addEventListener('click', event => { if (event.target === modal) hide(); });
	modal.addEventListener('keydown', event => {
		if (event.key === 'Escape') { event.preventDefault(); hide(); }
		if (event.key !== 'Tab') return;
		const controls = [...modal.querySelectorAll('button, input, select, [href], [tabindex]:not([tabindex="-1"])')].filter(control => !control.disabled && control.offsetParent !== null);
		if (!controls.length) return;
		if (event.shiftKey && document.activeElement === controls[0]) { event.preventDefault(); controls[controls.length - 1].focus(); }
		else if (!event.shiftKey && document.activeElement === controls[controls.length - 1]) { event.preventDefault(); controls[0].focus(); }
	});
}


const editedFields = new Set();
async function refreshState() {
    const response = await fetch('/api/state', {cache: 'no-store'});
    if (!response.ok) throw new Error('Could not read display state');
    const state = await response.json();
    for (const [id, value] of Object.entries({boardType: state.boardType, lineCount: state.lineCount,
        brightnessSlider: state.brightness, line1SpeedInput: state.animationSpeed[0], line2SpeedInput: state.animationSpeed[1],
        textInput: state.customText, zipInput: state.weatherZipLocation, cityInput: state.weatherCityLocation,
        tempUnit: state.tempUnits, timeFormat: state.timeFormat})) {
        const field = document.getElementById(id);
        if (!editedFields.has(id) && document.activeElement !== field) field.value = value;
    }
    for (let line = 0; line < 2; line++) for (const type of ['time', 'date', 'weather', 'text']) {
        const id = `line${line + 1}${type}`;
        if (!editedFields.has(id) && document.activeElement !== document.getElementById(id))
            document.getElementById(id).checked = state.content.includes(`${type} ${line}`);
    }
    openLineSettings(); openXLSettings();
}

async function loadPresets() {
    const response = await fetch('/api/presets', {cache: 'no-store'});
    if (!response.ok) throw new Error('Could not load presets');
    const data = await response.json();
    for (const id of ['presetSelect', 'schedulePreset', 'defaultPreset']) {
        const select = document.getElementById(id), previous = select.value;
        select.replaceChildren();
        if (id === 'defaultPreset') select.add(new Option('No default', ''));
        for (const preset of data.presets) select.add(new Option(preset.name, preset.id));
        if (id === 'defaultPreset') {
            const pending = editedFields.has(id) && (previous === '' || data.presets.some(p => p.id === previous));
            select.value = pending ? previous : (data.default || '');
            if (!pending) editedFields.delete(id);
        } else select.value = data.presets.some(p => p.id === previous) ? previous : (data.presets[0]?.id || '');
    }
    const list = document.getElementById('scheduleList');
    list.replaceChildren();
    if (!data.schedules.length) list.textContent = 'No schedules yet.';
    for (const schedule of data.schedules) {
        const row = document.createElement('div');
        const name = data.presets.find(p => p.id === schedule.preset)?.name || 'Unknown preset';
        const label = document.createElement('span');
        label.textContent = `${name} at ${schedule.time} (${schedule.days.map(d => ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][d]).join(', ')}) `;
        const toggle = document.createElement('button');
        toggle.type = 'button'; toggle.className = 'btn btn-purple'; toggle.textContent = schedule.enabled ? 'Disable' : 'Enable';
        toggle.onclick = () => presetAction({action:'schedule', id:schedule.id, preset:schedule.preset, time:schedule.time, days:JSON.stringify(schedule.days), enabled:String(!schedule.enabled)});
        const remove = document.createElement('button');
        remove.type = 'button'; remove.className = 'btn btn-purple'; remove.textContent = 'Delete schedule';
        remove.onclick = () => presetAction({action:'delete_schedule', id:schedule.id});
        row.append(label, toggle, remove); list.append(row);
    }
}
async function presetAction(values) {
    const ok = await enqueue([['/api/presets', values]]);
    if (!ok) return;
    if (values.action === 'default' && document.getElementById('defaultPreset').value === values.id) editedFields.delete('defaultPreset');
    try { await loadPresets(); if (values.action === 'apply') await refreshState(); showError('Preset settings updated.'); }
    catch (error) { showError(error.message); }
}
if (typeof window !== 'undefined') window.addEventListener('load', () => {
    for (const field of document.querySelectorAll('input, select')) field.addEventListener('input', () => editedFields.add(field.id));
    const value = id => document.getElementById(id).value;
    document.getElementById('savePreset').onclick = () => presetAction({action:'save', name:value('presetName')});
    document.getElementById('applyPreset').onclick = () => presetAction({action:'apply', id:value('presetSelect')});
    document.getElementById('deletePreset').onclick = () => presetAction({action:'delete', id:value('presetSelect')});
    document.getElementById('setDefaultPreset').onclick = () => presetAction({action:'default', id:value('defaultPreset')});
    document.getElementById('addSchedule').onclick = () => presetAction({action:'schedule', preset:value('schedulePreset'), time:value('scheduleTime'), days:JSON.stringify([...document.querySelectorAll('.schedule-day:checked')].map(d => Number(d.value))), enabled:'true'});
    loadPresets().catch(error => showError(error.message));
    setInterval(async () => {
        try {
            await refreshState();
            const response = await fetch('/api/scheduler-status', {cache:'no-store'});
            if (response.ok) { const status = await response.json(); if (status.error) showError(`Scheduled preset failed: ${status.error}`); }
        } catch (error) { showError(error.message); }
    }, 10000);
});
