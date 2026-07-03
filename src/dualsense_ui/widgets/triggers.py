import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk

from ..backend import TriggerSide, TriggerMode


MODE_LABELS = {
    TriggerMode.OFF: 'Off (no effect)',
    TriggerMode.FEEDBACK: 'Feedback (resistance)',
    TriggerMode.WEAPON: 'Weapon (gun trigger)',
    TriggerMode.BOW: 'Bow',
    TriggerMode.GALLOPING: 'Galloping',
    TriggerMode.MACHINE: 'Machine (vibrating)',
    TriggerMode.VIBRATION: 'Vibration',
}


class TriggerWidget(Gtk.Box):
    def __init__(self, backend, get_device, parent_window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.backend = backend
        self.get_device = get_device
        self.parent_window = parent_window
        self._side = TriggerSide.BOTH
        self._build_ui()

    def _build_ui(self):
        frame = Gtk.Frame(margin_top=12, margin_bottom=12, margin_start=12, margin_end=12)
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        vbox.set_margin_top(16)
        vbox.set_margin_bottom(16)
        vbox.set_margin_start(16)
        vbox.set_margin_end(16)

        lbl = Gtk.Label()
        lbl.set_markup('<big><b>Trigger Effects</b></big>')
        vbox.append(lbl)

        side_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        side_lbl = Gtk.Label(label='Trigger:')
        self.side_combo = Gtk.DropDown(
            model=Gtk.StringList.new(['Left + Right', 'Left', 'Right']),
        )
        self.side_combo.set_selected(0)
        self.side_combo.connect('notify::selected', self._send_trigger)
        side_box.append(side_lbl)
        side_box.append(self.side_combo)
        vbox.append(side_box)

        mode_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        mode_lbl = Gtk.Label(label='Mode:')
        modes = list(MODE_LABELS.values())
        self.mode_combo = Gtk.DropDown(
            model=Gtk.StringList.new(modes),
        )
        self.mode_combo.set_selected(0)
        self.mode_combo.connect('notify::selected', self._on_mode_changed)
        mode_box.append(mode_lbl)
        mode_box.append(self.mode_combo)
        vbox.append(mode_box)

        self.params_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.params_box.set_margin_top(8)
        vbox.append(self.params_box)

        self._param_widgets = {}
        self._current_mode = TriggerMode.OFF
        self._update_params()

        frame.set_child(vbox)
        self.append(frame)

    def _get_side(self):
        idx = self.side_combo.get_selected()
        return [TriggerSide.BOTH, TriggerSide.LEFT, TriggerSide.RIGHT][idx]

    def _get_mode(self):
        idx = self.mode_combo.get_selected()
        return list(MODE_LABELS.keys())[idx]

    def _on_mode_changed(self, dropdown, param):
        self._update_params()
        self._send_trigger()

    def _clear_params(self):
        while self.params_box.get_first_child():
            child = self.params_box.get_first_child()
            self.params_box.remove(child)
        self._param_widgets = {}

    def _add_param(self, name, lower, upper, default, step=1):
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        lbl = Gtk.Label(label=f'{name}:')
        adj = Gtk.Adjustment(value=default, lower=lower, upper=upper, step_increment=step, page_increment=step*5)
        scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=adj)
        scale.set_draw_value(True)
        scale.set_hexpand(True)
        scale.set_size_request(200, -1)
        adj.connect('value-changed', lambda a: self._send_trigger())
        box.append(lbl)
        box.append(scale)
        self.params_box.append(box)
        self._param_widgets[name.lower()] = adj

    def _update_params(self):
        self._clear_params()
        mode = self._get_mode()

        if mode == TriggerMode.FEEDBACK:
            self._add_param('Position', 0, 9, 0)
            self._add_param('Strength', 1, 8, 5)
        elif mode == TriggerMode.WEAPON:
            self._add_param('Start Position', 2, 7, 3)
            self._add_param('Stop Position', 3, 8, 6)
            self._add_param('Strength', 1, 8, 5)
        elif mode == TriggerMode.BOW:
            self._add_param('Start Position', 1, 8, 2)
            self._add_param('Stop Position', 2, 8, 6)
            self._add_param('Strength', 1, 8, 5)
            self._add_param('Snap Force', 1, 8, 3)
        elif mode == TriggerMode.GALLOPING:
            self._add_param('Start Position', 0, 8, 0)
            self._add_param('Stop Position', 1, 9, 6)
            self._add_param('First Foot', 0, 6, 2)
            self._add_param('Second Foot', 1, 7, 5)
            self._add_param('Frequency', 1, 255, 8, step=1)
        elif mode == TriggerMode.MACHINE:
            self._add_param('Start Position', 1, 8, 2)
            self._add_param('Stop Position', 2, 9, 7)
            self._add_param('Strength A', 0, 7, 3)
            self._add_param('Strength B', 0, 7, 6)
            self._add_param('Frequency', 1, 255, 8, step=1)
            self._add_param('Period', 0, 255, 10, step=1)
        elif mode == TriggerMode.VIBRATION:
            self._add_param('Position', 0, 9, 4)
            self._add_param('Amplitude', 1, 8, 5)
            self._add_param('Frequency', 1, 255, 8, step=1)
        elif mode == TriggerMode.OFF:
            placeholder = Gtk.Label(label='No parameters needed — removes all effects')
            placeholder.set_margin_top(8)
            self.params_box.append(placeholder)

    def _send_trigger(self, *args):
        mode = self._get_mode()
        side = self._get_side()
        params = [int(adj.get_value()) for adj in self._param_widgets.values()]

        try:
            self.backend.set_trigger(side, mode.value, params if params else None, device=self.get_device())
        except Exception as e:
            self.parent_window.show_error(f'Trigger Error: {e}')
