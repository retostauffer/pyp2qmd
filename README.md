
# Quarto Documentation for Python Packages

Small Python script to convert Python Google-Style docstrings to
[quarto](https://quarto.org) files to be used to render a Python package documentation
using a [quarto website](https://quarto.org/docs/websites/). This script
started as the author was not happy with existing software to document Python
packages, namely [sphinx](https://sphinx-doc.org) altough having a variety of features.

As sphinx has been used previously, this parser partially relies on the 
sphinx syntax for cross-referencing classes, functions, and methods.

### Under the hood

Uses the Python standard libraries `importlib` to import all visible classes
and functions of an existing package and `inspect` to inspect these objects.
The Python package
[`docstring_parser`](https://pypi.org/project/docstring_parser/) is used to
parse Google style docstrings which are then converted into quarto `.qmd`
files.

### Usage

In the simplest case:

```
python3 makedocs.py <action> -p <package>
```

... where `<action>` can be `init` or `document`. `init` will initialize a new
project and stores all necessary files in a directory `_quarto`. If initialized
once, an error will be thrown if executed again to avoid overwriting changes
made by the user. The argument `--overwrite` can be used to force-overwrite
the existing quarto files as well as `_quarto.yml`. `document` will only update
the man pages created from the Python docstrings as well as update the
'Function references' and 'Class references' section in the `_quarto.yml` file.

Additional options are available to change a few things. For more details see:

```
python3 makedocs.py --help
```

### Cross referencing

Based on the syntax of sphinx, cross-referencing in the docstrings is done
via `:py:class:`, `:py:func:` and `:py:meth:` followed by the name/path of the
class, function, or method.

* `:py:class:\`package.module.class\`` references a class
* `:py:class:\`class <package.module.class>\`` references a class but will
    only display `class` (custom text) in the rendered quarto document.
* `:py:class\`class\`` expects the class to be in the same module as the
    class it is references from.

Similarely functions can be cross-referenced with the same system:

* `:py:func:\`package.module.function\`` references a func
* `:py:func:\`function <package.module.function>\`` references a func but will
    only display `function` (custom text) in the rendered quarto document.
* `:py:func\`function\`` expects the func to be in the same module as the
    func it is references from.

Last but not least, sibling methods can be referenced within a class using:

* `:py:meth:\`method\``

The script does not validate if these references are valid, but will link to them
in the quarto documents. `quarto render` will throw warnings if links cannot be
resolved.


### Examples

One additional feature is a special comment in the Example section of each
Google style docstring. Whenver a line (code line) starts with `#:`, the example
will be split at this point, resulting in multiple quarto code chunks allowing
for 'in-line' (in-between chunks) output in the exercises. A line solely containing
`#:` also initiales a new code chunk but will not be shown (hidden chunk splitter).
As an example, this could look as follows in the docstring:

```
    Example:

    >>> # Basic addition
    >>> a = 10 + 3
    >>> a
    >>> #: Basic subtraction
    >>> 20 - 4
    >>> #:
    >>> 20 - 5
```






