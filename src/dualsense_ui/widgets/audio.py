import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk

from ..backend import SpeakerMode, MicMode, MicLedMode


class AudioWidget(Gtk.Box):
    def __init__(self, backend, get_device, parent_window, get_connection_type):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.backend = backend
        self.get_device = get_device
        self.parent_window = parent_window
        self.get_connection_type = get_connection_type
        self._build_ui()

    def _build_ui(self):
        self.bt_warning = Gtk.Label(label='')
        self.bt_warning.set_markup(
            '<span color="orange">⚠ Audio controls work over Bluetooth, '
            'but audio streaming (sound/mic) only functions over USB.</span>'
        )
        self.bt_warning.set_wrap(True)
        self.bt_warning.set_xalign(0)
        self.bt_warning.set_margin_start(12)
        self.bt_warning.set_margin_end(12)
        self.bt_warning.set_margin_top(8)
        self.append(self.bt_warning)
        self._update_bt_warning()

        mic_frame = Gtk.Frame(margin_top=8, margin_bottom=12, margin_start=12, margin_end=12)
        mic_frame.set_child(self._build_mic_section())
        self.append(mic_frame)

        speaker_frame = Gtk.Frame(margin_bottom=12, margin_start=12, margin_end=12)
        speaker_frame.set_child(self._build_speaker_section())
        self.append(speaker_frame)

    def _build_mic_section(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(16)
        box.set_margin_bottom(16)
        box.set_margin_start(16)
        box.set_margin_end(16)

        lbl = Gtk.Label()
        lbl.set_markup('<big><b>Microphone</b></big>')
        box.append(lbl)

        row1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        row1_lbl = Gtk.Label(label='Microphone:')
        self.mic_switch = Gtk.Switch()
        self.mic_switch.set_active(True)
        self.mic_switch.connect('state-set', self._on_mic_switch)
        row1.append(row1_lbl)
        row1.append(self.mic_switch)
        box.append(row1)

        row2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        row2_lbl = Gtk.Label(label='LED Mode:')
        self.mic_led_combo = Gtk.DropDown(
            model=Gtk.StringList.new(['On', 'Off', 'Pulse']),
        )
        self.mic_led_combo.set_selected(0)
        self.mic_led_combo.connect('notify::selected', self._on_mic_led_changed)
        row2.append(row2_lbl)
        row2.append(self.mic_led_combo)
        box.append(row2)

        row3 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        row3_lbl = Gtk.Label(label='Mode:')
        self.mic_mode_combo = Gtk.DropDown(
            model=Gtk.StringList.new(['Chat', 'ASR (Speech Rec)', 'Both']),
        )
        self.mic_mode_combo.set_selected(0)
        self.mic_mode_combo.connect('notify::selected', self._on_mic_mode_changed)
        row3.append(row3_lbl)
        row3.append(self.mic_mode_combo)
        box.append(row3)

        row4 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        row4_lbl = Gtk.Label(label='Volume:')
        self.mic_volume_adj = Gtk.Adjustment(value=200, lower=0, upper=255, step_increment=1, page_increment=10)
        self.mic_volume_scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=self.mic_volume_adj)
        self.mic_volume_scale.set_draw_value(True)
        self.mic_volume_scale.set_hexpand(True)
        self.mic_volume_scale.connect('value-changed', self._on_mic_volume_changed)
        row4.append(row4_lbl)
        row4.append(self.mic_volume_scale)
        box.append(row4)

        return box

    def _build_speaker_section(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(16)
        box.set_margin_bottom(16)
        box.set_margin_start(16)
        box.set_margin_end(16)

        lbl = Gtk.Label()
        lbl.set_markup('<big><b>Speaker</b></big>')
        box.append(lbl)

        row1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        row1_lbl = Gtk.Label(label='Audio Output:')
        self.speaker_combo = Gtk.DropDown(
            model=Gtk.StringList.new(['Internal Speaker', 'Headphone', 'Mono Headphone', 'Both']),
        )
        self.speaker_combo.set_selected(0)
        self.speaker_combo.connect('notify::selected', self._on_speaker_changed)
        row1.append(row1_lbl)
        row1.append(self.speaker_combo)
        box.append(row1)

        row2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        row2_lbl = Gtk.Label(label='Volume:')
        self.volume_adj = Gtk.Adjustment(value=200, lower=0, upper=255, step_increment=1, page_increment=10)
        self.volume_scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=self.volume_adj)
        self.volume_scale.set_draw_value(True)
        self.volume_scale.set_hexpand(True)
        self.volume_scale.connect('value-changed', self._on_volume_changed)
        row2.append(row2_lbl)
        row2.append(self.volume_scale)
        box.append(row2)

        return box

    def _update_bt_warning(self):
        conn = self.get_connection_type() if hasattr(self, 'get_connection_type') else None
        self.bt_warning.set_visible(conn == 'Bluetooth')

    def _on_mic_switch(self, switch, state):
        self._safe_call(self.backend.set_mic, state)

    def _on_mic_led_changed(self, dropdown, param):
        modes = [MicLedMode.ON, MicLedMode.OFF, MicLedMode.PULSE]
        idx = dropdown.get_selected()
        self._safe_call(self.backend.set_mic_led, modes[idx])

    def _on_mic_mode_changed(self, dropdown, param):
        modes = [MicMode.CHAT, MicMode.ASR, MicMode.BOTH]
        idx = dropdown.get_selected()
        self._safe_call(self.backend.set_mic_mode, modes[idx])

    def _on_mic_volume_changed(self, scale):
        vol = int(scale.get_value())
        self._safe_call(self.backend.set_mic_volume, vol)

    def _on_speaker_changed(self, dropdown, param):
        modes = [SpeakerMode.INTERNAL, SpeakerMode.HEADPHONE, SpeakerMode.MONOHEADPHONE, SpeakerMode.BOTH]
        idx = dropdown.get_selected()
        self._safe_call(self.backend.set_speaker, modes[idx])

    def _on_volume_changed(self, scale):
        vol = int(scale.get_value())
        self._safe_call(self.backend.set_volume, vol)

    def _safe_call(self, func, *args):
        dev = self.get_device()
        try:
            func(*args, device=dev)
        except Exception as e:
            self._show_error(str(e))

    def _show_error(self, msg):
        self.parent_window.show_error(f'Audio Error: {msg}')
