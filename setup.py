from setuptools import setup

setup(name='wombat',
      version='0.1',
      description='A framework to construct a machine learning model predicting the benefit of code optimisation.',
      url='http://github.com/mackoo13/wombat',
      author='Maciej Kocot',
      author_email='mkocot@op.pl',
      license='MIT',
      packages=['wombat'],
      install_requires=[
          'pandas',
          'pycparser',
          'scipy',
          'sklearn',
          'numpy'
      ],
      entry_points={
          'console_scripts': ['wombat-download-lore = wombat.download_lore:main',
                              'wombat-transform-lore = wombat.transform_lore:main',
                              'wombat-transform-lore-unroll = wombat.transform_lore_unroll:main',
                              'wombat-transform-pips = wombat.transform_pips:main',
                              'wombat-params-lore = wombat.params_lore:main',
                              'wombat-params-lore-unroll = wombat.params_lore_unroll:main',
                              'wombat-train = wombat.train:main',
                              'wombat-predict = wombat.predict:main']
      },
      zip_safe=False)
