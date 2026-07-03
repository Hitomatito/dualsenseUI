import struct


HAT_NEUTRAL = 0x8
HAT_MAP = {
    0: (0, 1, 0, 0),
    1: (0, 1, 1, 0),
    2: (0, 0, 1, 0),
    3: (1, 0, 1, 0),
    4: (1, 0, 0, 0),
    5: (1, 0, 0, 1),
    6: (0, 0, 0, 1),
    7: (0, 1, 0, 1),
}


def parse_input_report(data):
    if not data or data[0] not in (0x01, 0x31):
        return None

    payload = data[1:]
    if data[0] == 0x31:
        payload = data[2:-4]

    if len(payload) < 53:
        return None

    state = {
        'x': payload[0],
        'y': payload[1],
        'rx': payload[2],
        'ry': payload[3],
        'z': payload[4],
        'rz': payload[5],
    }

    face = payload[7] >> 4
    b1 = payload[8]
    b2 = payload[9]

    buttons = {
        'square':    bool(face & 0x01),
        'cross':     bool(face & 0x02),
        'circle':    bool(face & 0x04),
        'triangle':  bool(face & 0x08),
        'l1':        bool(b1 & 0x01),
        'r1':        bool(b1 & 0x02),
        'l2':        bool(b1 & 0x04),
        'r2':        bool(b1 & 0x08),
        'select':    bool(b1 & 0x10),
        'start':     bool(b1 & 0x20),
        'l3':        bool(b1 & 0x40),
        'r3':        bool(b1 & 0x80),
        'ps':        bool(b2 & 0x01),
        'touchpad':  bool(b2 & 0x02),
        'mic':       bool(b2 & 0x04),
    }

    hat_val = payload[7] & 0x0F
    up = right = down = left = False
    if hat_val != HAT_NEUTRAL and hat_val in HAT_MAP:
        down_b, up_b, right_b, left_b = HAT_MAP[hat_val]
        up = bool(up_b)
        down = bool(down_b)
        left = bool(left_b)
        right = bool(right_b)
    buttons.update({
        'dpad_up': up,
        'dpad_down': down,
        'dpad_left': left,
        'dpad_right': right,
    })

    state['buttons'] = buttons

    state['gyro'] = struct.unpack_from('<3h', payload, 15)
    state['accel'] = struct.unpack_from('<3h', payload, 21)

    touch = []
    for i in range(2):
        off = 32 + i * 4
        if off + 3 < len(payload):
            contact = payload[off]
            x_lo = payload[off + 1]
            packed = payload[off + 2]
            y_hi = payload[off + 3]
            x_hi = packed & 0x0F
            y_lo = (packed >> 4) & 0x0F
            tx = x_lo | (x_hi << 8)
            ty = y_lo | (y_hi << 4)
            touch.append({'contact': contact, 'x': tx, 'y': ty})
    state['touch'] = touch

    if len(payload) > 52:
        status = payload[52]
        state['battery'] = min((status & 0x0F) * 10 + 5, 100)

    return state
