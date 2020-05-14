# -*- coding: utf-8 -*-
from setuptools import setup


short_description = \
    'Check for python builtins being used as variables or parameters.'


long_description = '{0}\n{1}'.format(
    open('README.rst').read(),
    open('CHANGES.rst').read(),
)


setup(
    name='flake8-builtins',
    version='1.5.3',
    description=short_description,
    long_description=long_description,
    # Get more from https://pypi.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Framework :: Flake8',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development',
        'Topic :: Software Development :: Quality Assurance',
    ],
    keywords='pep8 flake8 python',
    author='Gil Forcada',
    author_email='gil.gnome@gmail.com',
    url='https://github.com/gforcada/flake8-builtins',
    license='GPL version 2',
    py_modules=['flake8_builtins'],
    include_package_data=True,
    test_suite='run_tests',
    zip_safe=False,
    install_requires=[
        'flake8',
    ],
    extras_require={
        'test': [
            'coverage',
            'coveralls',
            'mock',
            'pytest',
            'pytest-cov',
        ],
    },
    entry_points={
        'flake8.extension': ['A00 = flake8_builtins:BuiltinsChecker'],
    },
)
