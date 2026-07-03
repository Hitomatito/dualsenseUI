import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib, Gdk


class LightbarWidget(Gtk.Box):
    def __init__(self, backend, get_device, parent_window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.backend = backend
        self.get_device = get_device
        self.parent_window = parent_window
        self._updating = False
        self._build_ui()

    def _build_ui(self):
        group = Gtk.SizeGroup(mode=Gtk.SizeGroupMode.HORIZONTAL)

        frame = Gtk.Frame(margin_top=12, margin_bottom=12, margin_start=12, margin_end=12)
        frame.set_child(self._build_color_section(group))
        self.append(frame)

        frame2 = Gtk.Frame(margin_bottom=12, margin_start=12, margin_end=12)
        frame2.set_child(self._build_leds_section(group))
        self.append(frame2)

    def _build_color_section(self, group):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_top(16)
        box.set_margin_bottom(16)
        box.set_margin_start(16)
        box.set_margin_end(16)

        lbl = Gtk.Label()
        lbl.set_markup('<big><b>Lightbar</b></big>')
        box.append(lbl)

        power_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        power_lbl = Gtk.Label(label='Lightbar Power:')
        group.add_widget(power_lbl)
        self.power_switch = Gtk.Switch()
        self.power_switch.set_active(True)
        self.power_switch.connect('state-set', self._on_power_switch)
        power_box.append(power_lbl)
        power_box.append(self.power_switch)
        box.append(power_box)

        color_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        color_lbl = Gtk.Label(label='Color:')
        group.add_widget(color_lbl)
        self.color_button = Gtk.ColorButton()
        rgba = Gdk.RGBA()
        rgba.parse('blue')
        self.color_button.set_rgba(rgba)
        self.color_button.connect('color-set', self._on_color_set)
        self.color_button.set_halign(Gtk.Align.START)
        color_box.append(color_lbl)
        color_box.append(self.color_button)
        box.append(color_box)

        bright_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        bright_lbl = Gtk.Label(label='Brightness:')
        group.add_widget(bright_lbl)
        self.brightness_adj = Gtk.Adjustment(value=125, lower=0, upper=255, step_increment=1, page_increment=10)
        self.brightness_scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=self.brightness_adj)
        self.brightness_scale.set_draw_value(True)
        self.brightness_scale.set_hexpand(True)
        self.brightness_scale.connect('value-changed', self._on_brightness_changed)
        bright_lbl_tmp = Gtk.Label(label='Brightness:')
        group.add_widget(bright_lbl_tmp)
        bright_box.append(bright_lbl)
        bright_box.append(self.brightness_scale)
        box.append(bright_box)

        return box

    def _build_leds_section(self, group):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_top(16)
        box.set_margin_bottom(16)
        box.set_margin_start(16)
        box.set_margin_end(16)

        lbl = Gtk.Label()
        lbl.set_markup('<big><b>LEDs</b></big>')
        box.append(lbl)

        led_bright_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        led_bright_lbl = Gtk.Label(label='LED Brightness:')
        group.add_widget(led_bright_lbl)
        self.led_brightness_combo = Gtk.DropDown(
            model=Gtk.StringList.new(['Off (0)', 'Low (1)', 'High (2)']),
        )
        self.led_brightness_combo.set_selected(1)
        self.led_brightness_combo.connect('notify::selected', self._on_led_brightness_changed)
        led_bright_box.append(led_bright_lbl)
        led_bright_box.append(self.led_brightness_combo)
        box.append(led_bright_box)

        player_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        player_lbl = Gtk.Label(label='Player LEDs:')
        group.add_widget(player_lbl)
        self.player_leds_adj = Gtk.Adjustment(value=1, lower=0, upper=7, step_increment=1, page_increment=1)
        self.player_leds_spin = Gtk.SpinButton(adjustment=self.player_leds_adj)
        self.player_leds_spin.connect('value-changed', self._on_player_leds_changed)
        player_box.append(player_lbl)
        player_box.append(self.player_leds_spin)
        box.append(player_box)

        return box

    def _on_power_switch(self, switch, state):
        self._safe_call(self.backend.set_lightbar_power, state)

    def _on_color_set(self, btn):
        self._send_color()

    def _on_brightness_changed(self, scale):
        self._send_color()

    def _on_led_brightness_changed(self, dropdown, param):
        val = dropdown.get_selected()
        self._safe_call(self.backend.set_led_brightness, val)

    def _on_player_leds_changed(self, spin):
        val = int(spin.get_value())
        self._safe_call(self.backend.set_player_leds, val, True)

    def _send_color(self):
        rgba = self.color_button.get_rgba()
        r = min(255, max(0, int(rgba.red * 255)))
        g = min(255, max(0, int(rgba.green * 255)))
        b = min(255, max(0, int(rgba.blue * 255)))
        brightness = int(self.brightness_adj.get_value())
        self._safe_call(self.backend.set_lightbar_color, r, g, b, brightness)

    def _safe_call(self, func, *args):
        dev = self.get_device()
        try:
            func(*args, device=dev)
        except Exception as e:
            self._show_error(str(e))

    def _show_error(self, msg):
        self.parent_window.show_error(f'Lightbar Error: {msg}')
