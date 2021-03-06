#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2012-2019 SoftBank Robotics. All rights reserved.
# Use of this source code is governed by a BSD-style license (see the COPYING file).
""" QiBuild """
from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function

from setuptools import setup

setup(
    name="with_distutils",
    py_modules=["foo"],
    entry_points={
        "console_scripts": [
            "foo = foo:main"
        ]
    }
)
