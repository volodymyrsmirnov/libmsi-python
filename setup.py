'''
 Copyright (C) 2015, Vladimir Smirnov (vladimir@smirnov.im)
 This program is distributed in the hope that it will be useful, but WITHOUT
 ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
 FOR A PARTICULAR PURPOSE.  See the license for more details.
'''
from distutils.core import setup

setup(
    name='libmsi-python',
    version='0.0.1',
    description='Python bindings for libmsi from msitools. Read only for now.',
    author='Vladimir Smirnov',
    author_email='vladimir@smirnov.im',
    url='https://github.com/mindcollapse/libmsi-python',
    license='BSD',
    py_modules=['msi'],
    install_requires=['cffi']
)

