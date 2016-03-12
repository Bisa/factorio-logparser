try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'A Factorio log parser',
    'author': 'Tobias Wallin',
    'url': 'https://github.com/Bisa/factorio-logparser',
    'download_url': 'https://github.com/Bisa/factorio-logparser/releases',
    'author_email': 'bisa.wallin@gmail.com',
    'version': '2.0',
    'install_requires': ['nose'],
    'packages': ['flogparser'],
    'scripts': [],
    'name': 'Factorio LogParser'
}

setup(**config)
