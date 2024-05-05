#!/usr/bin/env python3
# -------------------------------------------------
# Building quarto manual pages for python package
# -------------------------------------------------


class DocConverter:
    """Documentation Converter

    This is the main class of the package which will extract the docstrings
    of all exported classes and functions of an installed python package,
    and convert them into quarto markdown files (thus pyp2qmd; python package to
    quarto markdown).

    The :py:class:`Config` contains all the required arguments/settings to perform
    this task and is, thus, the only reqired input argument.

    Args:
        config (Config): See :py:class:`Config` for details; must be
            set up properly.

    Return:
        Initializes a new object of class `DocConverter`.

    Raises:
        TypeError: If `config` is not of class :py:class:`Config`.
        Exception: If `config` object is not set up properly.
        Exception: If the package which should be documented is not found (can't
            be imported).
        ValueError: If package `docstring_parser` has no `DocstringStyle` class
            matching the docstringstyle defined by the user (handled as 'all upper case').
    """

    # bool: is used to later on modify _quarto.yml (adding function references
    # and class references).
    _quarto_yml_initialized = False

    # Created man pages will be stored here, used to populate _quarto.yml if needed
    _man_created = {"classes": dict(), "functions": dict(), "method": dict()}

    def __init__(self, config):
        from .Config import Config
        from importlib import import_module
        from docstring_parser import DocstringStyle
        if not isinstance(config, Config):
            raise TypeError("argument `config` must be of class pyp2qmd.Config")
        elif not config.is_set_up():
            raise Exception(f"issue with argument `config`: {config}")

        # Testing two more things. First we load the package which should be
        # documented. Throws an error if that package cannot be loaded (not
        # installed). Stores the package on _pkg, used by the methods to extract
        # classes and functions (e.g., get_classes, get_functions methods).
        try:
            self._pkg = import_module(config.get("package"))
        except Exception as e:
            raise Exception(f"Cannot document \"{config.get('package')}\". Reason: {e}.")

        # Next check if the docstringstyle is valid
        if not hasattr(DocstringStyle, config.get("docstringstyle").upper()):
            raise ValueError("invalid `docstringstyle`, package `docstring_parser` has no class " + \
                           f"`docstring_parser.DocstringStyle.{config.get('docstringstyle').upper()}`")

        # Store config
        self._config = config

        # Checking action: If action = "init" and overwrite = False we are
        # checking if some specific output files already exist. If so, raise
        # Exception and inform the user that he/she can enable overwrite,
        # however, this might result in loss of data (overwrites these files).
        from os.path import join, isfile
        files_to_check = [
                join(self.config_get("quarto_dir"), "_quarto.yml"),
                join(self.config_get("quarto_dir"), "pyp.scss"),
                join(self.config_get("quarto_dir"), "index.qmd")
            ]
        if self.config_get("action") == "init" and not self.config_get("overwrite"):
            tmp = []
            for f in files_to_check:
                if isfile(f): tmp.append(f)

            if len(tmp) > 0:
                pl  = "" if len(tmp) == 1 else "s"
                pl2 = "it" if len(tmp) == 1 else "them"
                tmp = ", ".join(f"\"{x}\"" for x in tmp)
                raise Exception(f"file{pl} {tmp} already exist{pl}, `action = \"init\"` " + \
                        f"would overwrite {pl2} with a template. Consider using " + \
                        "`action = \"document\"` or allow DocConverter to overwrite " + \
                        "the existing file using `overwrite = True` (`--overwrite` " + \
                        "via console). WARNING: May `action = \"init\"` with " + \
                        f"`overwrite = True` may result in loss of data if the file{pl} " + \
                        "mentioned have been edited manually!")

        # Proceed. If action == 'init' create template files
        if self.config_get("action") == "init":
            self.__init_documentation()
            self._quarto_yml_initialized = True 

        # Class is now ready to do what it is designed for

    def __init_documentation(self):

        from os import makedirs
        from os.path import join, isdir, basename
        from shutil import copy
        from re import sub, match
        
        # Trying to create quarto_dir and quarto_dir/man_dir if needed
        if not isdir(self.config_get("quarto_dir")):
            try:
                makedirs(self.config_get("quarto_dir"))
            except Exception as e:
                raise Exception(f"cannot create {self.config_get('quarto_dir')}: {e}")
        man_dir = join(self.config_get("quarto_dir"), self.config_get("man_dir"))
        if not isdir(man_dir):
            try:
                makedirs(man_dir)
            except Exception as e:
                raise Exception(f"cannot create {man_dir}: {e}")
         
        # Getting package name
        pkgname = match(r"^([^\.]+)", self.__class__.__module__).group(1)

        # Adding template(s)
        def pkg_file(pkgname, directory, file):
            from re import match
            from pkg_resources import resource_filename
            from os.path import isfile, join

            # Getting package name
            assert isinstance(pkgname, str), TypeError("argument `pkgname` must be str")
            assert isinstance(file, str), TypeError("argument `file` must be str")
            assert isinstance(directory, str), TypeError("argument `directory` must be str")

            # Getting name of file
            file = resource_filename(pkgname, join(directory, file))
            if not isfile(file):
                raise Exception(f"whoops, file \"{file}\" (intended to be shipped with " + \
                        "the package) does not exist; contact the mainainer")
            return file

        # Adding _quarto.yml
        src = pkg_file(pkgname, "templates", "_quarto.yml")
        content = open(src, "r").read()
        content = sub("<title>", pkgname, content)
        content = sub("<output_dir>", self.config_get("output_dir"), content)
        with open(join(self.config_get("quarto_dir"), basename(src)), "w") as fid:
            fid.write(content)
        del src, content

        # Adding index.qmd
        from datetime import datetime as dt
        src = pkg_file(pkgname, "templates", "index.qmd")
        content = open(src, "r").read()
        content = sub("<title>", pkgname, content)
        content = sub("<date_and_time>", f"{dt.now():%Y-%m-%d %H:%M}", content)
        with open(join(self.config_get("quarto_dir"), basename(src)), "w") as fid:
            fid.write(content)
        del src, content

        # Copy sass
        src = pkg_file(pkgname, "templates", "pyp.sass")
        copy(src, join(self.config_get("quarto_dir"), "pyp.sass"))




    def __repr__(self):
        """Standard Representation

        Standard representation of the DocConverter class,
        mainly for development purposes at the moment.

        Returns:
            str: String with standard representation.
        """
        res  = f"{self.__module__} Object:\n"

        cls = self.get_classes(names_only = True)
        if len(cls) > 0:
            res += f"{self.__nice_stdout_list_of_strings('    Classes:   ', cls)}"

        fun = self.get_functions(names_only = True)
        if len(fun) > 0:
            res += f"{self.__nice_stdout_list_of_strings('    Functions: ', fun)}"

        return res


    def __nice_stdout_list_of_strings(self, desc, x):
        from re import sub

        assert isinstance(desc, str), TypeError("argument `desc` must be str")
        assert isinstance(x, list),   TypeError("argument `x` must be str")
        assert all([isinstance(y, str) for y in x]), TypeError("elements in `x` must be str")

        res = [desc]
        for rec in x:
            tmp = res[len(res) - 1] + rec + ", "
            if len(tmp) < 80:
                res[len(res) - 1] = tmp
            else:
                res.append(" " * len(desc) + rec + ", ")
        return sub(",\s+$", "", "\n".join(res)) + "\n"


    def config_get(self, what):
        """Get Config Attribute

        Calls the `.get()` method of the :py:class:`Config` object
        as defined via `config` on class initialization. Will raise
        exceptions if not available (see :py:class:`Config` for details).

        Args:
            what (str): Attribute to be returned.

        Return:
            Whatever is stored on the `_{what}` attribute of the
            :py:class:`Config` object.
        """
        return self._config.get(what)


    def get_classes(self, names_only = False):
        """Get Exported Classes

        Args:
            names_only (bool): If `False` (default) a list of tuples is returned,
                if set `True` a list of str (name of classes only).

        Return:
            dict or list: Dictionary with all exported classes if `names_only = True`,
                else a list of str containing only the class names.

        Raises:
            Exception: If there are issues extracting classes via `inspect`.
        """
        from inspect import getmembers, isclass
        try:
            res = getmembers(self._pkg, isclass)
        except Exception as e:
            raise Exception(f"problems extracting classes from package: {e}")

        if not names_only:
            return dict(zip([x[0] for x in res], [x[1] for x in res]))
        else:
            return [x[0] for x in res]

    def get_functions(self, names_only = False):
        """Get Exported Functions

        Args:
            names_only (bool): If `False` (default) a list of tuples is returned,
                if set `True` a list of str (name of classes only).

        Return:
            dict or list: Dictionary with all exported functions if `names_only = True`,
                else a list of str containing only the function names.

        Raises:
            Exception: If there are issues extracting functions via `inspect`.
        """
        from inspect import getmembers, isfunction
        try:
            res = getmembers(self._pkg, isfunction)
        except Exception as e:
            raise Exception(f"problems extracting classes from package: {e}")

        if not names_only:
            return dict(zip([x[0] for x in res], [x[1] for x in res]))
        else:
            return [x[0] for x in res]

    
    def document_classes(self):
        """Document Classes

        Generates man pages for all exported classes.
        """
        from .ManPage import ManPage

        for name,cls in self.get_classes().items():
            print(f"[DEVEL] Create man page for {name}")
            man = ManPage(name, cls, self._config)

            self._man_created["classes"][name] = man.write_qmd()

        import sys; sys.exit(3)

#def create_quarto_yml(args):
#    """
#
#    Returns:
#    bool: Returns `True` if the yml file is created the first time
#    by calling this function, else `False` (file did already exist).
#    """
#    import os
#    ymlfile = f"{args.quarto_dir}/_quarto.yml"
#
#    if args.action == "init":
#        res = True
#        # If yml already exists and overwrite = False, error
#        if os.path.isfile(ymlfile) and not args.overwrite:
#            raise Exception(f"action = {args.action}, overwrite = {args.overwrite} " + \
#                    f"but file \"{ymlfile}\" already exists; stop!")
#
#        # If output directory does not yet exist, create.
#        if not os.path.isdir(args.quarto_dir):
#            try:
#                os.makedirs(args.quarto_dir)
#            except:
#                raise Exception(f"Unable to create output folder \"{args.quarto_dir}\"")
#
#        # Content of the yml file
#        content = {"project": {"type": "website"},
#                     "website": {"title": args.package,
#                        "navbar": {"search": True,
#                            "right": [{"icon": "github", "href": "https://github.com/dummy/entry", "aria-label": "gsdata GitHub"}]},
#                        "sidebar": {"collapse-level": 1,
#                           "contents": [{"text": "Home", "file": "index.qmd"}]
#                        }
#                     },
#                     "format": {"html": {"theme": ["quarto", "pyp.scss"]}},
#                     "execute": {"cache": True, "freeze": "auto"}
#                   }
#
#        # Else create (overwrite) the file
#        with open(ymlfile, "w+") as fid: fid.write(yaml.dump(content))
#
#    # Else (not init): Ensure the output folder and the yml file exists, else
#    # init must be used.
#    else:
#        res = False
#        if not os.path.isdir(args.quarto_dir):
#            raise Exception(f"Output folder \"{args.quarto_dir}\" does not exist. " + \
#                    "You may first need to call the script with action = init")
#        elif not os.path.isfile(ymlfile):
#            raise Exception(f"yml file \"{ymlfile}\" does not exist. " + \
#                    "You may first need to call the script with action = init")
#
#    # Create references dir if not existing
#    refdir = os.path.join(args.quarto_dir, args.man_dir)
#    if not os.path.isdir(refdir):
#        try:
#            os.makedirs(refdir)
#        except Exception as e:
#            raise Exception(e)
#
#    return res
#
#def write_index(args):
#    """
#    Write index
#
#    Returns:
#    bool : True if index was newly created, else False.
#    """
#    import os
#    import re
#    from datetime import datetime as dt
#    qmdfile = f"{args.quarto_dir}/index.qmd"
#    res = False
#    if not os.path.isfile(qmdfile):
#        res = True
#        # Sorry, indent is important
#        content = f"""
#        # {args.package} Package Documentation
#
#        This page has been automatically generated by
#        pyp2qmd (Python package documentation to quarto),
#        converting the docstrings of all loaded functions
#        and methods available via `{args.package}.*` into
#        quarto markdown files (`.qmd`).
#
#        ### Function reference
#
#        Contains the documentation/reference of all functions,
#        including description, usage, arguments, exceptions,
#        as well as evaluated examples.
#
#        ### Class reference
#
#        The documentation/reference of all classes including
#        description, usge, arguments, _methods_, exceptions,
#        and evaluated examples (if any).
#
#        For each method listed on the class reference page,
#        a quarto markdown file is generated as well, altough
#        not listed in the navigation. The documentation can
#        be accessed by visiting the class reference, and then
#        click on the method of interest.
#        
#        _Generated: {dt.now() : %Y-%m-%d %H:%M}_.
#        """
#
#        # There is for sure a single nice regex instead of
#        # this approach (currently the regex kills empty lines).
#        content = re.sub(r"^(?!\s*$)\s+", "", content, flags = re.MULTILINE)
#        with open(qmdfile, "w+") as fid: fid.write(content)
#
#    return res
#
#
#def write_sass(args):
#    """
#    Write sass
#
#    Returns:
#    bool : True sass file was created/replaced, else False.
#    """
#    import os
#    scssfile = f"{args.quarto_dir}/pyp.scss"
#    res = False
#    if not os.path.isfile(scssfile) or args.action == "init":
#        res = True
#        # Sorry, indent is important
#        content = """
#/*-- scss:defaults --*/
#// Base document colors
#$body-bg: white;
#$body-color: black;
#$primary: #0d6efd;
#$link-color: #4287f5;
#
#/*-- scss:custom --*/
#
#// pre code styling
#pre {
#    code {
#        padding: 0.25rem 0.75rem;
#        &.language-python {  
#            white-space: pre;
#            font-family: monospace;
#            vertical-align: top;
#            color: $primary; 
#            font-weight: 500;
#        }
#    }
#}
#
#
#// Styling of the <dl> lists
#dl.pyp-list {
#    dt {
#        code {
#            &.argument-class {
#                color: gray;
#                margin-left: 0.5em;
#                font-weight: 500;
#            }
#        }
#    }
#    dd {
#        margin-left: 2em;
#    }
#}
#
#
#// sourceCode cells
#div {
#    &.sourceCode {
#        background-color: rgba(233,236,239,.95) !important;
#        border: 1px solid rgba(233,236,239,.95) !important;
#        margin: 0.25rem 0;
#    }
#}
#
#// Output cells; identical style for .cell-output-display and .cell-output-stdout
#div.cell-output-display, div.cell-output-stdout {
#    margin: 1rem 0;
#    pre {
#        background-color: rgba(233,236,239,.55);
#        border: 1px solid rgba(233,236,239,.55);
#        padding: 0.125rem 0.25rem;
#    }
#}
#
#// Styling raises section (exception documentation)
#ul.python-raises {
#    list-style: none;
#    padding-left: 0;
#    code {
#        font-family: monospace;
#        font-weight: 500;
#    }
#}
#        """
#        with open(scssfile, "w+") as fid: fid.write(content)
#
#    return res
#
#def update_quarto_yml(args, section, mans):
#
#    import yaml
#
#    assert isinstance(section, str)
#    assert isinstance(mans, dict)
#    assert all([isinstance(x, str) for x in mans])
#    ymlfile = f"{args.quarto_dir}/_quarto.yml"
#
#    # Read existing 
#    with open(ymlfile, "r") as fid:
#        content = yaml.load("".join(fid.readlines()), yaml.SafeLoader)
#
#    # Dictionary to extend the content
#    tmp = []
#    for key,val in mans.items():
#        tmp.append({"text": key, "file": val})
#    tmp = {"section": section, "contents": tmp}
#
#    # Append and overwrite _quarto.yml with new content
#    content["website"]["sidebar"]["contents"].append(tmp)
#    with open(ymlfile, "w+") as fid: fid.write(yaml.dump(content))
#
#def extract_docstring(obj, style, include_hidden):
#    dstyle = getattr(docstring_parser.DocstringStyle, style.upper())
#
#    # If parent is None, extract docstring of main function or class.
#    class_docstring = docstring_parser.parse(inspect.getdoc(obj), dstyle)
#    if class_docstring:
#        res = [class_docstring, inspect.signature(obj), obj.__module__]
#    else:
#        res = [None, None, None]
#
#    return res
#
#    ## If parent is a class object we extractt he members of that object,
#    ## i.e., the methods of a class. Only meaningful for classes, obviously.
#    #else:
#    #    # Extract method/function docstrings
#    #    for name,func in get_members(obj).items():
#
#    #        name = re.search(r"[^.]+$", name).group(0)
#    #        if not include_hidden and name.startswith("_"): continue
#
#    #        # Else check if is function
#    #        if inspect.isfunction(func):
#    #            try:
#    #                doc = docstring_parser.parse(inspect.getdoc(func), dstyle)
#    #            except Exception as e:
#    #                print(f"Problem extracting docstring from:   {func.__name__} ({name})")
#    #                raise Exception(e)
#
#    #            # Setting up the displayed name for the manuals; a combination
#    #            # of the parent `obj` and the visible name of the function.
#    #            fn_name = ".".join([parent.fullname(), func.__name__])
#
#    #            fn_module = re.sub(f"^{package}\.", "", obj.__module__)
#    #            docstrings[fn_name] = {"docstring": doc,
#    #                                   "signature": inspect.signature(func),
#    #                                   "module":    ".".join([func.__module__, obj.__name__])}
#
#    #            # For this function (method) we'll also write 
#    #            # a qmd page, tough it will not be added/included
#    #            # in the navigation.
#    #            fn_man = py2quarto(func, package, args.include_hidden)
#    #            print(f"[DEVEL]     - adding man page for method {fn_man.fullname()}")
#    #            fn_qmdfile = os.path.join(args.quarto_dir, args.man_dir,
#    #                                      f"{fn_name}.qmd")
#    #                                      #f"{fn_fullname()}.qmd")
#    #            print(f"              {fn_qmdfile}")
#    #            with open(fn_qmdfile, "w+") as fid: print(fn_man, file = fid)
#
#    #return docstrings
#
#class manPage:
#    def __init__(self, name, obj, args, parent = None):
#        # parent (None, str): If str, this will be removed from full name.
#        if not isinstance(name, str):
#            raise TypeError("argument `name` must be str")
#        if not inspect.isfunction(obj) and not inspect.isclass(obj):
#            raise TypeError("argument `obj` must be function or class")
#        if not isinstance(parent, type(None)) and not isinstance(parent, str):
#            raise TypeError("argument `parent` must be None or str")
#
#        self._name           = name
#        self._obj            = obj
#        self._parent         = parent
#        self._args           = args
#
#        self._doc, self._signature, self._module = \
#                extract_docstring(obj, args.docstringstyle, args.include_hidden)
#
#    def fullname(self):
#        if re.match(f"^{self._module}", self._name):
#            return self._name
#        else:
#            return f"{self._module}.{self._name}"
#
#    def quartofile(self):
#        return f"{self.fullname()}.qmd"
#
#    def isclass(self):
#        return inspect.isclass(self._obj)
#
#    def isfunction(self):
#        return inspect.isfunction(self._obj)
#
#    def _format_signature(self, name, max_length = 200, remove_self = False):
#        """
#        formatting of signature to get some line breaks in output
#        """
#
#        n = max_length - len(name) - 1
#        formatted_params = []
#        tmp = []
#
#        for k,p in self._signature.parameters.items():
#            if remove_self and k == "self": continue
#            tmp_len = max(0, sum([len(x) for x in tmp]) + (len(tmp) - 1) * 2)
#            if (tmp_len + len(str(p)) + 1) <= n:
#                tmp.append(str(p))
#            else:
#                formatted_params.append(", ".join(tmp))  
#                tmp = [str(p)]
#
#        # First empty? Can happen if max_length very small
#        if len(formatted_params) > 0 and formatted_params[0] == "":
#            formatted_params = formatted_params[1:]
#        # End   
#        if len(tmp) > 0: formatted_params.append(", ".join(tmp))
#            
#        spacers = "".join([" "] * (len(name) + 1))
#        return name + "(" + f",<br/>{spacers}".join(formatted_params) + ")"   
#
#    def signature(self, remove_self = None, max_length = 200):
#        assert isinstance(remove_self, type(None)) or isinstance(remove_self, bool)
#        assert isinstance(max_length, int)
#        assert max_length >= 0
#        name = self._name
#        # Remove ^parent. if self._parent is set
#        if isinstance(self._parent, str):
#            name = re.sub(f"^{self._parent}\.", "", self._name)
#        else:
#            name = self._name
#
#        if remove_self is None:
#            remove_self = self._parent is not None
#        
#        return self._format_signature(name, max_length, remove_self)
#
#    def getmembers(self):
#        members = []
#        for rec in inspect.getmembers(self._obj):
#            # requires three independent ifs here
#            if rec[0].startswith("__"): continue
#            if not inspect.isfunction(rec[1]) and not inspect.isclass(rec[1]): continue
#            if not self._args.include_hidden and rec[1].__name__.startswith("_"): continue
#            members.append((f"{self.fullname()}.{rec[0]}", rec[1]))
#        return members
#
#    def get(self, attr):
#        assert isinstance(attr, str), "argument `attr` must be of type str"
#        if not hasattr(self._doc, attr):    return None
#        else:                               return getattr(self._doc, attr)
#
#    def write_qmd(self):
#        import tempfile
#        import filecmp
#
#        qmd   = f"{self._args.man_dir}/{self.quartofile()}"
#        ofile = f"{self._args.quarto_dir}/{qmd}"
#
#        if not os.path.isfile(ofile):
#            with open(ofile, "w+") as fid: print(self, file = fid)
#        else:
#            tmpfile = tempfile.NamedTemporaryFile()
#            with open(tmpfile.name, "w+") as fid: print(self, file = fid)
#            files_equal = filecmp.cmp(tmpfile.name, ofile)
#            # New file differs? Overwrite existing qmd. Re-write the file (not
#            # move the temporary file) to ensure correct file permissions.
#            if not files_equal:
#                with open(ofile, "w+") as fid: print(self, file = fid)
#            tmpfile.close()
#        
#        # Return name of the qmd; used for linking
#        return qmd
#
#    def __repr_args(self):
#
#        res = ""
#
#        # Given the signature, we should have the following parameters
#        expected_args = list(self._signature.parameters.keys())
#        # These are the available parameters (from the docstring)
#        documented_args = [re.sub("^\*+", "", x.arg_name.strip()) for x in self.get("params")]
#        # If self._parent is set this is the man page for a method.
#        # if the first argument in list is 'self', remove.
#        if self._parent and len(expected_args) > 0 and expected_args[0] == "self":
#            expected_args.remove("self")
#
#        # Check if any of the expected arguments is not documented
#        missing_args = []
#        for ea in expected_args:
#            if not ea in documented_args:
#                missing_args.append(ea)
#
#        # Counting number of warnings and/or arguments added
#        counter = 0
#
#        if len(missing_args) > 0:
#            counter += 1
#            res += "<ul>"
#            for rec in missing_args:
#                res += f"<li>WARNING(missing argument definition \"{rec}\" in docstring)</li>"
#            res += "</ul>"
#
#        # Count arguments
#        res += "<dl class=\"pyp-list param-list\">\n"
#        for arg in self.get("params"):
#            counter += 1
#            # If we get "argument (class)" we separate them
#            mtch = re.findall(r"^(.*)\((.*?)\)$", arg.args[1])
#            if len(mtch) > 0:
#                arg_name = mtch[0][0].strip()
#                arg_cls  = f"<code class=\"argument-class\">{mtch[0][1]}</code>"
#            else:
#                arg_name = arg.args[1].strip()
#                arg_cls  = ""
#
#            #short_arg = re.search("^([\*\w]+)", arg.args[1]).group(1).replace("*", "")
#            # Building html table row
#            res += "  <dt style = \"white-space: nowrap; font-family: monospace; vertical-align: top\">\n" + \
#                   f"   <code id=\"{self.fullname()}:{arg_name}\">{arg_name}</code>{arg_cls}\n" + \
#                   "  </dt>\n" + \
#                   f" <dd>{self._add_references(arg.description)}</dd>\n"
#
#        res += "</dl>"
#
#        # If no arguments or warnings have been added, return None
#        # such that we can skip to add the 'Arguments' section.
#        return None if counter == 0 else res
#
#
#    def __repr_raises(self):
#
#        res = "<ul class=\"python-raises\">\n"
#        for rec in self.get("raises"):
#            res += f"<li><code class=\"text-warning\">{rec.type_name}</code>: " + \
#                   f"{self._add_references(rec.description)}\n"
#        return res + "</ul>\n"
#
#    def __repr__(self):
#        if self.get("short_description") is None:
#            res  = "---\ntitle: \"WARNING(short_description missing)\"\n---\n\n"
#        else:
#            res  = "---\ntitle: \"" + \
#                   self._add_references(self.get("short_description")) + \
#                   "\"\n---\n\n"
#
#        if self.get("long_description"):
#            res += "### Description\n\n"
#            res += self._add_references(self.get("long_description"))
#        else:
#            res += "WARNING(long_description missing)"
#
#        res += "\n\n### Usage\n\n"
#        res += "<pre><code class='language-python'>" + \
#               f"{self.signature(max_length = 50)}" + \
#               "</code></pre>"
#
#        # Function arguments
#        tmp = self.__repr_args()
#        if tmp is not None:
#            res += "\n\n### Arguments\n\n" + tmp
#
#        # Return value
#        if self.get("returns"):
#            res += "\n\n### Return\n\n"
#            res += f"{self._add_references(self.get('returns').description)}"
#
#        # If is class, append methods
#        if self.isclass():
#
#            res += "\n\n### Methods\n\n"
#            # Convert package.module.class into package.module
#            parent = re.sub(r"\.[^.]*$", "", self.fullname())
#
#            res += "<dl class=\"pyp-list method-list\">\n"
#            for name,meth in man.getmembers():
#                m_man = manPage(name, meth, args)
#                if m_man.get("short_description") is None:
#                    short = "WARNING(short_description missing)"
#                else:
#                    short = m_man.get("short_description")
#
#                # Adding <dt><dd> for current method
#                link = m_man.quartofile()
#                text = re.sub(f"^{parent}\.", "", m_man.signature(remove_self = True))
#                res += "    <dt style = \"white-space: nowrap; font-family: monospace; vertical-align: top\">\n" + \
#                       f"       <code>[{text}]({link})</code>\n    </dt>\n" + \
#                       f"    <dd>{short}</dd>\n"
#            res += "</dl>\n"
#
# 
#        # If we have examples:
#        if self.get("examples"):
#            examples = []
#            for tmp in [ex.description for ex in self.get("examples")]:
#                # Prepare example and possibly split it.
#                tmp       = self._prepare_example(tmp)
#                examples += self._split_example(tmp)
#
#            res += "\n\n### Examples\n\n"
#            #####res += self._add_matplotlib_inline()
#            for tmp in examples:
#                res += self.__repr_examples(tmp)
#            res += "\n"
#
#        # If has documented raises exception
#        if len(self.get("raises")) > 0:
#            res += "\n\n### Raises\n\n" + self.__repr_raises()
#
# 
#        return res
#
#    def _add_references(self, x):
#        import re
#        if x is None: return x
#
#        # Replace sphinx refs with quarto refs
#        matches = re.findall(r":py:(?:func|class|method):`.*?`", x)
#
#        # If any matches are found, set quarto references properly
#        for m in matches:
#            # Find basic match
#            tmp = re.search("py:(\w+?):`(.*?)(?=`)", m)
#            if tmp:
#                # Extact typ (func, class, or method) and the 'reference'
#                typ,ref = tmp.groups()
#                # If format is "name <ref>" we further decompose the match
#                ref2 = re.match("^(.*)\s+?<(.*?)>$", ref)
#                # Take `text <link>` from the docstring
#                if ref2:
#                    x = x.replace(m, f"[{ref2.group(1)}]({ref2.group(2)}.qmd)")
#                # IF we only have a `word` we expect that it refers
#                # to it's current module OR its class (if typ == "method")
#                elif re.match("^\w+$", ref):
#                    if typ == "method":
#                        cls = re.sub(r"\.\w+?$", "", self.fullname())
#                        x   = x.replace(m, f"[{ref}]({cls}.{ref}.qmd)")
#                    else:
#                        x   = x.replace(m, f"[{ref}]({self._obj.__module__}.{ref}.qmd)")
#                # Else take whatever we got
#                else:
#                    x = x.replace(m, f"[{ref}]({ref}.qmd)")
#
#        return x
#
#    def __repr_examples(self, x):
#        assert isinstance(x, str)
#        res = "```{python}\n" + \
#              "#| echo: true\n" + \
#              "#| error: true\n" + \
#              "#| warning: true\n" + \
#              re.sub("^#:", "#", x, flags = re.MULTILINE) + \
#              "\n```\n\n"
#        return res
#
#    def _prepare_example(self, x):
#        """prepapre_example(x)
# 
#        Args:
#            x (str): The example extracted from the docstring.
# 
#        Return:
#        str : Modified example to be ready for quarto.
#        """
#        # Comment 'text' (can be included in the py example section)
#        x = re.sub(r"^(?!(>>>))", "## ", x, flags = re.MULTILINE)
#        # Removing empty lines
#        x = re.sub(r"^##\s+?$", "", x, flags = re.MULTILINE)
#        # Remove >>> code identifiers
#        x = re.sub(r"^>>>\s+?", "", x, flags = re.MULTILINE)
#        return x
#
#    def _add_matplotlib_inline(self):
#        """Add Matplotlib Line Option
#
#        Supressing warnings due to interactive mode when plotting.
#        A extra (silent) code chunk at the beginning of each Example section.
#        """
#        res = "```{python}\n" + \
#              "#| echo: false\n" + \
#              "#| error: true\n" + \
#              "#| warning: true\n" + \
#              "import matplotlib.pyplot as plt\n" + \
#              "%matplotlib inline\n" + \
#              "```\n\n"
#        return res
#
# 
#    def _split_example(self, x):
#        """split_example(x)
# 
#        Args:
#            x: str, the example extracted from the docstring.
# 
#        Return:
#        list: List of strings. If we find `#:` at the start of a line
#        we split the example at this position in multiple segments.
#        """
#        res = re.split(r"\n(?=#:)", x, flags = re.MULTILINE)
#        # Remove empty lines if any
#        for i in range(len(res)):
#            res[i] = re.sub("#:[\s+]?\n", "", res[i], flags = re.MULTILINE)
#        return res
#
#
## Testing a function
#def py2quarto(obj, package, include_hidden = False):
#    """py2quarto(obj)
#
#    Args:
#        obj: function or class.
#        package (str): name of the package for which the documentation
#            is created.
#        include_hidden (bool): Defaults to `False`. If set,
#            hidden functions and methods (_*, __*) will also
#            be documented.
#    """
#
#    if not inspect.isfunction(obj) and not inspect.isclass(obj):
#        raise TypeError("argument `obj` must be a function or class")
#    if not isinstance(package, str):
#        raise TypeError("argument `package` must be str")
#    if not isinstance(include_hidden, bool):
#        raise TypeError("argument `include_hidden` must be boolean True or False")
#
#
#    docstrings = extract_docstrings(obj, None, args.docstringstyle, include_hidden)
#
#    # Generate manPage object
#    u = manPage(package    = args.package,
#                typ        = "function" if inspect.isfunction(obj) else "class",
#                name       = obj.__name__,
#                docstrings = docstrings)
#
#    if inspect.isclass(obj):
#        docstrings = extract_docstrings(obj, u, args.docstringstyle, include_hidden)
#        sys.exit(333)
#
#    # Returning object of class manPageFunction or manPageClass
#    return u
#
#def get_members(pkg, predicate = None):
#    from inspect import getmembers
#    result = {}
#    # Extract all members (given predicate) which have
#    # a __qualname__ (functions, classes), the rest will be ignored
#    for rec in getmembers(pkg, predicate):
#        try:
#            result[".".join([rec[1].__module__, rec[1].__qualname__])] = rec[1]
#        except:
#            pass
#    return result
#
## -------------------------------------------------
## -------------------------------------------------
#if __name__ == "__main__":
#
#    # Parsing user args
#    args = parse_input_args()
#
#    # If args.action is init, crate _quarto.yml
#    yml_newly_created = create_quarto_yml(args)
#
#    # Wirte sass (if not existing _or_ action = "init")
#    write_sass(args)
#    # Write index (if not existing)
#    write_index(args)
#
#    # Trying to import the module
#    try:
#        pkg = import_module(args.package)
#    except Exception as e:
#        raise Exception(e)
#
#    # Extracting functions and classes
#    import inspect
#    functions = inspect.getmembers(pkg, inspect.isfunction)
#    classes   = inspect.getmembers(pkg, inspect.isclass)
#
#    functions = dict(zip([x[0] for x in functions], [x[1] for x in functions]))
#    classes   = dict(zip([x[0] for x in classes], [x[1] for x in classes]))
#
#    #print(functions.keys())
#    #print(classes.keys())
#    #print("\n\n")
#
#    #functions = {"darken": functions["darken"]}
#    #classes   = {"sequential_hcl": classes["sequential_hcl"]}
#    
#    # -------------------------------------------------
#    # Create man pages for functions
#    # -------------------------------------------------
#    man_func_created = {}
#    for name,func in functions.items():
#        print(f"[DEVEL] Create man page function {name}")
#        man = manPage(name, func, args)
#        man_func_created[name] = man.write_qmd()
#    print(f"{man_func_created=}")
#
#    print(f"Number of function manuals created: {len(man_func_created)}")
#
#    # Adding Function references to _quarto.yml
#    if yml_newly_created and len(man_func_created) > 0:
#        update_quarto_yml(args, "Function reference", man_func_created)
#
#
#    # -------------------------------------------------
#    # Create man pages for classtions
#    # -------------------------------------------------
#    man_class_created = {}
#    man_meth_created  = {}
#    for name,cls in classes.items():
#        print(f"[DEVEL] Create man page for class {name}")
#        man = manPage(name, cls, args)
#        man_class_created[name] = man.write_qmd()
#        #if name == "qualitative_hcl":
#        #    sys.exit(0)
#
#        # Now do the same for all methods belonging to the current class (if any)
#        for name,meth in man.getmembers():
#            if not args.include_hidden and meth.__name__.startswith("_"): continue
#            print(f"[DEVEL]   + method page for {name}")
#            parent = re.sub(r"\.[^.]*$", "", man.fullname())
#            m_man = manPage(name, meth, args, parent = parent)
#            man_meth_created[name] = m_man.write_qmd()
#    
#
#    print(f"Number of class manuals created: {len(man_class_created)}")
#
#    # Adding Function references to _quarto.yml
#    if yml_newly_created and len(man_class_created) > 0:
#        update_quarto_yml(args, "Class reference", man_class_created)
#
