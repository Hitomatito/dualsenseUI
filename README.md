# DualSense UI

Graphical interface for configuring and monitoring PlayStation DualSense and DualSense Edge controllers on Linux.

![CI](https://github.com/Hitomatito/dualsenseUI/actions/workflows/ci.yml/badge.svg)
[![Flatpak](https://github.com/Hitomatito/dualsenseUI/actions/workflows/release.yml/badge.svg)](https://github.com/Hitomatito/dualsenseUI/releases)

## Features

- **Monitor** — real-time input viewer: sticks, triggers, face buttons, D-pad, gyroscope, accelerometer, touchpad, battery
- **Lightbar** — color picker, brightness, LED dimming, player LEDs
- **Audio** — microphone on/off/mode/volume, speaker mode/volume
- **Triggers** — adaptive trigger modes: Feedback, Weapon, Bow, Galloping, Machine, Vibration
- **Info** — firmware version, serial, battery level with animated gauge
- **Advanced** — vibration attenuation, firmware update

## Dependencies

- Python 3.9+
- `dualsensectl` — backend tool ([GitHub](https://github.com/nowrep/dualsensectl))
- GTK 4 (runtime + development headers)
- Cairo (development headers)
- `libhidapi-hidraw`

### Install system dependencies

**Fedora / RHEL / Mageia:**

```sh
sudo dnf install python3-gobject gtk4-devel cairo-devel libhidapi-devel pkgconfig
```

**Debian / Ubuntu / Linux Mint:**

```sh
sudo apt install python3-gi gir1.2-gtk-4.0 libcairo2-dev libhidapi-dev pkg-config
```

**Arch / Manjaro / EndeavourOS:**

```sh
sudo pacman -S python-gobject gtk4 cairo hidapi pkgconf
```

**openSUSE:**

```sh
sudo zypper install python3-gobject Gtk4-devel cairo-devel hidapi-devel pkgconfig
```

**Void Linux:**

```sh
sudo xbps-install python3-gobject gtk4-devel cairo-devel hidapi-devel pkg-config
```

**Solus:**

```sh
sudo eopkg install python3-gobject gtk4-devel cairo-devel hidapi-devel pkg-config
```

## Install

### From source

```sh
git clone https://github.com/Hitomatito/dualsenseUI.git
cd dualsenseUI

# Install dualsensectl (build from source):
# https://github.com/nowrep/dualsensectl

make install
```

Then run:

```sh
dualsense-ui
```

Or without installing:

```sh
make run
```

### Udev rules

Create `/etc/udev/rules.d/70-dualsensectl.rules`:

```
# PS5 DualSense controller over USB hidraw
KERNEL=="hidraw*", ATTRS{idVendor}=="054c", ATTRS{idProduct}=="0ce6", MODE="0660", TAG+="uaccess"

# PS5 DualSense controller over bluetooth hidraw
KERNEL=="hidraw*", KERNELS=="*054C:0CE6*", MODE="0660", TAG+="uaccess"

# PS5 DualSense Edge controller over USB hidraw
KERNEL=="hidraw*", ATTRS{idVendor}=="054c", ATTRS{idProduct}=="0df2", MODE="0660", TAG+="uaccess"

# PS5 DualSense Edge controller over bluetooth hidraw
KERNEL=="hidraw*", KERNELS=="*054C:0DF2*", MODE="0660", TAG+="uaccess"
```

Reload:

```sh
sudo udevadm control --reload-rules
sudo udevadm trigger
```

> **Note:** If the Monitor tab cannot read the touchpad or motion sensors on Bluetooth, ensure your user is in the `input` group:
> ```sh
> sudo usermod -aG input $USER
> ```
> Then log out and back in.

## Run tests

```sh
make check
# or
python3 -m pytest tests/ -v
```

## Development

```sh
make run              # run from source tree
make install          # install locally
make uninstall        # remove
```

## Flatpak

Build and run with Flatpak:

```sh
make flatpak
```
