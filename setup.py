try:
    from setuptools import setup
    setup  # quiet "redefinition of unused ..." warning from pyflakes
    # arguments that distutils doesn't understand
    setuptools_kwargs = {
        'install_requires': [
            'psutil',
            'optutils>=0.3',
        ],
        'provides': ['swork'],
        'zip_safe': True
        }
except ImportError:
    from distutils.core import setup
    setuptools_kwargs = {}

import swork_version


setup(name='swork',
      version=str(swork_version.RELEASE),
      description=(
        'A shell enviroment manager. Allows you to easily manage the shell enviroment for'
        'working on various projects.'
      ),
      author='Tim Henderson',
      author_email='tim.tadh@gmail.com',
      url='https://www.github.com/timtadh/swork/tree/%s' % str(swork_version.RELEASE),
      license='GPLv2',
      packages=['sworklib'],
      scripts=['bin/swork'],
      py_modules=['swork', 'swork_version'],
      platforms=['unix'],
      **setuptools_kwargs
)
