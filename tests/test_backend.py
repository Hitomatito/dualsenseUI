import subprocess
from unittest.mock import patch
import pytest
from dualsense_ui.backend import (
    list_devices, get_battery, get_info,
    set_lightbar_power, set_lightbar_color, set_led_brightness,
    set_player_leds, set_mic, set_mic_led, set_mic_mode,
    set_mic_volume, set_speaker, set_volume, set_attenuation,
    set_trigger, power_off, update_firmware, _run,
    DualsenseError,
    TriggerSide, TriggerMode, SpeakerMode, MicMode, MicLedMode,
)


def _assert_cmd(mock, *expected):
    cmd = mock.call_args[0][0]
    assert cmd[-len(expected):] == list(expected), f'cmd={cmd}'


def test_list_devices_returns_list(mock_subprocess):
    mock_subprocess.return_value.stdout = (
        'AA:BB:CC:DD:EE:FF (USB)\n'
        '11:22:33:44:55:66 (Bluetooth)\n'
    )
    devices = list_devices()
    assert len(devices) == 2
    assert devices[0]['id'] == 'AA:BB:CC:DD:EE:FF'
    assert devices[0]['connection'] == 'USB'
    assert devices[1]['id'] == '11:22:33:44:55:66'
    assert devices[1]['connection'] == 'Bluetooth'
    _assert_cmd(mock_subprocess, '-l')


def test_list_devices_no_device(mock_subprocess):
    mock_subprocess.side_effect = DualsenseError('No device')
    assert list_devices() == []


def test_list_devices_empty_output(mock_subprocess):
    mock_subprocess.return_value.stdout = ''
    assert list_devices() == []


def test_list_devices_no_devices_message(mock_subprocess):
    mock_subprocess.return_value.stdout = 'No device connected'
    assert list_devices() == []


def test_get_battery(mock_subprocess):
    mock_subprocess.return_value.stdout = '75 charging'
    result = get_battery()
    assert result['level'] == 75
    assert result['status'] == 'charging'
    assert result['charging'] is True
    _assert_cmd(mock_subprocess, 'battery')


def test_get_battery_full(mock_subprocess):
    mock_subprocess.return_value.stdout = '100 full'
    result = get_battery()
    assert result['level'] == 100
    assert result['charging'] is True


def test_get_battery_discharging(mock_subprocess):
    mock_subprocess.return_value.stdout = '30 discharging'
    result = get_battery()
    assert result['level'] == 30
    assert result['status'] == 'discharging'
    assert result['charging'] is False


def test_get_battery_no_device(mock_subprocess):
    mock_subprocess.side_effect = DualsenseError('No device')
    result = get_battery()
    assert result['text'] == 'No device'
    assert result['level'] is None


def test_get_info(mock_subprocess):
    mock_subprocess.return_value.stdout = (
        'firmware version: 1.0.0\n'
        'serial: AA:BB:CC:DD:EE:FF\n'
        'connection: USB\n'
    )
    result = get_info()
    assert result['firmware_version'] == '1.0.0'
    assert result['serial'] == 'AA:BB:CC:DD:EE:FF'
    assert result['connection'] == 'USB'
    _assert_cmd(mock_subprocess, 'info')


def test_get_info_no_device(mock_subprocess):
    mock_subprocess.side_effect = DualsenseError('No device')
    result = get_info()
    assert 'No device connected' in result['raw']


@pytest.mark.parametrize('state,expected', [
    (True, ['lightbar', 'on']),
    (False, ['lightbar', 'off']),
])
def test_set_lightbar_power(mock_subprocess, state, expected):
    set_lightbar_power(state)
    _assert_cmd(mock_subprocess, *expected)


@pytest.mark.parametrize('red,green,blue,brightness,expected', [
    (255, 0, 0, None, ['lightbar', '255', '0', '0']),
    (0, 128, 255, 50, ['lightbar', '0', '128', '255', '50']),
])
def test_set_lightbar_color(mock_subprocess, red, green, blue, brightness, expected):
    set_lightbar_color(red, green, blue, brightness)
    _assert_cmd(mock_subprocess, *expected)


@pytest.mark.parametrize('level', [0, 1, 2])
def test_set_led_brightness(mock_subprocess, level):
    set_led_brightness(level)
    _assert_cmd(mock_subprocess, 'led-brightness', str(level))


@pytest.mark.parametrize('number,instant,expected', [
    (1, False, ['player-leds', '1']),
    (5, True, ['player-leds', '5', 'instant']),
])
def test_set_player_leds(mock_subprocess, number, instant, expected):
    set_player_leds(number, instant)
    _assert_cmd(mock_subprocess, *expected)


@pytest.mark.parametrize('state,expected', [
    (True, ['microphone', 'on']),
    (False, ['microphone', 'off']),
])
def test_set_mic(mock_subprocess, state, expected):
    set_mic(state)
    _assert_cmd(mock_subprocess, *expected)


@pytest.mark.parametrize('mode', [MicLedMode.ON, MicLedMode.OFF, MicLedMode.PULSE])
def test_set_mic_led(mock_subprocess, mode):
    set_mic_led(mode)
    _assert_cmd(mock_subprocess, 'microphone-led', mode.value)


@pytest.mark.parametrize('mode', [MicMode.CHAT, MicMode.ASR, MicMode.BOTH])
def test_set_mic_mode(mock_subprocess, mode):
    set_mic_mode(mode)
    _assert_cmd(mock_subprocess, 'microphone-mode', mode.value)


@pytest.mark.parametrize('volume', [0, 128, 255])
def test_set_mic_volume(mock_subprocess, volume):
    set_mic_volume(volume)
    _assert_cmd(mock_subprocess, 'microphone-volume', str(volume))


@pytest.mark.parametrize('mode,expected_arg', [
    (SpeakerMode.INTERNAL, 'internal'),
    (SpeakerMode.HEADPHONE, 'headphone'),
    (SpeakerMode.BOTH, 'both'),
])
def test_set_speaker(mock_subprocess, mode, expected_arg):
    set_speaker(mode)
    _assert_cmd(mock_subprocess, 'speaker', expected_arg)


@pytest.mark.parametrize('volume', [0, 128, 255])
def test_set_volume(mock_subprocess, volume):
    set_volume(volume)
    _assert_cmd(mock_subprocess, 'volume', str(volume))


@pytest.mark.parametrize('rumble,trigger_val', [(0, 0), (3, 7), (7, 3)])
def test_set_attenuation(mock_subprocess, rumble, trigger_val):
    set_attenuation(rumble, trigger_val)
    _assert_cmd(mock_subprocess, 'attenuation', str(rumble), str(trigger_val))


def test_set_trigger_off(mock_subprocess):
    set_trigger(TriggerSide.LEFT, TriggerMode.OFF.value)
    _assert_cmd(mock_subprocess, 'trigger', 'left', 'off')


def test_set_trigger_with_params(mock_subprocess):
    set_trigger(TriggerSide.LEFT, TriggerMode.FEEDBACK.value, [50, 100])
    _assert_cmd(mock_subprocess, 'trigger', 'left', 'feedback', '50', '100')


def test_set_trigger_both_sides(mock_subprocess):
    set_trigger(TriggerSide.BOTH, TriggerMode.OFF.value)
    _assert_cmd(mock_subprocess, 'trigger', 'both', 'off')


def test_update_firmware(mock_subprocess):
    update_firmware('/path/to/fw.bin')
    _assert_cmd(mock_subprocess, 'update', '/path/to/fw.bin')
    assert mock_subprocess.call_args[1]['timeout'] == 180


def test_power_off(mock_subprocess):
    power_off()
    _assert_cmd(mock_subprocess, 'power-off')


def test_power_off_no_device(mock_subprocess):
    mock_subprocess.side_effect = DualsenseError('No device')
    power_off()


def test_device_serial_passthrough(mock_subprocess, device_serial):
    get_battery(device=device_serial)
    cmd = mock_subprocess.call_args[0][0]
    assert '-d' in cmd
    assert device_serial in cmd
    _assert_cmd(mock_subprocess, 'battery')


class TestErrors:
    def test_missing_binary(self):
        with patch('dualsense_ui.backend.subprocess.run') as mock:
            mock.side_effect = FileNotFoundError()
            with pytest.raises(DualsenseError, match='no encontrado'):
                _run(['test'])

    def test_timeout(self):
        with patch('dualsense_ui.backend.subprocess.run') as mock:
            mock.side_effect = subprocess.TimeoutExpired('cmd', 5)
            with pytest.raises(DualsenseError, match='timed out'):
                _run(['test'])

    def test_nonzero_returncode(self):
        with patch('dualsense_ui.backend.subprocess.run') as mock:
            mock.return_value.returncode = 1
            mock.return_value.stderr = 'Some error'
            with pytest.raises(DualsenseError, match='Some error'):
                _run(['test'])
