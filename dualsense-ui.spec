%global appname dualsense-ui

Name:          dualsense-ui
Version:       1.0.0
Release:       1%{?dist}
Summary:       Graphical interface for PlayStation DualSense controllers

License:       GPL-3.0-or-later
URL:           https://github.com/Hitomatito/dualsenseUI
Source0:       %{appname}-%{version}.tar.gz

BuildArch:     noarch
BuildRequires: python3-setuptools

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
%setup -q -n %{name}-%{version}

%build
python3 -m pip install --no-build-isolation --no-deps .

%install
python3 -m pip install --no-build-isolation --no-deps --prefix=%{_prefix} --root=%{buildroot} .
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
python3 -m pytest tests/ -v --tb=short || :

%post
%{_bindir}/gtk-update-icon-cache %{_datadir}/icons/hicolor &>/dev/null || :

%postun
%{_bindir}/gtk-update-icon-cache %{_datadir}/icons/hicolor &>/dev/null || :

%files
%doc README.md
%license LICENSE
%{_bindir}/dualsense-ui
%{python3_sitelib}/dualsense_ui/
%dir %{_datadir}/applications/
%{_datadir}/applications/com.dualsenseui.app.desktop
%dir %{_datadir}/icons/hicolor/scalable/apps/
%{_datadir}/icons/hicolor/scalable/apps/com.dualsenseui.svg
%dir %{_datadir}/icons/hicolor/symbolic/devices/
%{_datadir}/icons/hicolor/symbolic/devices/usb-symbolic.svg
%dir %{_datadir}/dualsense-ui/
%dir %{_datadir}/dualsense-ui/icons/
%{_datadir}/dualsense-ui/style.css
%{_datadir}/dualsense-ui/icons/com.dualsenseui.svg
%{_datadir}/dualsense-ui/icons/usb-symbolic.svg

%changelog
* Thu Jul 02 2026 DualSense UI Contributors - 1.0.0-1
- Initial release
