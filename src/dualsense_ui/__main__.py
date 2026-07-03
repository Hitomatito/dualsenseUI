import sys
import os
import gi

gi.require_version('Gtk', '4.0')

from gi.repository import Gtk, GLib, Gio, Gdk

from .backend import DualsenseBackend
from .window import DualsenseWindow


APPLICATION_ID = 'com.dualsenseui.app'


def _find_data_dir():
    dirs = [
        os.environ.get('FLATPAK_DEST'),
        sys.prefix,
        '/app',
        '/usr',
        '/usr/local',
    ]
    for base in dirs:
        if base:
            p = os.path.join(base, 'share', 'dualsense-ui')
            if os.path.isdir(p):
                return p
    pkg_dir = os.path.dirname(os.path.abspath(__file__))
    dev = os.path.join(pkg_dir, '..', '..')
    if os.path.isdir(os.path.join(dev, 'data')):
        return os.path.join(dev, 'data')
    return pkg_dir


DATA_DIR = _find_data_dir()
STYLE_PATH = os.path.join(DATA_DIR, 'style.css')
ICONS_PATH = os.path.join(DATA_DIR, 'icons')


def _load_css():
    path = os.path.abspath(STYLE_PATH)
    if not os.path.exists(path):
        return
    provider = Gtk.CssProvider()
    provider.load_from_path(path)
    Gtk.StyleContext.add_provider_for_display(
        Gdk.Display.get_default(),
        provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
    )


class DualsenseApplication(Gtk.Application):
    def __init__(self):
        super().__init__(
            application_id=APPLICATION_ID,
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )
        self.backend = DualsenseBackend()

    def do_startup(self):
        Gtk.Application.do_startup(self)
        _load_css()
        icon_path = os.path.abspath(ICONS_PATH)
        if os.path.isdir(icon_path):
            theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())
            theme.add_search_path(icon_path)

    def do_activate(self):
        win = DualsenseWindow(application=self, backend=self.backend)
        win.present()


def main():
    app = DualsenseApplication()
    return app.run(sys.argv)


if __name__ == '__main__':
    sys.exit(main())
