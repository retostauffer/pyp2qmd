
class Config:
    """pyp2qmd Configuration

    Custom class for handling the required arguments for pyp2qmd which
    has two modes: If `argparse = False` (default) on initialization, the
    user must use the :py:meth:`setup` method to specify the required
    arguments.

    If `argparse = True` user inputs will be parsed via the `argparse` package
    and automatically handed over to the :py:meth:`setup` method. This is used
    when called via console (console arguments).

    Args:
        argparse (bool): `False` by default, the user has to use the `.setup()` method.
            If set to `True` it will try to parse input arguments via `argparse`.

    Return:
        Initializes an object of class `pyp2qmd.Configuration`.
    """

    def __init__(self, argparse = False):

        # Falls until .setup was executed such that we know
        # that the object has been set up properly one way
        # or the other.
        self._is_set_up = False

        # Parse user input args
        if argparse: self.__parse_arguments()

    def __parse_arguments(self):

        # Allowed action options
        allowed_action = ["init", "document", "examples"]

        import argparse
        import sys
        from re import search

        pkg_name = search(r"^(.*?)(?=\.)", self.__module__).group(1)
        parser = argparse.ArgumentParser(pkg_name)
        parser.add_argument("action", nargs = 1, type = str,
                help = f"Action to perform, one of: {', '.join(allowed_action)}")
        parser.add_argument("-p", "--package", type = str,
                help = "Name of the python package.")
        parser.add_argument("--overwrite", default = False, action = "store_true",
                help = "Only used if action = create; will overwrite _quarto.yml if needed.")
        parser.add_argument("--quarto_dir", type = str, default = "_quarto",
                help = "Name of the target directory for rendered quarto website. " + \
                       "Defaults to \"_quarto\".")
        parser.add_argument("--man_dir", type = str, default = "man",
                help = "Folder to store the function/class manual qmds (subfolder of quarto_dir). " + \
                       "Defaults to \"man\".")
        parser.add_argument("--output_dir", type = str, default = "_site",
                help = "Name of the target directory for rendered quarto website," + \
                       "relative to quarto_dir. Defaults to \"_site\".")
        parser.add_argument("--docstringstyle", type = str, default = "GOOGLE",
                help = "Docstring type (format). Defaults to \"GOOGLE\".")
        parser.add_argument("--include_hidden", default = False, action = "store_true",
                help = "If set, hidden functions and methods will also be documented " + \
                        "(functions/methods starting with _ or __).")
        parser.add_argument("--examples_dir", type = str, default = "_examples",
                help = "Name of the target directory for docstring examples (qmds). " + \
                       "Only used if action is 'examples', defaults to \"_examples\".")
        parser.add_argument("--silent", default = False, action = "store_true",
                help = "If set, output will be suppressed.")

        # Parsing input args
        args = parser.parse_args()

        args.action = args.action[0]
        if not args.action in allowed_action:
            parser.print_help()
            sys.exit("\nUsage error: invalid \"action\" (see help).")

        if args.package is None:
            parser.print_help()
            sys.exit("\nUsage error: argument -p/--package must be set.")

        ymlfile = f"{args.quarto_dir}/_quarto.yml"
        if args.action == "create" and isfile(ymlfile):
            parser.print_help()
            sys.exit(f"\nUsage error: action is set to \"{args.action}\" " + \
                     f"but the file \"{ymlfile}\" " + \
                     f"already exists. Remove folder \"{args.quarto_dir}\" or use " + \
                     f"--overwrite; be aware, will overwrite the existing \"{ymlfile}\".")


        self.setup(**vars(args))


    def setup(self, action, package,
              quarto_dir = "_quarto", man_dir = "man", output_dir = "_site",
              overwrite = False, include_hidden = False, examples_dir = "_examples",
              docstringstyle = "GOOGLE", silent = False):
        """Config Setup

        `action = "init"` initializes the auto-generated documentation and will
        automatically create the quarto website template including a
        `_quarto.yml` file and `pyp.sass`. Will thorw an exception one of these
        files already exists, except if the user allows for `overwrite = True`
        (take care, the current content of `_quarto.yml` will be overwritten).

        `action = "document"` parses the python package classes and functions
        and will update the man pages. It will, however, not overwrite
        `_quarto.yml`. When used the first time, it will also initialize the
        output folder structure and create the required files (`_quarto.yml`,
        `pyp.sass`) similar to the init action.

        Args:
            action (str): Action to be executed. One of `"init"` or `"document"`,
                see method description.
            package (str): Name of the package which should be documented.
            quarto_dir (str): Output directory, defaults to `"_quarto"`.
            man_dir (str): Name of the directory for the manual pages (subfolder
                inside `quarto_dir`), defaults to `"man"`.
            output_dir (str): Directory for the rendered quarto website, used
                as `output-dir` target in `_quarto.yml`, relative to
                `quarto_dir`. Defaults to `"_site"`.
            overwrite (bool): Only used if `action = "init"`, see method
                description.
            include_hidden (bool): If `False` (default), classes, functions, and
                methods starting with an underscore will not be documented
                (no quarto man pages will be crated). Dunder classes, functions, and
                methods are always excluded.
            docstringstyle (str): Style of the docstrings in the package, must be one
                of the allowed types of the `docstring_parser` package
                (AUTO, EPYDOC, GOOGLE, NUMPYDOC, REST), defaults to `"GOOGLE"`;
                not case sensitive.
            silent (bool): If `False` (default) some output will be produced
                when rendering the man pages. Can be specified to silence the
                execution.

        Raises:
            TypeError: If the inputs are not of the expected type.
            ValueError: If `action` is not one of the allowed ones.
        """

        # Store input arguments as object attributes
        for key,val in locals().items():
            if key in ["self", "kwargs"]: continue
            setattr(self, f"_{key}", val)

        # --------------------------------------------
        # Now checking validity of all required args
        # --------------------------------------------
        action_allowed = ["init", "document", "examples"]
        if not isinstance(self.get("action"), str):
            raise TypeError("argument `action` must be str")
        elif not self.get("action") in action_allowed:
            raise ValueError(f"action must be one of: {', '.join(action_allowed)}")

        if not isinstance(self.get("package"), str):
            raise TypeError("argument `package` must be str")

        if not isinstance(self.get("quarto_dir"), str):
            raise TypeError("argument `quarto_dir` must be str")
        if not isinstance(self.get("man_dir"), str):
            raise TypeError("argument `man_dir` must be str")
        if not isinstance(self.get("output_dir"), str):
            raise TypeError("argument `output_dir` must be str")

        if not isinstance(self.get("overwrite"), bool):
            raise TypeError("argument `overwrite` must be bool")
        if not isinstance(self.get("include_hidden"), bool):
            raise TypeError("argument `include_hidden` must be bool")

        if not isinstance(self.get("docstringstyle"), str):
            raise TypeError("argument `docstringstyle` must be str")

        if not isinstance(self.get("silent"), bool):
            raise TypeError("argument `silent` must be bool")

        self._is_set_up = True


    def get(self, what):
        """Get Attribute

        Allows to access attributes from the object. `get("foo")`
        will try to return `self._foo` if it exists.

        Args:
            what (str): Name of the attribute (without leading underscore).

        Returns:
            Whatever is stored on the attribute.

        Raises:
            TypeError: If argument `what` is not str.
            ValueError: If the argument `_{what}` does not exist.
        """
        if not isinstance(what, str):
            raise TypeError("argument `what` must be str")
        if not hasattr(self, f"_{what}"):
            raise ValueError(f"object has no attribute \"_{what}\"")
        return getattr(self, f"_{what}")


    def is_set_up(self):
        """Object Set Up Properly?

        Returns:
            bool: Returns `True` if the object has been set up properly
            (see main class description) and `False` otherwise.
        """
        return self._is_set_up

    def __repr__(self):
        """Standard Representation

        Returns:
            str: Standard representation of the class.
        """
        if not self.is_set_up():
            return f"{self.__module__} Object not yet set up, call .setup() first."
        else:
            res  = f"{self.__module__} Object:\n"
            res += f"    Action:            {self.get('action')}\n"
            res += f"    Package:           {self.get('package')}\n"
            res += f"    Quarto dir:        {self.get('quarto_dir')}\n"
            res += f"    Man page dir:      {self.get('man_dir')}\n"
            res += f"    Output dir:        {self.get('output_dir')}\n"
            res += f"    Overwrite:         {self.get('overwrite')}\n"
            res += f"    Examples dir:      {self.get('examples_dir')}\n"
            res += f"    Include hidden:    {self.get('include_hidden')}\n"
            res += f"    Docstring style:   {self.get('docstringstyle')}\n"
            return res



