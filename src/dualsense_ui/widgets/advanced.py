import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib


class AdvancedWidget(Gtk.Box):
    def __init__(self, backend, get_device, parent_window, get_connection_type):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.backend = backend
        self.get_device = get_device
        self.parent_window = parent_window
        self.get_connection_type = get_connection_type
        self._build_ui()

    def _build_ui(self):
        atten_frame = Gtk.Frame(margin_top=12, margin_bottom=12, margin_start=12, margin_end=12)
        atten_frame.set_child(self._build_attenuation_section())
        self.append(atten_frame)

        fw_frame = Gtk.Frame(margin_bottom=12, margin_start=12, margin_end=12)
        fw_frame.set_child(self._build_firmware_section())
        self.append(fw_frame)

    def _build_attenuation_section(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(16)
        box.set_margin_bottom(16)
        box.set_margin_start(16)
        box.set_margin_end(16)

        lbl = Gtk.Label()
        lbl.set_markup('<big><b>Vibration Attenuation</b></big>')
        box.append(lbl)

        row1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        row1_lbl = Gtk.Label(label='Rumble/Haptic motors:')
        self.rumble_adj = Gtk.Adjustment(value=0, lower=0, upper=7, step_increment=1, page_increment=1)
        self.rumble_adj = Gtk.Adjustment(value=0, lower=0, upper=7, step_increment=1, page_increment=1)
        self.rumble_adj.connect('value-changed', self._on_attenuation_changed)
        self.rumble_scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=self.rumble_adj)
        self.rumble_scale.set_draw_value(True)
        self.rumble_scale.set_hexpand(True)
        row1.append(row1_lbl)
        row1.append(self.rumble_scale)
        box.append(row1)

        row2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        row2_lbl = Gtk.Label(label='Trigger vibration:')
        self.trigger_adj = Gtk.Adjustment(value=0, lower=0, upper=7, step_increment=1, page_increment=1)
        self.trigger_adj.connect('value-changed', self._on_attenuation_changed)
        self.trigger_scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=self.trigger_adj)
        self.trigger_scale.set_draw_value(True)
        self.trigger_scale.set_hexpand(True)
        row2.append(row2_lbl)
        row2.append(self.trigger_scale)
        box.append(row2)

        return box

    def _build_firmware_section(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(16)
        box.set_margin_bottom(16)
        box.set_margin_start(16)
        box.set_margin_end(16)

        lbl = Gtk.Label()
        lbl.set_markup('<big><b>Firmware Update</b></big>')
        box.append(lbl)

        self.fw_conn_note = Gtk.Label(label='')
        self.fw_conn_note.set_wrap(True)
        box.append(self.fw_conn_note)

        desc = Gtk.Label(label='Battery must be at least 10%.')
        desc.set_wrap(True)
        desc.set_xalign(0)
        box.append(desc)

        file_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.fw_path_label = Gtk.Label(label='No file selected')
        self.fw_path_label.set_hexpand(True)
        self.fw_path_label.set_xalign(0)
        file_box.append(self.fw_path_label)

        browse_btn = Gtk.Button(label='Browse...')
        browse_btn.connect('clicked', self._on_browse_fw)
        file_box.append(browse_btn)
        box.append(file_box)

        update_btn = Gtk.Button(label='Update Firmware')
        update_btn.add_css_class('suggested-action')
        update_btn.connect('clicked', self._on_update_fw)
        update_btn.set_halign(Gtk.Align.CENTER)
        self.update_btn = update_btn
        box.append(update_btn)

        self.fw_status = Gtk.Label(label='')
        box.append(self.fw_status)

        return box

    def _on_attenuation_changed(self, adj):
        rumble = int(self.rumble_adj.get_value())
        trigger = int(self.trigger_adj.get_value())
        self._safe_call(self.backend.set_attenuation, rumble, trigger)

    def _on_browse_fw(self, btn):
        dialog = Gtk.FileDialog()
        dialog.set_title('Select Firmware File')
        dialog.open(callback=self._on_fw_dialog_response)

    def _on_fw_dialog_response(self, dialog, result):
        try:
            file = dialog.open_finish(result)
            if file:
                self._fw_path = file.get_path()
                self.fw_path_label.set_text(self._fw_path)
        except GLib.Error:
            pass

    def _on_update_fw(self, btn):
        conn = self.get_connection_type()
        if conn == 'Bluetooth':
            self.fw_status.set_text('Firmware update requires USB connection')
            return

        path = getattr(self, '_fw_path', None)
        if not path:
            self.fw_status.set_text('Please select a firmware file first')
            return

        self.fw_status.set_text('Updating firmware... (this may take a while)')
        self.update_btn.set_sensitive(False)

        def do_update():
            try:
                self.backend.update_firmware(path, device=self.get_device())
                GLib.idle_add(lambda: self.fw_status.set_text('Update complete! Reconnect controller.'))
            except Exception as e:
                GLib.idle_add(lambda: self.fw_status.set_text(f'Update failed: {e}'))
            finally:
                GLib.idle_add(lambda: self.update_btn.set_sensitive(True))

        import threading
        t = threading.Thread(target=do_update, daemon=True)
        t.start()

    def _safe_call(self, func, *args):
        dev = self.get_device()
        try:
            func(*args, device=dev)
        except Exception as e:
            self._show_error(str(e))

    def _show_error(self, msg):
        self.parent_window.show_error(f'Error: {msg}')
