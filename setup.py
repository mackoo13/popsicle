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
          'scikit-learn',
          'numpy'
      ],
      entry_points={
          'console_scripts': ['popsicle-download-lore = popsicle.download_lore:main',
                              'popsicle-transform-lore = popsicle.transform_lore:main',
                              'popsicle-transform-pips = popsicle.transform_pips:main',
                              'popsicle-transform-user-input = popsicle.transform_user_input:main',
                              'popsicle-params-lore = popsicle.params_lore:main',
                              'popsicle-train = popsicle.train:main',
                              'popsicle-predict-ml = popsicle.predict_ml:main',

                              'popsicle-exec = popsicle.fake_bash:exec',
                              'popsicle-predict = popsicle.fake_bash:predict']
      },
      scripts=['scripts/exec-time/popsicle-compile-time.sh',
               'scripts/exec-time/popsicle-init-time.sh',
               'scripts/exec-time/popsicle-exec-time.sh',
               'scripts/exec-gcc/popsicle-compile-gcc.sh',
               'scripts/exec-gcc/popsicle-init-gcc.sh',
               'scripts/exec-gcc/popsicle-exec-gcc.sh',
               'scripts/exec-unroll/popsicle-compile-unroll.sh',
               'scripts/exec-unroll/popsicle-init-unroll.sh',
               'scripts/exec-unroll/popsicle-exec-unroll.sh',
               'scripts/exec/popsicle-exec.sh',
               'scripts/papi/papi-events.sh',
               'scripts/ml/popsicle-predict.sh'],
      zip_safe=False)
