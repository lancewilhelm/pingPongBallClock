"""Validated preset definitions and local-time schedule decisions."""
import copy
import re
import uuid
from datetime import datetime

import storage

DISPLAY_KEYS = ('animationSpeed', 'textColor', 'fontName', 'textSpacing', 'customText',
                'weatherZipLocation', 'weatherCityLocation', 'tempUnits', 'content',
                'bgColor', 'brightness', 'timeFormat', 'lineCount')
EMPTY = {'presets': [], 'schedules': [], 'default': None}


def validate(value):
    storage.object_value(value)
    if set(value) != set(EMPTY) or not isinstance(value['presets'], list) or not isinstance(value['schedules'], list):
        raise ValueError('Invalid preset definitions')
    if len(value['presets']) > 100 or len(value['schedules']) > 100:
        raise ValueError('Too many presets or schedules')
    ids = set()
    for item in value['presets']:
        if not isinstance(item, dict) or set(item) != {'id', 'name', 'display'}:
            raise ValueError('Invalid preset')
        if not isinstance(item['id'], str) or not re.fullmatch(r'[0-9a-f]{32}', item['id']) or item['id'] in ids:
            raise ValueError('Invalid preset ID')
        if not isinstance(item['name'], str) or not item['name'].strip() or len(item['name']) > 80:
            raise ValueError('Invalid preset name')
        if not isinstance(item['display'], dict) or set(item['display']) != set(DISPLAY_KEYS):
            raise ValueError('Invalid display snapshot')
        storage.device_settings({**item['display'], 'boardType': 'xl'})
        ids.add(item['id'])
    if value['default'] is not None and value['default'] not in ids:
        raise ValueError('Invalid default preset')
    schedule_ids = set()
    for item in value['schedules']:
        if not isinstance(item, dict) or set(item) != {'id', 'preset', 'time', 'days', 'enabled'}:
            raise ValueError('Invalid schedule')
        if not isinstance(item['id'], str) or not re.fullmatch(r'[0-9a-f]{32}', item['id']) or item['id'] in schedule_ids:
            raise ValueError('Invalid schedule ID')
        if item['preset'] not in ids or not isinstance(item['time'], str) or not re.fullmatch(r'(?:[01][0-9]|2[0-3]):[0-5][0-9]', item['time']):
            raise ValueError('Invalid schedule preset or time')
        if not isinstance(item['days'], list) or not item['days'] or any(type(day) is not int or day not in range(7) for day in item['days']) or len(set(item['days'])) != len(item['days']) or type(item['enabled']) is not bool:
            raise ValueError('Invalid schedule days or enabled status')
        schedule_ids.add(item['id'])


def load():
    path = storage.STATE_DIR / 'presets.json'
    if not path.exists():
        backup = path.with_suffix(path.suffix + '.bak')
        if backup.exists():
            value = storage.read_json(backup)
            validate(value)
            return value
        return copy.deepcopy(EMPTY)
    return storage.load_state('presets.json', 'presets.txt', validate)


def save(value):
    storage.save_state('presets.json', value, validate)


def snapshot(settings):
    return {key: copy.deepcopy(settings[key]) for key in DISPLAY_KEYS}


def new_id():
    return uuid.uuid4().hex


def get_preset(definitions, preset_id):
    return next((p for p in definitions['presets'] if p['id'] == preset_id), None)


def due(definitions, now, executed):
    """Choose a deterministic winner for the observed local minute, once per date."""
    date = now.date().isoformat()
    candidates = [s for s in definitions['schedules'] if s['enabled'] and now.weekday() in s['days']
                  and s['time'] == now.strftime('%H:%M') and executed.get(s['id'], '') < date]
    return sorted(candidates, key=lambda s: s['id'])
