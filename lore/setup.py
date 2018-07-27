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
          'sklearn',
      ],
      entry_points={
          'console_scripts': ['lore-train = lore.lore_train:main']
      },
      zip_safe=False)
