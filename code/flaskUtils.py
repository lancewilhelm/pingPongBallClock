import json
import math
import secrets
import threading
from datetime import datetime
from urllib.parse import urlsplit

from flask import Flask, abort, g, jsonify, render_template, request
from LEDUtils import *
import storage

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16384
board_lock = threading.RLock()


def origin_tuple(value):
    try:
        parsed = urlsplit(value)
        if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username is not None or parsed.password is not None or parsed.path not in ('', '/') or parsed.query or parsed.fragment:
            return None
        return parsed.scheme, parsed.hostname.lower(), parsed.port or (443 if parsed.scheme == 'https' else 80)
    except ValueError:
        return None


@app.before_request
def protect_request():
    try:
        credentials = storage.read_json(storage.STATE_DIR / 'auth.json')
        username, password = credentials['username'], credentials['password']
        auth = request.authorization
        valid = (isinstance(username, str) and bool(username) and isinstance(password, str) and bool(password)
                 and auth is not None and auth.type.lower() == 'basic'
                 and secrets.compare_digest(username.encode('utf-8'), (auth.username or '').encode('utf-8'))
                 and secrets.compare_digest(password.encode('utf-8'), (auth.password or '').encode('utf-8')))
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        valid = False
    if not valid:
        return 'Authentication required', 401, {'WWW-Authenticate': 'Basic realm="Ping Pong Ball Clock"'}
    if request.method == 'POST':
        if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
            abort(403)
        origin = request.headers.get('Origin')
        if origin is not None and (origin_tuple(origin) is None or origin_tuple(origin) != origin_tuple(request.host_url)):
            abort(403)
        request.get_data(cache=True)
    board_lock.acquire()
    g.board_lock_acquired = True


@app.teardown_request
def release_board_lock(error):
    if g.pop('board_lock_acquired', False):
        board_lock.release()


def choice(name, values):
    value = request.form.get(name)
    if value not in values:
        abort(400)
    return value


def integer(name, minimum, maximum):
    try:
        value = int(request.form[name])
    except (KeyError, ValueError, TypeError):
        abort(400)
    if not minimum <= value <= maximum:
        abort(400)
    return value


def text_value(name, maximum=512):
    value = request.form.get(name)
    if value is None or len(value) > maximum:
        abort(400)
    return value


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/state')
def state():
    return jsonify(PPB.settingsSnapshot())


@app.route('/api/frame')
def frame():
    response = jsonify(PPB.frameSnapshot())
    response.headers['Cache-Control'] = 'no-store'
    return response


def set_color(attribute, animations):
    program = choice('color', ('solid', *animations))
    rgb = [integer(channel, 0, 255) for channel in ('red', 'green', 'blue')]
    setattr(PPB, attribute, ['solid', Color(*rgb)] if program == 'solid' else ['animation', program])
    setattr(PPB, 'bgDisplayChanged' if attribute == 'bgColor' else 'textDisplayChanged', True)
    return ''


@app.post('/api/bgcolor')
def setBGColor():
    return set_color('bgColor', ('rainbow', 'rainbowCycle', 'breathing', 'twinkle'))


@app.post('/api/textcolor')
def setTextColor():
    return set_color('textColor', ('rainbow', 'rainbowCycle', 'breathing'))


@app.post('/api/font')
def setFont():
    font = choice('font', ('slanted', 'digits'))
    PPB.font = {'slanted': slanted, 'digits': digits}[font]
    PPB.fontName = font
    PPB.fontChanged = True
    PPB.updateDisplayString()
    return ''


@app.post('/api/textanimation')
def setTextAnimation():
    animation = choice('animation', ('static', 'scrolling'))
    line = integer('lineNum', 0, 1)
    speed = 0.0
    if animation == 'scrolling':
        try:
            speed = float(request.form['speed'])
        except (KeyError, ValueError, TypeError):
            abort(400)
        if not math.isfinite(speed) or not 0 <= speed <= 100:
            abort(400)
    if animation == 'static':
        if PPB.boardType == 'normal':
            PPB.textOrigin[0] = [1, 1]
        elif PPB.lineCount == 1:
            PPB.textOrigin[0] = [2, 4]
        else:
            PPB.textOrigin[line] = [[4, 1], [1, 7]][line]
    PPB.animationSpeed[line] = speed
    PPB.textStateWipe()
    PPB.textOriginMoved = [True, True]
    PPB.updateDisplayString()
    return ''


@app.post('/api/setcontent')
def setContent():
    content = choice('content', ('time', 'date', 'text', 'weather'))
    line = integer('lineNum', 0, 1)
    checked = choice('checked', ('true', 'false'))
    item = f'{content} {line}'
    if checked == 'true' and item not in PPB.content:
        PPB.content.append(item)
    elif checked == 'false' and item in PPB.content:
        PPB.content.remove(item)
    return ''


@app.post('/api/setcustomtext')
def setCustomText():
    PPB.customText = text_value('text')
    return ''


@app.post('/api/weather')
def setWeather():
    unit = choice('unit', ('f', 'c', 'k'))
    zipcode, city = text_value('zip'), text_value('city')
    PPB.tempUnits, PPB.weatherZipLocation, PPB.weatherCityLocation = unit, zipcode, city
    PPB.updateWeather = True
    return ''


@app.post('/api/settings')
def updateSettings():
    action = choice('action', ('save', 'load'))
    if action == 'save':
        PPB.dumpSettings()
    else:
        PPB.loadSettings(False)
    return ''


@app.post('/api/brightness')
def setBrightness():
    brightness = integer('brightness', 0, 255)
    PPB.strip.setBrightness(brightness)
    PPB.brightness = brightness
    PPB.strip.show()
    return ''


@app.post('/api/timeformat')
def setTimeFormat():
    PPB.timeFormat = choice('timeFormat', ('12h', '24h'))
    return ''


@app.route('/api/webpagesettings', methods=['GET', 'POST'])
def updateWebPageSettings():
    if request.method == 'GET':
        return jsonify(storage.load_state('webpage.json', 'webpagesettings.txt', storage.page_settings))
    try:
        settings = json.loads(text_value('settings', 12000))
        storage.page_settings(settings)
        if len(settings['title']) > 200 or len(settings['mainBGColor']) > 100:
            abort(400)
    except (ValueError, TypeError):
        abort(400)
    storage.save_state('webpage.json', settings, storage.page_settings)
    return ''


@app.post('/api/boardtype')
def setBoardType():
    board_type = choice('boardType', ('normal', 'xl'))
    try:
        PPB.changeBoardType(board_type)
    except Exception:
        app.logger.exception('Board type change failed')
        return 'Board type change failed', 500
    return ''


@app.post('/api/xlsettings')
def setXLSettings():
    line_count = integer('lineCount', 1, 2)
    pending = PPB.pendingBoardConfig
    target_type = pending['boardType'] if pending is not None else PPB.boardType
    if target_type == 'normal' and line_count != 1:
        abort(400)
    if pending is not None:
        with PPB._settingsLock:
            PPB.pendingBoardConfig['lineCount'] = line_count
    if PPB.boardType == 'normal' and line_count == 2:
        return ''
    PPB.lineCount = line_count
    if PPB.boardType == 'xl':
        PPB.textOrigin[0] = [2, 4] if line_count == 1 else [4, 1]
        if line_count == 2:
            PPB.textOrigin[1] = [1, 7]
    PPB.textOriginMoved = [True, True]
    return ''


@app.route('/api/presets', methods=['GET', 'POST'])
def manage_presets():
    import presets
    try:
        definitions = presets.load()
        if request.method == 'GET':
            return jsonify(definitions)
        action = choice('action', ('save', 'apply', 'delete', 'default', 'schedule', 'delete_schedule'))
        if action == 'save':
            name = text_value('name', 80).strip()
            if not name:
                raise ValueError('Enter a preset name')
            definitions['presets'].append({'id': presets.new_id(), 'name': name,
                                           'display': presets.snapshot(PPB.settingsSnapshot())})
        elif action in ('apply', 'delete', 'default'):
            preset_id = text_value('id', 32)
            preset = presets.get_preset(definitions, preset_id)
            if action == 'default' and not preset_id:
                definitions['default'] = None
            elif preset is None:
                raise ValueError('Preset not found')
            elif action == 'apply':
                PPB.applyPreset(preset['display'])
                return jsonify(PPB.settingsSnapshot())
            elif action == 'default':
                definitions['default'] = preset_id
            else:
                if definitions['default'] == preset_id or any(s['preset'] == preset_id for s in definitions['schedules']):
                    raise ValueError('Remove the default and schedules using this preset first')
                definitions['presets'].remove(preset)
        elif action == 'schedule':
            schedule_id = request.form.get('id', '')
            existing = next((s for s in definitions['schedules'] if s['id'] == schedule_id), None)
            if schedule_id and existing is None:
                raise ValueError('Schedule not found')
            days = json.loads(text_value('days', 32))
            schedule = {'id': schedule_id or presets.new_id(), 'preset': text_value('preset', 32),
                        'time': text_value('time', 5), 'days': days,
                        'enabled': choice('enabled', ('true', 'false')) == 'true'}
            if existing is not None:
                definitions['schedules'].remove(existing)
            definitions['schedules'].append(schedule)
        else:
            schedule_id = text_value('id', 32)
            existing = next((s for s in definitions['schedules'] if s['id'] == schedule_id), None)
            if existing is None:
                raise ValueError('Schedule not found')
            definitions['schedules'].remove(existing)
        presets.save(definitions)
        if action == 'schedule':
            run_schedules(datetime.now())
        return jsonify(definitions)
    except (ValueError, TypeError, KeyError) as error:
        return str(error), 400
    except OSError:
        app.logger.exception('Preset storage failed')
        return 'Could not save or load presets', 500

scheduler_error = None


def initialize_presets():
    import presets
    global scheduler_error
    original = PPB.settingsSnapshot()
    try:
        metadata = original
        if metadata.get('presetApplyPending') or metadata.get('boardRestartPending'):
            for marker in ('presetApplyPending', 'boardRestartPending'):
                if metadata.get(marker):
                    PPB.clearPresetMarker(marker)
            return
        definitions = presets.load()
        preset = presets.get_preset(definitions, definitions['default'])
        if preset is not None:
            PPB.applyPreset(preset['display'])
    except Exception as error:
        scheduler_error = str(error)
        app.logger.exception('Startup preset failed')
        try:
            storage.save_state('settings.json', original, storage.device_settings)
            PPB.loadSettings(False)
        except Exception:
            app.logger.exception('Could not restore display settings after startup preset failure')


def run_schedules(now):
    import presets
    global scheduler_error
    try:
        definitions = presets.load()
        settings = PPB.settingsSnapshot()
        executions = settings.get('scheduleExecutions', {})
        candidates = presets.due(definitions, now, executions)
        if not candidates:
            return
        # All simultaneous events are consumed; the lowest stable ID wins.
        executions = {s['id']: executions[s['id']] for s in definitions['schedules'] if s['id'] in executions}
        for schedule in candidates:
            executions[schedule['id']] = now.date().isoformat()
        PPB.applyPreset(presets.get_preset(definitions, candidates[0]['preset'])['display'], executions)
        scheduler_error = None
    except Exception as error:
        scheduler_error = str(error)
        app.logger.exception('Scheduled preset failed')


@app.get('/api/scheduler-status')
def scheduler_status():
    return jsonify({'error': scheduler_error})
