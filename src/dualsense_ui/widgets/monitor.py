import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib, Gdk
import struct
import math
import cairo


STICK_RADIUS = 55
DOT_RADIUS = 5
TOUCH_W = 400
TOUCH_H = 150

HAT_NEUTRAL = 0x8
HAT_MAP = {
    0: (0, 1, 0, 0),  # N
    1: (0, 1, 1, 0),  # NE
    2: (0, 0, 1, 0),  # E
    3: (1, 0, 1, 0),  # SE
    4: (1, 0, 0, 0),  # S
    5: (1, 0, 0, 1),  # SW
    6: (0, 0, 0, 1),  # W
    7: (0, 1, 0, 1),  # NW
}

BTN_LABELS = {
    'dpad_up': 'Up', 'dpad_down': 'Down', 'dpad_left': 'Left', 'dpad_right': 'Right',
    'square': 'Square', 'cross': 'Cross', 'circle': 'Circle', 'triangle': 'Triangle',
    'l1': 'L1', 'r1': 'R1', 'l2': 'L2', 'r2': 'R2',
    'select': 'Select', 'start': 'Start', 'l3': 'L3', 'r3': 'R3',
    'ps': 'PS', 'touchpad': 'Touchpad', 'mic': 'Mic',
}

BTN_LAYOUT = [
    # Row 0: Triggers
    ('l2',       0, 0),
    ('r2',       5, 0),

    # Row 1: Bumpers
    ('l1',       0, 1),
    ('r1',       5, 1),

    # Row 2: D-Pad Up | Triangle
    ('dpad_up',    1, 2),
    ('triangle', 4, 2),

    # Row 3: D-Pad Left/Right | Square/Circle
    ('dpad_left',  0, 3),
    ('dpad_right', 2, 3),
    ('square',   3, 3),
    ('circle',   5, 3),

    # Row 4: D-Pad Down | Cross
    ('dpad_down',  1, 4),
    ('cross',    4, 4),

    # Row 5: L3 | R3
    ('l3',       1, 5),
    ('r3',       4, 5),

    # Row 6: Select | Start
    ('select',   1, 6),
    ('start',    4, 6),

    # Row 7: PS | Mic
    ('ps',       1, 7),
    ('mic',      4, 7),

    # Row 8: Touchpad
    ('touchpad', 1, 8),
]


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


class InputMonitorWidget(Gtk.Box):
    def __init__(self, backend, get_device, parent_window, get_connection_type):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.backend = backend
        self.get_device = get_device
        self.parent_window = parent_window
        self.get_connection_type = get_connection_type
        self._hid_device = None
        self._reading = False
        self._grabbed_devices = []
        self._state = {
            'x': 127, 'y': 127, 'rx': 127, 'ry': 127, 'z': 0, 'rz': 0,
            'hat': 8,
            'buttons': {},
            'gyro': (0, 0, 0),
            'accel': (0, 0, 0),
            'touch': [{'contact': 0, 'x': 0, 'y': 0}, {'contact': 0, 'x': 0, 'y': 0}],
            'battery': 0,
        }
        self._build_ui()

    def _build_ui(self):
        self.set_margin_top(8)
        self.set_margin_start(8)
        self.set_margin_end(8)
        self.set_margin_bottom(8)

        top_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        top_bar.set_halign(Gtk.Align.CENTER)
        self.status_icon = Gtk.Label(label='⏹')
        top_bar.append(self.status_icon)
        self.status_label = Gtk.Label(label='Monitor stopped')
        top_bar.append(self.status_label)
        self.toggle_button = Gtk.Button(label='▶ Start Monitor')
        self.toggle_button.connect('clicked', self._on_toggle)
        top_bar.append(self.toggle_button)
        self.append(top_bar)

        columns = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        columns.set_hexpand(True)
        columns.set_vexpand(True)

        left_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.left_stick_area = Gtk.DrawingArea()
        self.left_stick_area.set_content_width(STICK_RADIUS * 2 + 10)
        self.left_stick_area.set_content_height(STICK_RADIUS * 2 + 10)
        self.left_stick_area.set_draw_func(self._draw_stick, 'left')
        left_col.append(Gtk.Label(label='Left Stick'))
        left_col.append(self.left_stick_area)
        self.right_stick_area = Gtk.DrawingArea()
        self.right_stick_area.set_content_width(STICK_RADIUS * 2 + 10)
        self.right_stick_area.set_content_height(STICK_RADIUS * 2 + 10)
        self.right_stick_area.set_draw_func(self._draw_stick, 'right')
        left_col.append(Gtk.Label(label='Right Stick'))
        left_col.append(self.right_stick_area)
        columns.append(left_col)

        mid_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        mid_col.set_hexpand(True)

        triggers_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        triggers_box.set_homogeneous(True)
        self.l2_label = Gtk.Label(label='L2: 0')
        self.l2_bar = Gtk.LevelBar(min_value=0, max_value=255)
        self.l2_bar.set_value(0)
        l2_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        l2_col.append(self.l2_label)
        l2_col.append(self.l2_bar)
        triggers_box.append(l2_col)
        self.r2_label = Gtk.Label(label='R2: 0')
        self.r2_bar = Gtk.LevelBar(min_value=0, max_value=255)
        self.r2_bar.set_value(0)
        r2_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        r2_col.append(self.r2_label)
        r2_col.append(self.r2_bar)
        triggers_box.append(r2_col)
        mid_col.append(triggers_box)

        grid = Gtk.Grid()
        grid.set_row_spacing(3)
        grid.set_column_spacing(4)
        grid.add_css_class('monitor-buttons')
        self._btn_widgets = {}
        for key, col, row in BTN_LAYOUT:
            b = Gtk.CheckButton(label=BTN_LABELS[key])
            b.set_sensitive(False)
            grid.attach(b, col, row, 1, 1)
            self._btn_widgets[key] = b

        mid_col.append(grid)
        columns.append(mid_col)

        right_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.touch_area = Gtk.DrawingArea()
        self.touch_area.set_content_width(TOUCH_W)
        self.touch_area.set_content_height(TOUCH_H)
        self.touch_area.set_draw_func(self._draw_touch, None)
        right_col.append(Gtk.Label(label='Touchpad'))
        right_col.append(self.touch_area)
        self.gyro_label = Gtk.Label(label='Gyro: 0, 0, 0')
        self.accel_label = Gtk.Label(label='Accel: 0, 0, 0')
        right_col.append(self.gyro_label)
        right_col.append(self.accel_label)
        columns.append(right_col)

        self.append(columns)

    def _draw_stick(self, area, ctx, w, h, side):
        cx, cy = w / 2, h / 2
        r = STICK_RADIUS

        pat = cairo.RadialGradient(cx, cy, 0, cx, cy, r)
        pat.add_color_stop_rgb(0, 0.18, 0.18, 0.20)
        pat.add_color_stop_rgb(1, 0.12, 0.12, 0.14)
        ctx.set_source(pat)
        ctx.arc(cx, cy, r, 0, 2 * math.pi)
        ctx.fill()

        ctx.set_source_rgba(1, 1, 1, 0.06)
        ctx.arc(cx, cy, r, 0, 2 * math.pi)
        ctx.set_line_width(1)
        ctx.stroke()

        ctx.set_source_rgba(1, 1, 1, 0.10)
        ctx.move_to(cx - r + 4, cy)
        ctx.line_to(cx + r - 4, cy)
        ctx.move_to(cx, cy - r + 4)
        ctx.line_to(cx, cy + r - 4)
        ctx.stroke()

        ctx.set_source_rgba(1, 1, 1, 0.04)
        ctx.arc(cx, cy, 3, 0, 2 * math.pi)
        ctx.fill()

        s = self._state
        if side == 'left':
            nx = (s['x'] - 127) / 127.0
            ny = (s['y'] - 127) / 127.0
        else:
            nx = (s['rx'] - 127) / 127.0
            ny = (s['ry'] - 127) / 127.0

        max_d = r - DOT_RADIUS
        d = math.sqrt(nx * nx + ny * ny)
        if d > 1.0:
            nx /= d
            ny /= d
            d = 1.0

        dx = nx * max_d
        dy = ny * max_d

        intensity = max(0.4, min(1.0, d * 1.5 + 0.3))
        ctx.set_source_rgba(0.0, 0.6, 1.0, intensity)
        ctx.arc(cx + dx, cy + dy, DOT_RADIUS, 0, 2 * math.pi)
        ctx.fill()

        ctx.set_source_rgba(1, 1, 1, 0.3)
        ctx.arc(cx + dx, cy + dy, DOT_RADIUS - 1.5, 0, 2 * math.pi)
        ctx.fill()

    def _draw_touch(self, area, ctx, w, h, data):
        pat = cairo.RadialGradient(w/2, h/2, 0, w/2, h/2, max(w, h)/2)
        pat.add_color_stop_rgb(0, 0.13, 0.13, 0.15)
        pat.add_color_stop_rgb(1, 0.10, 0.10, 0.12)
        ctx.set_source(pat)
        ctx.rectangle(0, 0, w, h)
        ctx.fill()

        ctx.set_source_rgba(1, 1, 1, 0.04)
        ctx.set_line_width(1)
        for i in range(5):
            x = w * (i + 1) / 6
            ctx.move_to(x, 0)
            ctx.line_to(x, h)
        ctx.stroke()

        colors = [(0.0, 0.8, 0.0), (0.0, 0.5, 1.0)]
        for i, pt in enumerate(self._state['touch']):
            if (pt['contact'] & 0x80) == 0:
                tx = pt['x'] * w / 1920
                ty = pt['y'] * h / 1080
                ctx.set_source_rgb(*colors[i])
                ctx.arc(tx, ty, 8, 0, 2 * math.pi)
                ctx.fill()
                ctx.set_source_rgba(1, 1, 1, 0.25)
                ctx.arc(tx, ty, 4, 0, 2 * math.pi)
                ctx.fill()

    def _on_toggle(self, btn):
        if self._reading:
            self._stop_reading()
        else:
            self._start_reading()

    def _start_reading(self):
        dev = self.get_device()
        if not dev:
            self.parent_window.show_error('No device connected')
            return

        try:
            import hid
            d = hid.Device(0x054c, 0x0ce6)
            if d.serial != dev:
                d.close()
                d = hid.Device(0x054c, 0x0df2)
                if d.serial != dev:
                    d.close()
                    d = hid.Device(0x054c, 0x0ce6)

            d.nonblocking = True
            self._hid_device = d
            self._reading = True
            self.toggle_button.set_label('■ Stop Monitor')
            self.status_label.set_text('Monitor active')
            self.status_icon.set_text('▶')
            self._grab_touchpad(dev)
            GLib.timeout_add(16, self._poll_input)
        except Exception as e:
            self.parent_window.show_error(f'Failed to open HID device: {e}')

    def _stop_reading(self):
        self._reading = False
        self._ungrab_touchpad()
        if self._hid_device:
            try:
                self._hid_device.close()
            except Exception:
                pass
            self._hid_device = None
        self.toggle_button.set_label('▶ Start Monitor')
        self.status_label.set_text('Monitor stopped')
        self.status_icon.set_text('⏹')

    def _grab_touchpad(self, dev_serial):
        self._ungrab_touchpad()
        try:
            import evdev
            pids = {0x0ce6, 0x0df2}
            for path in evdev.list_devices():
                try:
                    inp = evdev.InputDevice(path)
                except Exception as e:
                    continue
                is_ds = inp.info.vendor == 0x054c and inp.info.product in pids
                if is_ds:
                    try:
                        inp.grab()
                        self._grabbed_devices.append(inp)
                        print(f'GRAB: grabado {path} ({inp.name})', flush=True)
                    except Exception as e:
                        print(f'GRAB: FALLO grab {path}: {e}', flush=True)
                        inp.close()
            print(f'GRAB: total dispositivos agarrados={len(self._grabbed_devices)}', flush=True)
        except Exception as e:
            print(f'GRAB: error general: {e}', flush=True)

    def _ungrab_touchpad(self):
        for inp in self._grabbed_devices:
            try:
                inp.ungrab()
            except Exception:
                pass
            try:
                inp.close()
            except Exception:
                pass
        self._grabbed_devices = []

    def _poll_input(self):
        if not self._reading or not self._hid_device:
            return False

        try:
            latest = None
            for _ in range(10):
                data = self._hid_device.read(64)
                if data:
                    latest = data
                else:
                    break
            if latest:
                self._parse_and_update(latest)
        except Exception:
            self._stop_reading()
            return False

        return self._reading

    def _parse_and_update(self, data):
        result = parse_input_report(data)
        if result is None:
            return
        self._state.update(result)
        self._update_ui()

    def _update_ui(self):
        s = self._state
        self.left_stick_area.queue_draw()
        self.right_stick_area.queue_draw()

        self.l2_bar.set_value(s['z'])
        self.l2_label.set_text(f'L2: {s["z"]}')
        self.r2_bar.set_value(s['rz'])
        self.r2_label.set_text(f'R2: {s["rz"]}')

        for key, widget in self._btn_widgets.items():
            widget.set_active(s['buttons'].get(key, False))

        self.gyro_label.set_text(f'Gyro: {s["gyro"][0]}, {s["gyro"][1]}, {s["gyro"][2]}')
        self.accel_label.set_text(f'Accel: {s["accel"][0]}, {s["accel"][1]}, {s["accel"][2]}')
        self.touch_area.queue_draw()
