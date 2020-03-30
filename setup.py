from setuptools import find_packages, setup

extras_require = {}

NAME = "utils4py"
VERSION = "0.0.1"

install_requires = []
with open('requirements.txt', 'rb') as f:
    for req in f.readlines():
        if not str(req).startswith('git+'):
            install_requires.append(bytes.decode(req.strip()))

setup(
    name=NAME,
    version=VERSION,
    description="A set of useful utilities for python",
    author='rct@42pay.com',
    author_email='rct@topay.com',
    url='http://gitlab.test2pay.com/rct/utils4j',
    packages=find_packages(exclude=('tests', 'tests.*')),
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
    ],
    python_requires='!=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*',
    install_requires=install_requires,
    extras_require=extras_require,
)
