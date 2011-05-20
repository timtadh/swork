from distutils.core import setup
import swork

setup(name='swork',
      version=str(swork.RELEASE),
      description=(
        'A shell enviroment manager. Allows you to easily manage the shell enviroment for'
        'working on various projects.'
      ),
      author='Tim Henderson',
      author_email='tim.tadh@gmail.com',
      url='https://www.github.com/timtadh/swork/tree/%s' % str(swork.RELEASE),
      license='GPLv2',
      packages=['sworklib'],
      scripts=['bin/swork'],
      py_modules=['swork'],
      platforms=['unix'],
      requires=['psutil']
)
