const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const elements = new Map();
function element(id) {
  if (!elements.has(id)) elements.set(id, {value: '', checked: false, textContent: '', style: {}, addEventListener() {}, focus() {}, querySelectorAll() {return []}});
  return elements.get(id);
}
const pending = [];
const context = {
  document: {getElementById: element, querySelector: element, documentElement: {style: {setProperty() {}}}},
  URLSearchParams,
  fetch: (path, options) => new Promise(resolve => pending.push({path, options, resolve})),
  console
};
vm.createContext(context);
vm.runInContext(fs.readFileSync('code/static/js/script.js', 'utf8'), context);
const tick = () => new Promise(resolve => setImmediate(resolve));
(async () => {
  element('textInput').value = 'A&B=100% + café';
  context.setCustomText();
  context.setFont('digits');
  await tick();
  assert.equal(pending.length, 1);
  assert.equal(pending[0].path, '/api/setcustomtext');
  assert.equal(pending[0].options.body.get('text'), 'A&B=100% + café');
  assert.equal(pending[0].options.headers['X-Requested-With'], 'XMLHttpRequest');
  pending[0].resolve({ok: true});
  await tick();
  assert.equal(pending[1].path, '/api/webpagesettings');
  pending[1].resolve({ok: true});
  await tick();
  assert.equal(pending[2].path, '/api/settings');
  pending[2].resolve({ok: true});
  await tick();
  assert.equal(pending[3].path, '/api/font');
  pending[3].resolve({ok: false, status: 403});
  await tick();
  assert.match(element('requestStatus').textContent, /403/);
  assert.equal(pending.length, 4, 'failed mutation must not save');
  element('titleInput').value = '<img src=x onerror=alert(1)>';
  context.setPageTitle();
  assert.equal(element('pageTitle').textContent, '<img src=x onerror=alert(1)>');
  await tick();
  pending[4].resolve({ok: true});
  await tick();
  pending[5].resolve({ok: true});
  await tick();
  element('boardType').value = 'xl';
  context.sendBoardType();
  await tick();
  assert.equal(pending[6].path, '/api/boardtype');
  pending[6].resolve({ok: true});
  await tick();
  assert.equal(pending[7].path, '/api/webpagesettings');
  pending[7].resolve({ok: true});
  await tick();
  assert.equal(pending[8].path, '/api/settings');
  pending[8].resolve({ok: true});
  await tick();
  assert.match(element('requestStatus').textContent, /restart shortly/);
  console.log('frontend request ordering, encoding, errors, title, and restart guidance passed');
})().catch(error => { console.error(error); process.exitCode = 1; });
