from setuptools import setup

setup(name='popsicle',
      version='0.1',
      description='A framework for prediction of program speedup after code optimisation.',
      url='http://github.com/mackoo13/popsicle',
      author='Maciej Kocot',
      author_email='mkocot@op.pl',
      license='MIT',
      packages=['popsicle', 'popsicle.code_transform_utils', 'popsicle.ml_utils'],
      install_requires=[
          'pandas',
          'pycparser',
          'scipy',
          'sklearn',
          'numpy'
      ],
      entry_points={
          'console_scripts': ['popsicle-download-lore = popsicle.download_lore:main',
                              'popsicle-transform-lore = popsicle.transform_lore:main',
                              'popsicle-transform-lore-unroll = popsicle.transform_lore_unroll:main',
                              'popsicle-transform-pips = popsicle.transform_pips:main',
                              'popsicle-params-lore = popsicle.params_lore:main',
                              'popsicle-train = popsicle.train:main',
                              'popsicle-predict = popsicle.predict:main']
      },
      scripts=['scripts/exec-time/popsicle-exec-time.sh',
               'scripts/exec-gcc/popsicle-exec-gcc.sh',
               'scripts/exec-unroll/popsicle-exec-unroll.sh',
               'scripts/ml/popsicle-predict.sh'],
      zip_safe=False)
