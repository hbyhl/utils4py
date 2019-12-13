from setuptools import find_packages, setup

extras_require = {}

NAME = "utils4py"
VERSION = "0.1.13"

setup(
    name=NAME,
    version=VERSION,
    description="A set of useful utilities for python",
    author='plusplus1',
    author_email='comeson@126.com',
    url='https://github.com/plusplus1/utils4py',
    packages=find_packages(exclude=('tests', 'tests.*')),
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.6',
    ],
    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*',
    install_requires=[
        "six",
        "flask",
        "PyMySQL",
        "redis",
        "gevent",
        "pymongo",
        "pika",
    ],
    extras_require=extras_require,
)
