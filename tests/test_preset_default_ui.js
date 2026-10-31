const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const elements = new Map();
function element(id) {
  if (!elements.has(id)) elements.set(id, {id, value:'', checked:false, style:{}, textContent:'', addEventListener(){}, focus(){}, querySelectorAll(){return []}, replaceChildren(){}, add(){}, append(){}});
  return elements.get(id);
}
let catalog = {presets:[{id:'a',name:'A'}, {id:'b',name:'B'}], schedules:[], default:'a'};
const context = {document:{getElementById:element, querySelector:element, documentElement:{style:{setProperty(){}}}},
  Option: function(name, value) { this.name=name; this.value=value; }, URLSearchParams,
  fetch:async (path, options) => {
    if (options && options.method === 'POST') { if (options.body.get('action') === 'default') catalog.default = options.body.get('id'); return {ok:true}; }
    return {ok:true, json:async()=>catalog};
  }, console};
vm.createContext(context);
vm.runInContext(fs.readFileSync('code/static/js/script.js','utf8'), context);
(async () => {
  await context.loadPresets();
  assert.equal(element('defaultPreset').value, 'a');
  element('defaultPreset').value = 'b';
  vm.runInContext("editedFields.add('defaultPreset')", context);
  await context.loadPresets();
  assert.equal(element('defaultPreset').value, 'b', 'unrelated reload preserves pending selection');
  await context.presetAction({action:'default', id:'b'});
  assert.equal(vm.runInContext("editedFields.has('defaultPreset')", context), false);
  catalog.default = 'a';
  await context.loadPresets();
  assert.equal(element('defaultPreset').value, 'a', 'successful save releases selection for future refresh');
  console.log('pending default survives reload and successful save releases it');
})().catch(error => {console.error(error); process.exitCode=1});
