# -*- coding: utf-8 -*-
# pylint: disable=C0111,C0103
"""
Setup configurations for the taxonomy connector application.
"""

import os
import re

from setuptools import setup

VCS_PREFIXES = ('git+', 'hg+', 'bzr+', 'svn+', '-e git+')
base_path = os.path.dirname(__file__)
here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()


def get_version(*file_paths):
    """
    Extract the version string from the file at the given relative path fragments.
    """
    filename = os.path.join(os.path.dirname(__file__), *file_paths)
    version_file = open(filename).read()
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError('Unable to find version string.')


def get_requirements(requirements_file):
    """
    Get the contents of a file listing the requirements.
    """
    lines = open(requirements_file).readlines()
    dependencies = []
    dependency_links = []

    for line in lines:
        package = line.strip()
        if package.startswith('#'):
            # Skip pure comment lines
            continue

        package, *_ = package.partition(' #')
        package = package.strip()

        if any(package.startswith(prefix) for prefix in VCS_PREFIXES):
            # VCS reference for dev purposes, expect a trailing comment
            # with the normal requirement
            package_link, __, package = package.rpartition('#')

            # Remove -e <version_control> string
            package_link = re.sub(r'(.*)(?P<dependency_link>https?.*$)', r'\g<dependency_link>', package_link)
            package = re.sub(r'(egg=)?(?P<package_name>.*)==.*$', r'\g<package_name>', package)
            package_version = re.sub(r'.*[^=]==', '', line.strip())

            if package:
                dependency_links.append(
                    '{package_link}#egg={package}-{package_version}'.format(
                        package_link=package_link,
                        package=package,
                        package_version=package_version,
                    )
                )
        else:
            # Ignore any trailing comment
            package, *_ = package.partition('#')
            # Remove any whitespace and assume non-empty results are dependencies
            package = package.strip()

        if package:
            dependencies.append(package)
    return dependencies, dependency_links


REQUIREMENTS, DEPENDENCY_LINKS = get_requirements(os.path.join(base_path, 'requirements', 'base.in'))
# To get the version
VERSION = get_version('taxonomy', '__init__.py')
CHANGELOG = open(os.path.join(base_path, 'CHANGELOG.rst')).read()

setup(
    name='taxonomy-connector',
    version=VERSION,
    packages=[
        'taxonomy',
    ],
    include_package_data=True,
    description='Taxonomy connector',
    long_description=README + "\n\n" + CHANGELOG,
    author='edX',
    author_email='oscm@edx.org',
    url='https://github.com/edx/taxonomy-connector',
    license='MIT',
    install_requires=REQUIREMENTS
)
