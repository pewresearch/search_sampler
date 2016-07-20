import os
from setuptools import setup, find_packages


with open(os.path.join(os.path.dirname(__file__), 'README.md'), 'r') as readme:
    README = str(readme.read())

os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

with open('requirements.txt') as reqs:
    install_requires = [
        str(line) for line in reqs.read().split('\n') if line and not line.startswith(('--', 'git+ssh'))
    ]
    dependency_links = [
        str(line) for line in reqs.read().split('\n') if line and line.startswith(('--', 'git+ssh'))
    ]

setup(
    name = 'search_sampler',
    version = '1.0.1',
    description = '',
    long_description = README,
    long_description_content_type='text/markdown',
    url = 'https://github.com/pewresearch/search_sampler',
    author = 'Pew Research Center',
    author_email = 'info@pewresearch.org',
    install_requires = install_requires,
    dependency_links = dependency_links,
    packages = find_packages(exclude = ['contrib', 'docs', 'tests']),
    include_package_data = True,
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Science/Research',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7'
    ],
    keywords = 'google, sampling, trends',
    license = 'MIT'
)
