import pathlib

import pkg_resources
from setuptools import setup
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

with pathlib.Path('requirements.txt').open() as requirements_txt:
    install_requires = [
        str(requirement)
        for requirement
        in pkg_resources.parse_requirements(requirements_txt)
    ]

setup(

    name='dedoc',

    version='0.0.1',

    description='Convert different document in tree structure',

    long_description=long_description,

    long_description_content_type='text/markdown',


    # url='https://github.com/pypa/sampleproject',  # Optional

    author='ISP RAS',

    author_email='kozlov-ilya@ispras.ru',  # Optional

    install_requires=install_requires,

    classifiers=[
        'Development Status :: 3 - Alpha',

        'Intended Audience :: Developers',

        'License :: OSI Approved :: MIT License',

        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3 :: Only',
    ],

    # keywords='sample setuptools development',  # Optional
    package_dir={'dedoc': 'dedoc'},  # Optional

    python_requires='>=3.5, <4',

)
