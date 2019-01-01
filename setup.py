import sys
# Remove current dir from sys.path, otherwise setuptools will peek up our
# module instead of system's.
sys.path.pop(0)
from setuptools import setup
sys.path.append("..")
import sdist_upip

setup(name='micropython-waze-route-calculator',
      version='1.0.0',
      description='Waze Route Calculator module for MicroPython',
      long_description='This is a Waze Route Calculator module for MicroPython.',
      url='https://github.com/sconaway/micropython-waze-route-calculator',
      author='Steven Conaway',
      author_email='sjconaway48@gmail.com',
      maintainer='Steven Conaway',
      maintainer_email='sjconaway48@gmail.com',
      license='GNU',
      cmdclass={'sdist': sdist_upip.sdist},
      py_modules=['micropython-waze-route-calculator'])
