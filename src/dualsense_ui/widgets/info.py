import math
import cairo
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk


class LiquidBattery(Gtk.DrawingArea):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._value = 0.0
        self._target_value = 0.0
        self._charging = False
        self._phase = 0.0

        self.set_size_request(200, 36)
        self.set_hexpand(True)
        self.set_draw_func(self._draw)
        self.add_tick_callback(self._on_tick)

    def set_value(self, val):
        self._target_value = max(0.0, min(100.0, float(val)))

    def get_value(self):
        return self._value

    def set_charging(self, charging):
        self._charging = charging

    def get_charging(self):
        return self._charging

    def _on_tick(self, widget, frame_clock):
        dt = frame_clock.get_frame_time() / 1000.0
        self._phase += dt * 0.8
        if self._phase > math.pi * 2:
            self._phase -= math.pi * 2

        diff = self._target_value - self._value
        if abs(diff) > 0.3:
            self._value += diff * 0.08
        else:
            self._value = self._target_value

        self.queue_draw()
        return True

    def _draw(self, area, cr, w, h):
        r = h / 2.0
        level = self._value / 100.0
        lx = w * level

        self._draw_rounded_rect(cr, 0, 0, w, h, r)
        cr.set_source_rgba(0, 0, 0, 0.06)
        cr.fill()

        if level > 0.01:
            cr.save()
            self._draw_rounded_rect(cr, 0, 0, w, h, r)
            cr.clip()

            c = self._get_fill_color()
            pat = cairo.LinearGradient(0, 0, lx, 0)
            pat.add_color_stop_rgba(0, c[0] * 0.85, c[1] * 0.85, c[2] * 0.85, c[3])
            pat.add_color_stop_rgba(lx, c[0], c[1], c[2], c[3])
            cr.set_source(pat)
            cr.rectangle(0, 0, lx, h)
            cr.fill()

            amp = 2.0
            freq = 0.03
            steps = max(int(w), 40)
            cr.set_source_rgba(1, 1, 1, 0.07)
            cr.move_to(0, 0)
            for i in range(steps + 1):
                x = (i / steps) * w
                if x > lx:
                    break
                y = amp * math.sin(freq * x + self._phase)
                cr.line_to(x, y)
            cr.line_to(lx, 0)
            cr.close_path()
            cr.fill()

            if self._charging:
                cr.set_source_rgba(c[0], c[1], c[2], 0.06)
                cr.paint_with_alpha(0.06)

            cr.restore()

        self._draw_rounded_rect(cr, 0, 0, w, h, r)
        cr.set_line_width(1.5)
        cr.set_source_rgba(1, 1, 1, 0.08)
        cr.stroke()

    def _draw_rounded_rect(self, cr, x, y, w, h, r):
        r = min(r, w / 2, h / 2)
        cr.move_to(x + r, y)
        cr.line_to(x + w - r, y)
        cr.arc(x + w - r, y + r, r, -math.pi / 2, 0)
        cr.line_to(x + w, y + h - r)
        cr.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
        cr.line_to(x + r, y + h)
        cr.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
        cr.line_to(x, y + r)
        cr.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
        cr.close_path()

    def _get_fill_color(self):
        if self._value <= 20:
            return (0.98, 0.55, 0.12, 0.95)
        elif self._charging:
            return (0.25, 0.85, 0.55, 0.95)
        else:
            return (0.35, 0.80, 0.50, 0.95)


class InfoWidget(Gtk.Box):
    def __init__(self, backend, get_device, parent_window, get_connection_type):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.backend = backend
        self.get_device = get_device
        self.parent_window = parent_window
        self.get_connection_type = get_connection_type
        self._build_ui()
        self._refresh()

    def _build_ui(self):
        frame = Gtk.Frame(margin_top=12, margin_bottom=12, margin_start=12, margin_end=12)
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        vbox.set_margin_top(16)
        vbox.set_margin_bottom(16)
        vbox.set_margin_start(16)
        vbox.set_margin_end(16)

        lbl = Gtk.Label()
        lbl.set_markup('<big><b>Device Info</b></big>')
        vbox.append(lbl)

        self.connection_label = Gtk.Label(label='')
        self.connection_label.set_xalign(0)
        vbox.append(self.connection_label)

        self.battery_bar = LiquidBattery()
        vbox.append(self.battery_bar)

        self.battery_label = Gtk.Label(label='Battery: --')
        vbox.append(self.battery_label)

        self.info_text = Gtk.Label(label='')
        self.info_text.set_selectable(True)
        self.info_text.set_wrap(True)
        self.info_text.set_xalign(0)
        self.info_text.add_css_class('info-text')
        vbox.append(self.info_text)

        frame.set_child(vbox)
        self.append(frame)

    def _refresh(self):
        dev = self.get_device()
        conn = self.get_connection_type()

        if not dev:
            self.connection_label.set_text('No device connected')
            self.battery_label.set_text('')
            self.info_text.set_text('Connect a DualSense controller')
            self.battery_bar.set_value(0)
            return

        if conn:
            self.connection_label.set_markup(f'<b>Connection:</b> {conn}')
        else:
            self.connection_label.set_text('')

        try:
            info = self.backend.get_info(device=dev)
            battery = self.backend.get_battery(device=dev)

            text_lines = []
            for key, val in info.items():
                if key != 'raw':
                    label = key.replace('_', ' ').title()
                    text_lines.append(f'<b>{label}:</b>  {val}')

            self.info_text.set_markup('\n'.join(text_lines))

            if battery['level'] is not None:
                self.battery_bar.set_value(battery['level'])
                status_str = battery.get('status', '')
                charging = f' ({status_str})' if status_str else ''
                self.battery_label.set_text(f'Battery: {battery["level"]}%{charging}')

                is_charging = battery.get('charging', False)
                self.battery_bar.set_charging(is_charging)

            else:
                self.battery_label.set_text(f'Battery: {battery["text"]}')

            if battery.get('level') is not None:
                self._last_battery = battery['level']
        except Exception as e:
            self.info_text.set_text(f'Error: {e}')
