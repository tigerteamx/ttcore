import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()


with open("VERSION.txt", "r") as f:
    version = f.read().strip()


setuptools.setup(
    name="ttcore",
    version=version,
    author="Martin F",
    author_email="pypi.org@tigerteamx.com",
    description="Atomic Batteries Included. Used by https://tigerteamx.com to maximize producitivty.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tigerteamx/ttcore",
    packages=['ttcore'],
    package_data={
        'ttcore': [
            'docs.html',
            'admin.html',
        ]
    },
    install_requires=[],  # Used for dependencies
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        'console_scripts': ['ttcore = ttcore.cli:cli']
    },
    keywords=['productivity', 'bottlepy', 'peewee'],
    python_requires='>=3.8',
    include_package_data=True,
)
