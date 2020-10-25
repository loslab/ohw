#!/usr/bin/env python

import setuptools

setuptools.setup(
        name="ohw",
        version="1.3",
        author="Oliver Schneider",
        author_email="oliver.schneider@igb.fraunhofer.de",
        description="optical determination of cardiomyocyte contractility",
        long_description="",
        url="https://github.com/loslab/ohw",
        packages=['ohw'],
        entry_points={
            'console_scripts': ['ohw_gui=ohw.OHWGUI:run_gui'],
            },
        )