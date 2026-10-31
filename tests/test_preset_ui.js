const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const elements = new Map();
function element(id) {
  if (!elements.has(id)) elements.set(id, {id, value:'', checked:false, style:{}, addEventListener(){}, focus(){}, querySelectorAll(){return []}});
  return elements.get(id);
}
const state = {boardType:'normal', lineCount:1, brightness:42, animationSpeed:[0,0], customText:'scheduled', weatherZipLocation:'', weatherCityLocation:'', tempUnits:'f', timeFormat:'12h', content:['time 0']};
const context = {document:{getElementById:element, querySelector:element, documentElement:{style:{setProperty(){}}}}, URLSearchParams,
  fetch:async path => path === '/api/state' ? {ok:true, json:async()=>state} : {ok:true}, console};
vm.createContext(context);
vm.runInContext(fs.readFileSync('code/static/js/script.js','utf8'), context);
(async () => {
  element('textInput').value = 'unsaved';
  vm.runInContext("editedFields.add('textInput')", context);
  await context.refreshState();
  assert.equal(element('textInput').value, 'unsaved');
  assert.equal(element('brightnessSlider').value, 42);
  await context.setCustomText();
  // setCustomText queues the submitted value but returns nothing, so wait for the queue.
  await vm.runInContext('requestQueue', context);
  await context.refreshState();
  assert.equal(element('textInput').value, 'scheduled');
  console.log('preset state refresh preserves unsaved input and refreshes submitted input');
})().catch(error => {console.error(error); process.exitCode=1});
