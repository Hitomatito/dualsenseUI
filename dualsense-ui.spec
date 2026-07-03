%global appname dualsense-ui

Name:          dualsense-ui
Version:       1.0.0
Release:       1%{?dist}
Summary:       Graphical interface for PlayStation DualSense controllers

License:       GPL-3.0-or-later
URL:           https://github.com/Hitomatito/dualsenseUI
Source0:       %{url}/archive/v%{version}/%{appname}-v%{version}.tar.gz

BuildArch:     noarch
BuildRequires: python3-devel
BuildRequires: python3-setuptools
BuildRequires: desktop-file-utils
BuildRequires: libappstream-glib

Requires:      python3-gobject
Requires:      python3-gobject-cairo
Requires:      gtk4
Requires:      dualsensectl
Requires:      python3-hidapi
Requires:      python3-evdev

%description
DualSense UI provides a graphical interface for configuring and
monitoring PlayStation DualSense and DualSense Edge controllers on Linux.

Features:
- Real-time input monitor (buttons, sticks, triggers, gyro, touchpad)
- Lightbar color and brightness control
- Microphone and speaker audio settings
- Adaptive trigger configuration (7 modes)
- Firmware updates
- Battery monitoring with animated gauge

%prep
%autosetup -n %{appname}

%build
%py3_build

%install
%py3_install
# Desktop file
install -Dm644 data/com.dualsenseui.app.desktop \
  %{buildroot}%{_datadir}/applications/com.dualsenseui.app.desktop
# Icons
install -Dm644 data/icons/com.dualsenseui.svg \
  %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/com.dualsenseui.svg
install -Dm644 data/icons/usb-symbolic.svg \
  %{buildroot}%{_datadir}/icons/hicolor/symbolic/devices/usb-symbolic.svg
# Data files
mkdir -p %{buildroot}%{_datadir}/dualsense-ui
cp data/style.css %{buildroot}%{_datadir}/dualsense-ui/style.css
cp -r data/icons %{buildroot}%{_datadir}/dualsense-ui/icons

%check
%py3_check

%post
%{_bindir}/gtk-update-icon-cache %{_datadir}/icons/hicolor &>/dev/null || :

%postun
%{_bindir}/gtk-update-icon-cache %{_datadir}/icons/hicolor &>/dev/null || :

%files
%doc README.md
%license LICENSE
%{_bindir}/dualsense-ui
%{python3_sitelib}/dualsense_ui/
%{_datadir}/applications/com.dualsenseui.app.desktop
%{_datadir}/icons/hicolor/scalable/apps/com.dualsenseui.svg
%{_datadir}/icons/hicolor/symbolic/devices/usb-symbolic.svg
%{_datadir}/dualsense-ui/

%changelog
* Thu Jul 02 2026 DualSense UI Contributors - 1.0.0-1
- Initial release
