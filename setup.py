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
          'scipy',
          'sklearn',
      ],
      entry_points={
          'console_scripts': ['lore-proc = lore.lore_proc:main',
                              'lore-train = lore.lore_train:main',
                              'lore-predict = lore.lore_precict:main']
      },
      zip_safe=False)
