.PHONY: all run install uninstall clean flatpak check desktop

APP=dualsense-ui
SRC=src

all: install

run:
	python3 $(SRC)/main.py

install:
	pip3 install --user -e .
	mkdir -p ~/.local/share/applications \
		~/.local/share/icons/hicolor/scalable/apps \
		~/.local/share/icons/hicolor/symbolic/devices
	cp data/com.dualsenseui.app.desktop ~/.local/share/applications/
	cp data/icons/com.dualsenseui.svg ~/.local/share/icons/hicolor/scalable/apps/
	cp data/icons/usb-symbolic.svg ~/.local/share/icons/hicolor/symbolic/devices/
	@echo "Installed. Run: dualsense-ui"

uninstall:
	pip3 uninstall -y $(APP) 2>/dev/null || true
	rm -f ~/.local/bin/$(APP) ~/.local/share/applications/com.dualsenseui.app.desktop

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete
	rm -rf *.egg-info

check:
	python3 -m pytest tests/ -v --tb=short

flatpak:
	flatpak-builder --force-clean build-dir flatpak/com.dualsenseui.yml
	flatpak-builder --run build-dir flatpak/com.dualsenseui.yml
