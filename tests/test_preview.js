const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const tick = () => new Promise(resolve => setImmediate(resolve));
(async () => {
  const svg = {attributes: {}, setAttribute(k, v) {this.attributes[k] = String(v)}, replaceChildren(f) {this.children = f.children}};
  let announcements = 0;
  const status = {dataset: {}, get textContent() {return this.text}, set textContent(value) {this.text = value; announcements++}};
  let visibility;
  let nextTimer = 0;
  const timers = new Map();
  const requests = [];
  const handlers = {};
  const menu = {classList: {shown: false, remove() {this.shown = false}, toggle(name, open) {this.shown = open}}, addEventListener(name, fn) {handlers[`menu:${name}`] = fn}};
  const parent = {addEventListener(name, fn) {handlers[`parent:${name}`] = fn}, contains(target) {return target === button || target === menu}};
  const button = {nextElementSibling: menu, parentElement: parent, expanded: 'false', removeAttribute() {},
    setAttribute(name, value) {this.expanded = value}, getAttribute() {return this.expanded},
    addEventListener(name, fn) {handlers[`button:${name}`] = fn}, focus() {}};
  const document = {hidden: false, getElementById(id) {return id === 'clockPreview' ? svg : status},
    createDocumentFragment() {return {children: [], appendChild(c) {this.children.push(c)}}},
    createElementNS() {return {attributes: {}, setAttribute(k, v) {this.attributes[k] = String(v)}}},
    addEventListener(name, fn) {if (name === 'visibilitychange') visibility = fn; else handlers[`document:${name}`] = fn}, querySelectorAll() {return [button]}};
  const context = {document, AbortController, setTimeout(fn, delay) {const id = ++nextTimer; timers.set(id, {fn, delay}); return id},
    clearTimeout(id) {timers.delete(id)},
    fetch(path, {signal}) {return new Promise((resolve, reject) => {
      signal.addEventListener('abort', () => reject(new Error('aborted')));
      requests.push({resolve, reject});
    })}};
  const runTimer = delay => {
    const entry = [...timers.entries()].find(([, timer]) => timer.delay === delay);
    assert(entry, `expected ${delay}ms timer`);
    timers.delete(entry[0]); entry[1].fn();
  };
  vm.runInNewContext(fs.readFileSync('code/static/js/preview.js', 'utf8'), context);
  handlers['button:click']();
  assert.equal(menu.classList.shown, true);
  handlers['document:click']({target: {}});
  assert.equal(menu.classList.shown, false, 'outside click closes menu');
  handlers['button:click']();
  handlers['parent:focusout']({relatedTarget: {}});
  assert.equal(button.expanded, 'false', 'leaving the dropdown closes menu');
  const reply = frame => requests.shift().resolve({ok: true, json: async () => frame});
  const normal = {boardType: 'normal', brightness: 255, rows: [[0xff0000, null], [0x0000ff, 0]]};
  reply(normal);
  await tick();
  assert.equal(status.textContent, 'Live');
  assert.equal(svg.children.length, 3);
  assert.equal(svg.children[0].attributes.cx, '1');
  assert.equal(svg.children[1].attributes.cx, '0.5');
  assert.equal(Number(svg.children[1].attributes.cy), 0.5 + Math.sqrt(3) / 2);
  assert.equal(svg.children[0].attributes.fill, 'rgb(255,0,0)');
  runTimer(400);
  reply(normal);
  await tick();
  assert.equal(announcements, 1, 'unchanged status should not be announced again');
  runTimer(400);
  runTimer(5000);
  requests.shift();
  await tick();
  assert.match(status.textContent, /Disconnected/);
  assert.equal(svg.children.length, 3);
  runTimer(400);
  reply({boardType: 'xl', brightness: 128, rows: [[0xffffff], [null], [0xff0000]]});
  await tick();
  assert.equal(status.textContent, 'Live');
  assert.equal(svg.attributes.viewBox, `0 0 2 ${1 + Math.sqrt(3)}`);
  assert.equal(svg.children[0].attributes.cx, '1.5');
  assert.equal(svg.children[0].attributes.fill, 'rgb(128,128,128)');
  document.hidden = true; visibility();
  assert.equal(timers.size, 0);
  document.hidden = false; visibility();
  assert.equal(requests.length, 1);
  console.log('preview geometry, brightness, timeout, retry, recovery, and visibility passed');
})().catch(error => {console.error(error); process.exitCode = 1});
