from distutils.core import setup
setup(
  name = 'Pyrex',
  packages = ['Pyrex'],
  version = '0.1',
  license='GPL-3.0-or-later',
  description = 'Automatically generate a requirements file for the pip package manager from your codebase.',
  author = 'Lionell Loh',
  author_email = 'your.email@domain.com',
  url = 'https://github.com/lionellloh/pyrex',
  download_url = 'https://github.com/lionellloh/pyrex/archive/v_01.tar.gz',
  keywords = ['auto-generate requirements', 'requirements', 'generate', 'auto-generate'],
  install_requires=[
          'piptools',
          'stdlib-list',
          'wcmatch'
      ],
  classifiers=[
    'Development Status :: 3 - Alpha',
    'Intended Audience :: Developers',
    'Topic :: Software Development :: Build Tools',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Python :: 3.9',
  ],
)