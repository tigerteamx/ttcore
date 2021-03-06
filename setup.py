import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()


setuptools.setup(
    name="ttcore",
    version="0.0.8",
    author="Martin F",
    author_email="pypi.org@tigerteamx.com",
    description="Django functionality to speedup development",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tigerteamx/ttcore",
    packages=setuptools.find_packages(),
    install_requires=[],  # Used for dependencies
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
