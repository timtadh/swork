from distutils.core import setup

setup(name='swork',
      version='0.1',
      description=(
        'A shell enviroment manager. Allows you to easily manage the shell enviroment for'
        'working on various projects.'
      ),
      author='Tim Henderson',
      author_email='tim.tadh@gmail.com',
      url='https://www.github.com/timtadh/swork',
      license='GPLv2',
      packages=['sworklib'],
      scripts=['bin/swork'],
      platforms=['unix']
)
