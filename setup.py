from setuptools import setup, find_packages


setup(
    name = 'dash-access',
    version = '0.3',
    description = 'Granular access control for Dash',
    long_description = 'A simple, granular access control system for Dash, with object-oriented or API-based approaces',
    keywords = 'dash callbacks plotly access authorization authentication flask python flask-login python3 user-access',
    url = 'https://github.com/russellromney/dash-access',
    download_url = 'https://github.com/russellromney/dash-access/archive/v0.1.tar.gz',
    author = 'Russell Romney',
    author_email = 'russellromney@gmail.com',
    license = 'MIT',
    packages = find_packages(),
    install_requires = [
        'Flask-Login=0.5.0'
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    include_package_data = False,
    zip_safe = False
)
