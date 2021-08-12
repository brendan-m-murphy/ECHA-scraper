from setuptools import find_packages, setup

setup(
    name='src',
    packages=find_packages(),
    version='0.1.0',
    description='Scraping the European Chemicals Agency's website to find all substances only used in cosmetics, and for these substances, what is their regulatory and testing status.',
    author='Brendan Murphy',
    license='MIT',
)
