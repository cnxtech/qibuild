#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2012-2018 SoftBank Robotics. All rights reserved.
# Use of this source code is governed by a BSD-style license (see the COPYING file).
""" Generate source/generated.rst """
from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function


def main():
    """ Main Entry Point """
    with open("source/generated.rst", "w") as fp:
        fp.write("""Generated section\n=================\n\n""")


if __name__ == "__main__":
    main()
