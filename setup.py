import pathlib
from setuptools import setup

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# This call to setup() does all the work
setup(
    name="mongobase",
    version="1.0.0",
    description="A lightweight MongoDB OR mapper.",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/kazukiotsuka/mongobase",
    author="Kazuki Otsuka",
    author_email="otsuka.kazuki@googlemail.com",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
    ],
    packages=["mongobase"],
    include_package_data=True,
    install_requires=["pymongo", "mecab-python3", "jaconv", ""],
    entry_points={
    },
)