import struct
import pytest
from dualsense_ui.parser import parse_input_report


def _usb_packet(payload_53):
    return bytes([0x01]) + payload_53


def _bt_packet(payload_53):
    return bytes([0x31, 0x00]) + payload_53 + bytes(4)


def _payload(**overrides):
    p = bytearray(53)
    p[0] = overrides.get('x', 127)
    p[1] = overrides.get('y', 127)
    p[2] = overrides.get('rx', 127)
    p[3] = overrides.get('ry', 127)
    p[4] = overrides.get('z', 0)
    p[5] = overrides.get('rz', 0)
    p[6] = overrides.get('seqno', 0)
    p[7] = overrides.get('byte7', 0x08)
    p[8] = overrides.get('byte8', 0x00)
    p[9] = overrides.get('byte9', 0x00)
    return bytes(p)


class TestInvalidData:
    def test_none(self):
        assert parse_input_report(None) is None

    def test_empty(self):
        assert parse_input_report(b'') is None

    def test_wrong_report_id(self):
        assert parse_input_report(b'\x02' + b'\x00' * 53) is None

    def test_short_payload(self):
        assert parse_input_report(b'\x01' + b'\x00' * 20) is None


class TestSticks:
    def test_center(self):
        pkt = _usb_packet(_payload(x=127, y=127, rx=127, ry=127))
        state = parse_input_report(pkt)
        assert state['x'] == 127
        assert state['y'] == 127
        assert state['rx'] == 127
        assert state['ry'] == 127

    def test_limits(self):
        pkt = _usb_packet(_payload(x=0, y=255, rx=255, ry=0))
        state = parse_input_report(pkt)
        assert state['x'] == 0
        assert state['y'] == 255
        assert state['rx'] == 255
        assert state['ry'] == 0


class TestTriggers:
    def test_rest(self):
        pkt = _usb_packet(_payload(z=0, rz=0))
        state = parse_input_report(pkt)
        assert state['z'] == 0
        assert state['rz'] == 0

    def test_full(self):
        pkt = _usb_packet(_payload(z=255, rz=255))
        state = parse_input_report(pkt)
        assert state['z'] == 255
        assert state['rz'] == 255


class TestButtons:
    @pytest.mark.parametrize('btn,byte_idx,bit,mask', [
        ('square',   7, 4, 0x10),
        ('cross',    7, 5, 0x20),
        ('circle',   7, 6, 0x40),
        ('triangle', 7, 7, 0x80),
    ])
    def test_face_buttons(self, btn, byte_idx, bit, mask):
        pkt = _usb_packet(_payload(**{'byte7': mask}))
        state = parse_input_report(pkt)
        assert state['buttons'][btn] is True

    @pytest.mark.parametrize('btn,byte_idx,bit,mask', [
        ('l1',       8, 0, 0x01),
        ('r1',       8, 1, 0x02),
        ('l2',       8, 2, 0x04),
        ('r2',       8, 3, 0x08),
        ('select',   8, 4, 0x10),
        ('start',    8, 5, 0x20),
        ('l3',       8, 6, 0x40),
        ('r3',       8, 7, 0x80),
    ])
    def test_shoulder_buttons(self, btn, byte_idx, bit, mask):
        pkt = _usb_packet(_payload(**{'byte8': mask}))
        state = parse_input_report(pkt)
        assert state['buttons'][btn] is True

    @pytest.mark.parametrize('btn,mask', [
        ('ps',       0x01),
        ('touchpad', 0x02),
        ('mic',      0x04),
    ])
    def test_system_buttons(self, btn, mask):
        pkt = _usb_packet(_payload(**{'byte9': mask}))
        state = parse_input_report(pkt)
        assert state['buttons'][btn] is True

    def test_all_buttons_false(self):
        pkt = _usb_packet(_payload(byte7=0x08, byte8=0x00, byte9=0x00))
        state = parse_input_report(pkt)
        for btn_name, val in state['buttons'].items():
            assert val is False, f'{btn_name} should be False'


HAT_TEST_CASES = [
    (0x00, False, True,  False, False),  # N: down=0, up=1, right=0, left=0
    (0x01, False, True,  True,  False),  # NE
    (0x02, False, False, True,  False),  # E
    (0x03, True,  False, True,  False),  # SE
    (0x04, True,  False, False, False),  # S
    (0x05, True,  False, False, True),   # SW
    (0x06, False, False, False, True),   # W
    (0x07, False, True,  False, True),   # NW
    (0x08, False, False, False, False),  # neutral
    (0x0F, False, False, False, False),  # invalid
]


class TestHat:
    @pytest.mark.parametrize('hat_val,down,up,right,left', HAT_TEST_CASES)
    def test_directions(self, hat_val, down, up, right, left):
        pkt = _usb_packet(_payload(byte7=hat_val & 0x0F))
        state = parse_input_report(pkt)
        assert state['buttons']['dpad_up'] == up
        assert state['buttons']['dpad_down'] == down
        assert state['buttons']['dpad_left'] == left
        assert state['buttons']['dpad_right'] == right


class TestIMU:
    def test_gyro(self):
        payload = bytearray(_payload())
        struct.pack_into('<3h', payload, 15, 100, -200, 300)
        pkt = _usb_packet(bytes(payload))
        state = parse_input_report(pkt)
        assert state['gyro'] == (100, -200, 300)

    def test_accel(self):
        payload = bytearray(_payload())
        struct.pack_into('<3h', payload, 21, -1000, 0, 5000)
        pkt = _usb_packet(bytes(payload))
        state = parse_input_report(pkt)
        assert state['accel'] == (-1000, 0, 5000)


class TestTouchpad:
    def _build_touch_payload(self, contacts):
        p = bytearray(53)
        for i, (contact, x, y) in enumerate(contacts):
            off = 32 + i * 4
            p[off] = contact
            x_lo = x & 0xFF
            x_hi = (x >> 8) & 0x0F
            y_lo = y & 0x0F
            y_hi = (y >> 4) & 0xFF
            p[off + 1] = x_lo
            p[off + 2] = (y_lo << 4) | x_hi
            p[off + 3] = y_hi
        return bytes(p)

    def test_both_inactive(self):
        pkt = _usb_packet(self._build_touch_payload([
            (0x80, 0, 0),
            (0x80, 0, 0),
        ]))
        state = parse_input_report(pkt)
        for pt in state['touch']:
            assert (pt['contact'] & 0x80) != 0

    def test_point_0_active(self):
        pkt = _usb_packet(self._build_touch_payload([
            (0x00, 100, 200),
            (0x80, 0, 0),
        ]))
        state = parse_input_report(pkt)
        assert (state['touch'][0]['contact'] & 0x80) == 0
        assert state['touch'][0]['x'] == 100
        assert state['touch'][0]['y'] == 200
        assert (state['touch'][1]['contact'] & 0x80) != 0

    def test_both_active(self):
        pkt = _usb_packet(self._build_touch_payload([
            (0x00, 1920, 1080),
            (0x00, 0, 0),
        ]))
        state = parse_input_report(pkt)
        assert state['touch'][0]['x'] == 1920
        assert state['touch'][0]['y'] == 1080
        assert state['touch'][1]['x'] == 0
        assert state['touch'][1]['y'] == 0

    def test_max_coordinates(self):
        pkt = _usb_packet(self._build_touch_payload([
            (0x00, 1920, 1080),
            (0x00, 1920, 1080),
        ]))
        state = parse_input_report(pkt)
        for pt in state['touch']:
            assert pt['x'] == 1920
            assert pt['y'] == 1080


class TestBattery:
    @pytest.mark.parametrize('level,expected', [
        (0, 5),
        (5, 55),
        (9, 95),
        (10, 100),
    ])
    def test_mapping(self, level, expected):
        p = bytearray(53)
        p[52] = level
        pkt = _usb_packet(bytes(p))
        state = parse_input_report(pkt)
        assert state['battery'] == expected

    def test_capped_at_100(self):
        p = bytearray(53)
        p[52] = 0x0F
        pkt = _usb_packet(bytes(p))
        state = parse_input_report(pkt)
        assert state['battery'] == 100


class TestBTFormat:
    def test_bt_packet(self):
        payload = _payload(x=50, y=200, z=128, byte7=0x38)
        pkt = _bt_packet(payload)
        state = parse_input_report(pkt)
        assert state['x'] == 50
        assert state['y'] == 200
        assert state['z'] == 128
        assert state['buttons']['cross'] is True


class TestRegression:
    def test_known_good_packet(self):
        p = bytearray(53)
        p[0:6] = [100, 150, 200, 50, 30, 60]
        face = 0x0A  # cross (bit1) + triangle (bit3)
        hat = 0x08   # neutral
        p[7] = (face << 4) | hat  # = 0xA8
        p[8] = 0x12                # r1 (bit1) + select (bit4)
        p[9] = 0x03                # ps (bit0) + touchpad (bit1)
        struct.pack_into('<3h', p, 15, 250, -150, 0)
        struct.pack_into('<3h', p, 21, 4000, -2000, 1000)
        p[32] = 0x00                # contact 0 active
        p[33] = 0x40                # x_lo = 64
        p[34] = 0xE0                # packed: y_lo=14 <<4 | x_hi=0
        p[35] = 0x01                # y_hi = 1 → y = 14 | 1<<4 = 30
        p[52] = 0x07                # battery level = 7 → 75%
        pkt = _usb_packet(bytes(p))

        state = parse_input_report(pkt)
        assert state['x'] == 100
        assert state['y'] == 150
        assert state['rx'] == 200
        assert state['ry'] == 50
        assert state['z'] == 30
        assert state['rz'] == 60
        assert state['buttons']['cross'] is True
        assert state['buttons']['triangle'] is True
        assert state['buttons']['square'] is False
        assert state['buttons']['circle'] is False
        assert state['buttons']['r1'] is True
        assert state['buttons']['select'] is True
        assert state['buttons']['ps'] is True
        assert state['buttons']['touchpad'] is True
        assert state['buttons']['l1'] is False
        assert state['buttons']['l3'] is False
        assert state['buttons']['r3'] is False
        assert state['gyro'] == (250, -150, 0)
        assert state['accel'] == (4000, -2000, 1000)
        assert state['touch'][0]['x'] == 64
        assert state['touch'][0]['y'] == 30
        assert state['battery'] == 75
