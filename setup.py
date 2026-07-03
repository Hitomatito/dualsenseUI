from setuptools import setup, find_packages


_DATA = 'share/dualsense-ui'

setup(
    name='dualsense-ui',
    version='1.0.0',
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
            'data/icons/com.dualsenseui.svg',
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
