import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="ttcore",
    version="0.0.5",
    author="Martin F",
    author_email="pypi.org@tigerteamx.com",
    description="Django functionality to speedup development",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tigerteamx/ttcore",
    packages=setuptools.find_packages(),
    install_requires=['Django >= 2.0',
                      "django-cron==0.5.1"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
