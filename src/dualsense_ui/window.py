import os
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib, Gio, Gdk, GdkPixbuf
from .backend import list_devices
from .widgets.lightbar import LightbarWidget
from .widgets.audio import AudioWidget
from .widgets.info import InfoWidget
from .widgets.triggers import TriggerWidget
from .widgets.advanced import AdvancedWidget
from .widgets.monitor import InputMonitorWidget



class DualsenseWindow(Gtk.ApplicationWindow):
    def __init__(self, application, backend):
        super().__init__(application=application)
        self.backend = backend
        self._selected_device = None
        self._connection_type = None

        self.set_title('DualSense Controller')
        self.set_default_size(700, 600)
        self.set_icon_name('com.dualsenseui')

        self._device_cache = []
        self._last_device_ids = set()

        self._build_ui()
        self._refresh_devices()
        self._start_polling()

    def _build_ui(self):
        self._overlay = Gtk.Overlay()

        main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        main_vbox.add_css_class('dualsense-content')

        header = Gtk.HeaderBar()
        self.set_titlebar(header)

        device_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        device_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.conn_icon = Gtk.Image.new_from_icon_name('input-gaming-symbolic')
        self.conn_icon.set_pixel_size(16)
        self.conn_icon.set_valign(Gtk.Align.CENTER)
        self.conn_icon.add_css_class('connection-icon')
        device_row.append(self.conn_icon)

        self.device_dropdown = Gtk.DropDown(
            model=Gtk.StringList.new(['No controller detected']),
        )
        self.device_dropdown.connect('notify::selected', self._on_device_selected)
        device_row.append(self.device_dropdown)
        device_box.append(device_row)

        self.connection_label = Gtk.Label(label='')
        self.connection_label.set_margin_top(2)
        self.connection_label.add_css_class('subtitle')
        device_box.append(self.connection_label)

        header.set_title_widget(device_box)

        power_img = Gtk.Image.new_from_icon_name('system-shutdown-symbolic')
        power_img.set_valign(Gtk.Align.CENTER)
        self.power_btn = Gtk.Button(child=power_img)
        self.power_btn.add_css_class('header-glass-btn')
        self.power_btn.set_tooltip_text('Power off controller (Bluetooth only)')
        self.power_btn.connect('clicked', self._on_power_off)
        header.pack_end(self.power_btn)

        about_img = Gtk.Image.new_from_icon_name('help-about-symbolic')
        about_img.set_valign(Gtk.Align.CENTER)
        about_btn = Gtk.Button(child=about_img)
        about_btn.add_css_class('header-glass-btn')
        about_btn.connect('clicked', self._show_about)
        header.pack_end(about_btn)

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)

        self.info_widget = InfoWidget(self.backend, self._get_device, self, self._get_connection_type)
        self.lightbar_widget = LightbarWidget(self.backend, self._get_device, self)
        self.audio_widget = AudioWidget(self.backend, self._get_device, self, self._get_connection_type)
        self.triggers_widget = TriggerWidget(self.backend, self._get_device, self)
        self.advanced_widget = AdvancedWidget(self.backend, self._get_device, self, self._get_connection_type)
        self.monitor_widget = InputMonitorWidget(self.backend, self._get_device, self, self._get_connection_type)

        self.stack.add_titled(self.info_widget, 'info', 'Info')
        self.stack.add_titled(self.lightbar_widget, 'lightbar', 'Lightbar')
        self.stack.add_titled(self.audio_widget, 'audio', 'Audio')
        self.stack.add_titled(self.triggers_widget, 'triggers', 'Triggers')
        self.stack.add_titled(self.advanced_widget, 'advanced', 'Advanced')
        self.stack.add_titled(self.monitor_widget, 'monitor', 'Monitor')

        stack_switcher = Gtk.StackSwitcher()
        stack_switcher.set_stack(self.stack)
        stack_switcher.set_halign(Gtk.Align.CENTER)
        main_vbox.append(stack_switcher)
        main_vbox.append(self.stack)

        self._overlay.set_child(main_vbox)
        self.set_child(self._overlay)

    def _get_device(self):
        return self._selected_device

    def _get_connection_type(self):
        return self._connection_type

    def _refresh_devices(self):
        try:
            devices = list_devices()
        except Exception:
            devices = []
        self._device_cache = devices

        current_ids = {d['id'] for d in devices}
        prev_ids = getattr(self, '_last_device_ids', set())

        store = Gtk.StringList.new([])
        if not devices:
            store.append('No controller detected')
            self._selected_device = None
            self._connection_type = None
        else:
            for dev in devices:
                store.append(f'{dev["id"]}')

            if self._selected_device not in current_ids:
                self._selected_device = devices[0]['id']
                self._connection_type = devices[0].get('connection', 'USB')

        self._last_device_ids = current_ids

        self._updating_devices = True
        self.device_dropdown.set_model(store)
        if devices and self._selected_device:
            idx = next((i for i, d in enumerate(devices) if d['id'] == self._selected_device), 0)
            self.device_dropdown.set_selected(idx)
        elif devices:
            self.device_dropdown.set_selected(0)
        else:
            self.device_dropdown.set_selected(Gtk.INVALID_LIST_POSITION)
        self._updating_devices = False

        self._update_connection_ui()

    def _update_connection_ui(self):
        conn = self._connection_type
        self.connection_label.remove_css_class('connection-badge')
        self.connection_label.remove_css_class('bluetooth')
        self.connection_label.remove_css_class('usb')
        if conn == 'Bluetooth':
            self.conn_icon.set_from_icon_name('bluetooth-symbolic')
            self.connection_label.set_text('Bluetooth')
            self.connection_label.add_css_class('connection-badge')
            self.connection_label.add_css_class('bluetooth')
            self.power_btn.set_sensitive(True)
            self.power_btn.set_tooltip_text('Power off controller')
        elif conn == 'USB':
            self.conn_icon.set_from_icon_name('usb-symbolic')
            self.connection_label.set_text('USB')
            self.connection_label.add_css_class('connection-badge')
            self.connection_label.add_css_class('usb')
            self.power_btn.set_sensitive(False)
            self.power_btn.set_tooltip_text('Power off unavailable over USB (Bluetooth only)')
        else:
            self.conn_icon.set_from_icon_name('input-gaming-symbolic')
            self.connection_label.set_text('')
            self.power_btn.set_sensitive(False)
            self.power_btn.set_tooltip_text('Power off controller (Bluetooth only)')

    def _on_device_selected(self, dropdown, param):
        if getattr(self, '_updating_devices', False):
            return
        pos = dropdown.get_selected()
        cache = getattr(self, '_device_cache', [])
        if 0 <= pos < len(cache):
            self._selected_device = cache[pos]['id']
            self._connection_type = cache[pos].get('connection', 'USB')
            self._update_connection_ui()
            self.info_widget._refresh()
        else:
            self._selected_device = None
            self._connection_type = None
            self._update_connection_ui()

    def _on_power_off(self, btn):
        dev = self._get_device()
        conn = self._get_connection_type()
        if not dev or conn != 'Bluetooth':
            self.show_error('Power off only works over Bluetooth')
            return
        self.backend.power_off(device=dev)

    def _show_about(self, btn):
        about = Gtk.AboutDialog()
        about.set_transient_for(self)
        about.set_program_name('DualSense UI')
        about.set_version('1.0.0')
        about.set_comments(
            'Graphical interface for configuring and monitoring '
            'PlayStation DualSense and DualSense Edge controllers on Linux.\n\n'
            'Supports real-time lightbar color, adaptive triggers, '
            'audio controls, battery monitoring, and firmware updates '
            'via dualsensectl.'
        )
        about.set_copyright('© 2026 DualSense UI Contributors')
        about.set_website('https://github.com/nowrep/dualsensectl')
        about.set_website_label('dualsensectl (GitHub)')
        about.set_authors([
            'DualSense UI Contributors',
            'dualsensectl — nowrep',
        ])
        about.set_license_type(Gtk.License.GPL_3_0)

        svg_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'icons', 'com.dualsenseui.svg')
        icon_pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(svg_path, 128, 128)
        pad = 20
        w = icon_pixbuf.get_width() + pad * 2
        h = icon_pixbuf.get_height() + pad * 2
        bg = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, w, h)
        bg.fill(0xffffffff)
        icon_pixbuf.composite(
            bg, pad, pad,
            icon_pixbuf.get_width(), icon_pixbuf.get_height(),
            pad, pad,
            1.0, 1.0,
            GdkPixbuf.InterpType.BILINEAR, 255
        )
        about.set_logo(Gdk.Texture.new_for_pixbuf(bg))

        about.present()

    def show_error(self, message):
        lbl = Gtk.Label(label=message)
        lbl.add_css_class('error-label')
        lbl.set_margin_top(48)
        lbl.set_halign(Gtk.Align.CENTER)
        lbl.set_valign(Gtk.Align.START)
        self._overlay.add_overlay(lbl)
        GLib.timeout_add_seconds(3, lambda: self._remove_toast(lbl))

    def _remove_toast(self, label):
        self._overlay.remove_overlay(label)
        return False

    def _start_polling(self):
        GLib.timeout_add_seconds(2, self._poll_all)

    def _poll_all(self):
        self._refresh_devices()
        if self._selected_device:
            self.info_widget._refresh()
        return True
