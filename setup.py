"""A setuptools based setup module.
See:
https://packaging.python.org/guides/distributing-packages-using-setuptools/
https://github.com/pypa/sampleproject
Modified by Madoshakalaka@Github (dependency links added)
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
from os import path

# io.open is needed for projects that support Python 2.7
# It ensures open() defaults to text mode with universal newlines,
# and accepts an argument to specify the text encoding
# Python 3 only projects can skip this import
from io import open

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()


setup(
    name="graph-wrap",
    version="0.0.1",
    description="Transform a tastypie REST-based API into a fully compliant GraphQL API.",
    long_description=long_description,  # Optional
    long_description_content_type="text/markdown",
    url="https://github.com/PaulGilmartin/graph_wrap",
    author="Paul Gilmartin",
    author_email="paul.gilmartin89@gmail.com",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    keywords="tastypie graphene django graphql rest api",
    packages=find_packages(),
    python_requires=">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*, <4",
    # For an analysis of "install_requires" vs pip's requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=[
        "Django>=1.11",
        "django-tastypie==0.14.3",
        "graphene>=2.1.7,<3",
        "graphene-django==2.9.0",
        "graphql-core>=2.1.0,<3",
        "graphql-relay==2.0.1",
        "promise>=2.1",
        "python-dateutil==2.8.1",
        "python-mimeparse==1.6.0",
        "pytz==2019.3",
    ],
    project_urls={
        "Source": "https://github.com/PaulGilmartin/graph_wrap",
    },
)
