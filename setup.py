import setuptools
import pymongo

with open("README.md", "r") as f:
    long_description = f.read()

setuptools.setup(
    name="mongobase",
    version="0.3.0a0",
    author="Kazuki Otsuka",
    author_email="otsuka.kazuki@googlemail.com",
    description="A lightweight Pythonic OR Mapper for MongoDB.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kazukiotsuka/mongobase",
    license="MIT",
    keywords=["mongodb", "mongo", "pymongo", "orm", "or mapper"],
    packages=setuptools.find_packages(),
    install_requires=["pymongo>=3.6.0"],
    python_requires='~=3.6',
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.7",
        "Intended Audience :: Developers",
        "Topic :: Database :: Front-Ends",
        "Topic :: Software Development :: Libraries"
    ],
)