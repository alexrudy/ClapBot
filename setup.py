from setuptools import setup

setup(
    name='clapbot',
    packages=['clapbot'],
    url='https://github.com/alexrudy/clapbot',
    author='Alex Rudy',
    author_email='alex@alexrudy.org',
    include_package_data=True,
    install_requires=[
        'flask',
    ],
)