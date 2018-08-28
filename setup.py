from setuptools import setup

setup(name='lore',
      version='0.1',
      description='...',
      url='http://github.com/mackoo13/wombat',
      author='...',
      author_email='...',
      license='MIT',
      packages=['lore'],
      install_requires=[
          'pandas',
          'pycparser',
          'scipy',
          'sklearn',
          'numpy'
      ],
      entry_points={
          'console_scripts': ['wombat-proc = lore.proc:main',
                              'wombat-params = lore.params:main',
                              'wombat-train = lore.train:main',
                              'wombat-predict = lore.precict:main']
      },
      zip_safe=False)
