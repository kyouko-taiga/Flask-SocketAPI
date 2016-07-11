"""
Flask-SocketAPI
--------------
Lightweight library to create streaming APIs over Flask-SocketIO.
"""

from setuptools import setup


setup(
    name='Flask-SocketAPI',
    version='0.2',
    url='https://github.com/kyouko-taiga/Flask-SocketAPI',
    license='MIT',
    author='Dimitri Racordon',
    author_email = "kyouko.taiga@gmail.com",
    description='Lightweight library to create streaming APIs over Flask-SocketIO',
    long_description=__doc__,
    packages=['flask_socketapi'],
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=[
        'flask-socketio>=2.5'
    ],
    tests_require=[
        'coverage'
    ],
    test_suite='test_socketapi',
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3'
    ]
)