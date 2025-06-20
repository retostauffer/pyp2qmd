# -------------------------------------------------------------------
# `setup.py` for the small packages "python package to quarto
# documentation" package.
# -------------------------------------------------------------------

from setuptools import setup, find_namespace_packages

ISRELEASED  = False
VERSION     = "0.1.2"

setup(
    name         = "pyp2qmd",
    version      = VERSION,
    author       = "Reto Stauffer",
    author_email = "reto.stauffer@uibk.ac.at",
    description  = "Parses docstrings of all exported classes and methods of a python package and turns them into quarto markdown (qmd) files. Alongside, a basic structure for a quarto website is created, intended to easily document your python package with quarto.",
    long_description = open("README.md").read(),
    long_description_content_type = "text/markdown",
    url = "https://github.com/retostauffer/pyp2qmd",
    project_urls = {
        "GitHub Issues": "https://github.com/retostauffer/pyp2qmd/issues"
    },
    license = "GNU General Public License v2.0 or later",
    classifiers = [
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent"
    ],
    install_requires     = ["docstring_parser", "pyyaml"],
    packages             = find_namespace_packages("src"),
    package_dir          = {"": "src"},
    python_requires      = ">=3.8",
    zip_safe             = False,

    # Static files (templates)
    include_package_data = True,
    package_data = {"pyp2qmd": ["templates/*"]},

    # Executables
    entry_points = {
        "console_scripts": [
            "pyp2qmd = pyp2qmd.bin.pyp2qmd:main"
        ]
    }

)
