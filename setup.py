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
          'console_scripts': ['wombat-download-lore = lore.download_lore:main',
                              'wombat-transform-lore = lore.transform_lore:main',
                              'wombat-transform-lore-unroll = lore.transform_lore_unroll:main',
                              'wombat-transform-pips = lore.transform_pips:main',
                              'wombat-params-lore = lore.params_lore:main',
                              'wombat-params-lore-unroll = lore.params_lore_unroll:main',
                              'wombat-train = lore.train:main',
                              'wombat-predict = lore.precict:main']
      },
      zip_safe=False)
