import re
from pathlib import Path

from setuptools import setup, find_packages


_DATA = 'share/dualsense-ui'


def _read_version():
    """Single source of truth: src/dualsense_ui/__init__.py"""
    init = Path(__file__).parent / 'src' / 'dualsense_ui' / '__init__.py'
    match = re.search(r'^__version__\s*=\s*["\']([^"\']+)["\']', init.read_text(), re.M)
    if not match:
        raise RuntimeError(f'Unable to find __version__ in {init}')
    return match.group(1)


setup(
    name='dualsense-ui',
    version=_read_version(),
    packages=find_packages('src'),
    package_dir={'': 'src'},
    entry_points={
        'console_scripts': [
            'dualsense-ui=dualsense_ui.__main__:main',
        ],
    },
    data_files=[
        (_DATA, ['data/style.css']),
        (f'{_DATA}/icons', [
            'data/icons/com.dualsenseui.app.svg',
            'data/icons/usb-symbolic.svg',
        ]),
    ],
    python_requires='>=3.9',
    install_requires=[
        'pygobject>=3.42',
        'hidapi>=0.14',
        'evdev>=1.4.0',
    ],
    description='GUI for configuring PlayStation DualSense controllers',
)
