import subprocess
import re
import shutil
from enum import Enum


class TriggerSide(Enum):
    LEFT = 'left'
    RIGHT = 'right'
    BOTH = 'both'


class TriggerMode(Enum):
    OFF = 'off'
    FEEDBACK = 'feedback'
    WEAPON = 'weapon'
    BOW = 'bow'
    GALLOPING = 'galloping'
    MACHINE = 'machine'
    VIBRATION = 'vibration'


class SpeakerMode(Enum):
    INTERNAL = 'internal'
    HEADPHONE = 'headphone'
    MONOHEADPHONE = 'monoheadphone'
    BOTH = 'both'


class MicMode(Enum):
    CHAT = 'chat'
    ASR = 'asr'
    BOTH = 'both'


class MicLedMode(Enum):
    ON = 'on'
    OFF = 'off'
    PULSE = 'pulse'


BINARY = 'dualsensectl'


class DualsenseError(Exception):
    pass


def _run(args, device=None, timeout=5) -> str:
    cmd = [BINARY]
    if device:
        cmd.extend(['-d', device])
    cmd.extend(args)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError:
        raise DualsenseError(f'{BINARY} no encontrado. Instálalo primero.')
    except subprocess.TimeoutExpired:
        raise DualsenseError('Comando timed out')

    if result.returncode != 0:
        err = result.stderr.strip() or result.stdout.strip()
        if err:
            raise DualsenseError(err)

    return result.stdout.strip()


def list_devices():
    try:
        out = _run(['-l'])
    except DualsenseError:
        return []
    if not out or 'No device' in out or 'No devices' in out:
        return []
    devices = []
    for line in out.split('\n'):
        line = line.strip()
        if not line or line.startswith('Devices'):
            continue
        m = re.match(r'(\S+)\s+\(([^)]+)\)', line)
        if m:
            serial = m.group(1)
            connection = m.group(2)
            devices.append({'id': serial, 'name': f'DualSense ({connection})', 'connection': connection})
    return devices


def get_battery(device=None) -> dict:
    try:
        out = _run(['battery'], device)
    except DualsenseError:
        return {'text': 'No device', 'level': None, 'charging': None}
    result = {'text': out, 'level': None, 'charging': None, 'status': 'unknown'}
    m = re.match(r'(\d+)\s+(\S+)', out)
    if m:
        result['level'] = int(m.group(1))
        result['status'] = m.group(2)
        result['charging'] = result['status'] in ('charging', 'full')
    return result


def get_info(device=None) -> dict:
    try:
        out = _run(['info'], device)
    except DualsenseError:
        return {'raw': 'No device connected'}
    info = {'raw': out}
    for line in out.split('\n'):
        line = line.strip()
        if ':' in line:
            key, _, val = line.partition(':')
            info[key.strip().lower().replace(' ', '_')] = val.strip()
    return info


def set_lightbar_power(state: bool, device=None):
    _run(['lightbar', 'on' if state else 'off'], device)


def set_lightbar_color(red: int, green: int, blue: int, brightness: int = None, device=None):
    args = ['lightbar', str(red), str(green), str(blue)]
    if brightness is not None:
        args.append(str(brightness))
    _run(args, device)


def set_led_brightness(level: int, device=None):
    _run(['led-brightness', str(level)], device)


def set_player_leds(number: int, instant: bool = False, device=None):
    args = ['player-leds', str(number)]
    if instant:
        args.append('instant')
    _run(args, device)


def set_mic(state: bool, device=None):
    _run(['microphone', 'on' if state else 'off'], device)


def set_mic_led(mode: MicLedMode, device=None):
    _run(['microphone-led', mode.value], device)


def set_mic_mode(mode: MicMode, device=None):
    _run(['microphone-mode', mode.value], device)


def set_mic_volume(volume: int, device=None):
    _run(['microphone-volume', str(volume)], device)


def set_speaker(mode: SpeakerMode, device=None):
    _run(['speaker', mode.value], device)


def set_volume(volume: int, device=None):
    _run(['volume', str(volume)], device)


def set_attenuation(rumble: int, trigger: int, device=None):
    _run(['attenuation', str(rumble), str(trigger)], device)


def set_trigger(trigger_side: TriggerSide, mode: str, params: list = None, device=None):
    args = ['trigger', trigger_side.value, mode]
    if params:
        args.extend(str(p) for p in params)
    _run(args, device)


def power_off(device=None):
    try:
        _run(['power-off'], device)
    except DualsenseError:
        pass


def update_firmware(file_path: str, device=None):
    _run(['update', file_path], device, timeout=180)


class DualsenseBackend:
    @staticmethod
    def list_devices():
        return list_devices()

    @staticmethod
    def get_battery(device=None):
        return get_battery(device)

    @staticmethod
    def get_info(device=None):
        return get_info(device)

    @staticmethod
    def set_lightbar_power(state: bool, device=None):
        set_lightbar_power(state, device)

    @staticmethod
    def set_lightbar_color(red: int, green: int, blue: int, brightness: int = None, device=None):
        set_lightbar_color(red, green, blue, brightness, device)

    @staticmethod
    def set_led_brightness(level: int, device=None):
        set_led_brightness(level, device)

    @staticmethod
    def set_player_leds(number: int, instant: bool = False, device=None):
        set_player_leds(number, instant, device)

    @staticmethod
    def set_mic(state: bool, device=None):
        set_mic(state, device)

    @staticmethod
    def set_mic_led(mode: MicLedMode, device=None):
        set_mic_led(mode, device)

    @staticmethod
    def set_mic_mode(mode: MicMode, device=None):
        set_mic_mode(mode, device)

    @staticmethod
    def set_mic_volume(volume: int, device=None):
        set_mic_volume(volume, device)

    @staticmethod
    def set_speaker(mode: SpeakerMode, device=None):
        set_speaker(mode, device)

    @staticmethod
    def set_volume(volume: int, device=None):
        set_volume(volume, device)

    @staticmethod
    def set_attenuation(rumble: int, trigger: int, device=None):
        set_attenuation(rumble, trigger, device)

    @staticmethod
    def set_trigger(trigger_side: TriggerSide, mode: str, params: list = None, device=None):
        set_trigger(trigger_side, mode, params, device)

    @staticmethod
    def update_firmware(file_path: str, device=None):
        update_firmware(file_path, device)

    @staticmethod
    def power_off(device=None):
        power_off(device)
