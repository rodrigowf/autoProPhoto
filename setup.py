# Esse arquivo nã foi usado nem testado ainda!

from setuptools import find_packages, setup

setup(
    name='refoto',
    version='1.0.0',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'Flask',
        'requests',
        'Flask-Cors',
        'Flask-Session',
        'python-memcached',
        'google-api-python-client',
        'google-auth-oauthlib',
        'numpy',
        'opencv-python',
        'scikit-image',
        'tensorflow',
        'Keras',
        'torch',
        'torchvision',
        'colorama',
        'pillow>=3.2.0',
        'Theano',
        'git+https://github.com/Lasagne/Lasagne.git@61b1ad1#egg=Lasagne==0.2-dev,',
    ],
)