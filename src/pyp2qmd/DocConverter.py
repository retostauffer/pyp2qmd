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

    The :py:class:`Config <pyp2qmd.Config.Config>` contains all the required
    arguments/settings to perform this task and is, thus, the only reqired
    input argument.

    Args:
        config (Config): See :py:class:`Config <pyp2qmd.Config.Config>` for details; must be
            set up properly.

    Return:
        Initializes a new object of class `DocConverter`.

    Raises:
        TypeError: If `config` is not of class :py:class:`Config <pyp2qmd.Config.Config>`.
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
    _man_created = {"class": dict(), "function": dict(), "method": dict()}

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
        else:
            from os.path import isdir, join
            tmp = join(self.config_get("quarto_dir"), self.config_get("man_dir"))
            if not isdir(tmp):
                raise Exception("missing folder \"{tmp}\". pyp2qmd project not initialized? (check documentation for `pyp2qmd init ...`)")

        # Class is now ready to do what it is designed for

    def __init_documentation(self):

        from os.path import join, isdir, basename
        from shutil import copy
        from re import sub, match

        # Getting package name
        pkgname = match(r"^([^\.]+)", self.__class__.__module__).group(1)

        # Create required output folder(s)
        self.__make_output_dirs()

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

        # Copy scss
        src = pkg_file(pkgname, "templates", "pyp.scss")
        copy(src, join(self.config_get("quarto_dir"), "pyp.scss"))


    def __make_output_dirs(self):

        from os import makedirs
        from os.path import join, isdir, basename

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

        Calls the `.get()` method of the
        :py:class:`Config <pyp2qmd.Config.Config>` object
        as defined via `config` on class initialization. Will raise
        exceptions if not available (see :py:class:`Config <pyp2qmd.Config.Config>`
        for details).

        Args:
            what (str): Attribute to be returned.

        Return:
            Whatever is stored on the `_{what}` attribute of the
            :py:class:`Config <pyp2qmd.Config.Config>` object.
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


    def document_functions(self):
        """Document Functions

        Generates man pages for all exported functions.
        """
        from .ManPage import ManPage

        for name,cls in self.get_functions().items():
            if not self.config_get("silent"):
                print(f"Create man page for function {name}")
            man = ManPage(name, cls, self._config)
            self._man_created["function"][name] = man.write_qmd()
    
    def examples_functions(self):
        """Examples of Functions

        Extracts examples from the functions docstring (if any)
        and writes a dedicated quarto markdown (qmd) file which can be
        used to see if the examples run without errors.
        """
        from .ManPage import ManPage

        for name,cls in self.get_functions().items():
            if not self.config_get("silent"):
                print(f"Create example qmd for function {name}")
            man = ManPage(name, cls, self._config)
            man.write_examples_qmd()

    def document_classes(self):
        """Examples of Classes and Methods

        Generates man pages for all exported classes.
        """
        from .ManPage import ManPage
        from re import sub

        for name,cls in self.get_classes().items():
            if not self.config_get("silent"):
                print(f"Create man page for class {name}")
            man = ManPage(name, cls, self._config)
            self._man_created["class"][name] = man.write_qmd()

            for name,meth in man.getmembers():
                if not self.config_get("include_hidden") and meth.__name__.startswith("_"):
                    continue
                if not self.config_get("silent"):
                    print(f"   + method page for {name}")
                parent = sub(r"\.[^.]*$", "", man.fullname())
                m_man = ManPage(name, meth, self._config, parent = parent)
                m_man.write_qmd()

    def examples_classes(self):
        """Document Classes

        Extracts examples from the classes and methods docstrings (if any)
        and writes a dedicated quarto markdown (qmd) file which can be
        used to see if the examples run without errors.
        """
        from .ManPage import ManPage
        from re import sub

        for name,cls in self.get_classes().items():
            if not self.config_get("silent"):
                print(f"Create example qmd for class {name}")
            man = ManPage(name, cls, self._config)
            man.write_examples_qmd()

            for name,meth in man.getmembers():
                if not self.config_get("include_hidden") and meth.__name__.startswith("_"):
                    continue
                if not self.config_get("silent"):
                    print(f"   + examples for method page for {name}")
                parent = sub(r"\.[^.]*$", "", man.fullname())
                m_man = ManPage(name, meth, self._config, parent = parent)
                m_man.write_examples_qmd()

    def document(self):
        """Document All

        Documents all exported classes and functions. Convenience function,
        calls :py:meth:`document_functions` and :py:meth:`document_classes`.
        """
        self.document_functions()
        self.document_classes()

    def examples(self):
        """Extract Examples

        Will extract all examples from the docstrings of the exported functions,
        classes, and methods and create dedicated quarto markdown files (qmd) for each
        of them. Only contains the example code. Used to quarto render all examples
        to see if any of them break.
        """
        self.examples_functions()
        self.examples_classes()
    
    def update_quarto_yml(self):
        """Update Quarto

        Updates the `_quarto.yml` file by adding all classes and functions
        to the website sidebar content (navigation). This is only done if
        the quarto file has just been initialized and man pages have been
        crated.
        """

        n = 0
        if not self.config_get("silent"):
            print(f"pyp2qmd: Number of (main) man pages created")
            for k,v in self._man_created.items():
                kx = "(es):" if k == "class" else "(s):"
                n += len(v)
                print(f"         {k + kx:15s}   {len(v):4d}")
            print(f"         in total:         {n:4d}")

        # Nothing? Do nothing
        if not self._quarto_yml_initialized or n == 0:
            return

        # Reading existing yml file
        content = self._load_yaml()
            
        content["website"]["sidebar"]["contents"] = []
        # Setting up dictionary for function references
        for what in ["Function", "Class"]:
            if len(self._man_created[what.lower()]):
                tmp = []
                for key,val in self._man_created[what.lower()].items():
                    tmp.append({"text": key, "file": val})
                tmp = {"section": f"{what} references", "contents": tmp}
                content["website"]["sidebar"]["contents"].append(tmp)

        # Write back
        self._save_yaml(content)


    def add_navbar_page(self, src, dest, text, menu = None):
        """Add Page to Navigation

        Adds page to website navbar left. Will be added to the _quarto.yml
        file if not yet included. Will place the source file (qmd) in the
        quarto output folder under name `dest` and linked in the navigation
        as `text`.

        Args:
            src (str): Path to an existing quarto file, must end in `.qmd`.
            dest (str): Name or path for target quarto file. If path, the
                directory will be created inside `quarto_dir` as specified in the
                config (see :py:class:`DocConverter`) if not yet existing.
            text (str): Name used in the navigation.
            menu (None, str): Must be `None` if pages are added. If set,
                it is expected that a menu with this name exists. The page
                will then be added to that menu if not already in there.

        Raises:
            TypeError: If `src`, `dest`, `text` are not str.
            ValueError: If `src` and `dest` do not end in `.qmd`
            ValueError: If `dest` is a path, not only the name of the target quarto file.
            FileNotFoundError: If `src` does not exist.
            TypeError: If `menu` is not `None` nor `str`.
            Exception: If `dest` already exists but overwrite is set `False`
                (see :py:class:`DocConverter`).
            Exception: if `src` cannot be copied to destination.
        """


        from re import match
        from os.path import isfile, basename, dirname, join
        from os import makedirs
        from shutil import copy

        if not isinstance(src, str):
            raise TypeError("argument `src` must be str, qmd file name")
        elif not match(r".*\.qmd$", src):
            raise ValueError("argument `src` must end in '.qmd' pointing to a quarto file")
        elif not isfile(src):
            raise FileNotFoundError(f"cannot find file \"{src}\"")

        if not isinstance(dest, str):
            raise TypeError("argument `dest` must be str, qmd file name")
        elif not match(r".*\.qmd$", dest):
            raise ValueError("argument `dest` must end in '.qmd' pointing to a quarto file")

        # Path?
        if not dest == basename(dest):
            tmp = join(self.config_get("quarto_dir"), dirname(dest))
            try:
                makedirs(tmp, exist_ok = True)
            except Exception as e:
                raise Exception(f"cannot create folder \"{tmp}\": {e}")

        if not isinstance(text, str):
            raise TypeError("argument `text` must be str, link name")

        if not isinstance(menu, type(None)) and not isinstance(menu, str):
            raise TypeError("argument `menu` must be `None` or str")

        # Already exists?
        dest_path = join(self.config_get("quarto_dir"), dest)
        if isfile(dest_path) and not self.config_get("overwrite"):
            raise Exception(f"target file \"{dest_path}\" already exists and overwrite " + \
                    "is False. Consider enabling overwrite. Could result in loss of data!")

        # Reading existing yml file
        content = self._load_yaml()

        # Access existing navbar left. If this fails, it does not exist
        # in the _quarto.yml and an exception will be thrown.
        try:
            tmp = content["website"]["navbar"]["left"]
        except:
            raise Exception(f"\"{ymlfile}\" does not contain website > navbar > left")

        # Copy src file to dest_path using shutil
        try:
            copy(src, dest_path)
        except Exception as e:
            raise Exception(e)

        # If `menu = None` we are adding a page, so we are searching
        # (and appending) to  this:
        nav = content["website"]["navbar"]["left"] # 'pointer'
        # If `menu` is set, we must first find the menu.
        if isinstance(menu, str):
            found = False
            for j in range(len(nav)):
                if not "menu" in nav[j].keys() or not "text" in nav[j].keys():
                    continue
                elif nav[j]["text"] == menu:
                    # Replace `nav` object and break
                    nav = nav[j]["menu"]
                    found = True
                    break
            # Not found? Error
            if not found:
                raise Exception(f"could not find menu \"{menu}\". " + \
                                "Not yet added via .add_navbar_menu()?")


        # Loop trough existing entries. If we find an entry
        # with the current file text, just update the text. Else add at the end.
        # This is when adding pages directly to the navigation.
        found = False
        for i in range(len(nav)):
            if len(nav[i]) > 0 and nav[i]["file"] == dest:
                nav[i]["text"] = text
                found = True
                break

        # Not found? Append at the end.
        if not found: nav.append({"file": dest, "text": text})

        # Write back
        self._save_yaml(content)


    def add_navbar_right(self, x):
        """Add Element To Navbar Right

        Allows to add elements to website navbar right.
        Will add it if not yet existing. Accepts a dict, originally
        used to add repository logo and link.
        """
        if not isinstance(x, dict):
            raise TypeError("argument `x` is expected to be a dict")

        content = self._load_yaml()
        try:
            tmp = content["website"]["navbar"]
        except:
            raise Exception("_quarto.yml does not contain website > navbar")

        try:
            tmp = content["website"]["navbar"]["right"]
        except:
            # Initialize empty list element
            tmp["right"] = []
            tmp = tmp["right"]
        tmp.append(x)

        self._save_yaml(content)

    def add_navbar_menu(self, menu):
        """Add Dropdown Menu to Navigation

        Adds a menu (dropdown menu) to the top navigation which can be
        populated with a series of pages. Will only be added if not yet existing.

        Args:
            menu (str): Name of the dropdown menu.

        Raises:
            TypeError: If `menu` is not str.
        """


        from re import match
        from os.path import isfile, basename

        if not isinstance(menu, str):
            raise TypeError("argument `menu` must be str")

        # Reading existing yml file
        content = self._load_yaml()

        # Check for menus
        found = False
        for rec in content["website"]["navbar"]["left"]:
            # No menu? Or no text? Skip
            if not "menu" in rec.keys() or not "text" in rec.keys():
                continue
            # Is the current menu the one the user wants to add?
            if rec["text"] == menu:
                found = True
        
        # Not found: Add new empty menu
        if not found:
            tmp = {"text": menu, "menu": []}
            content["website"]["navbar"]["left"].append(tmp)

        # Write back
        self._save_yaml(content)


    def add_favicon(self, file):
        """Add Favicon

        Args:
            file (str): File name of parth to the favicon (png, jpg).

        Raises:
            TypeError: If `file` is not str.
            FileNotFoundError: If `file` does not point to an existing file.
        """

        from re import match
        from os.path import isfile, basename, join
        from shutil import copy

        if not isinstance(file, str):
            raise TypeError("argument `file` must be str")
        elif not isfile(file):
            raise FileNotFoundError(f"file \"{f}\" not found on disc")

        # Reading existing yml file
        content = self._load_yaml()

        # Try to find the 'website' section where we will add this option
        content["website"]["favicon"] = basename(file)

        # Write back
        self._save_yaml(content)

        # Copy src file to dest_path using shutil
        try:
            copy(file, join(self.config_get("quarto_dir"), basename(file)))
        except Exception as e:
            raise Exception(e)

    def add_logo(self, logo, title):
        """Adding Logo and/or Title

        Allows to add a logo image and/or change the title.

        Args:
            logo (str, None): String (image file name) or None. If None,
                the logo is not set or removed if needed.
            title (str, None): String (title) or None. If None, title is set false
                such that it is not shown in navbar.
        """
        if not isinstance(logo, (str, type(None))):
            raise TypeError("argument `logo` must be str or None")
        if not isinstance(title, (str, type(None))):
            raise TypeError("argument `title` must be str or None")

        content = self._load_yaml()
        try:
            tmp = content["website"]["navbar"]
        except:
            raise Exception("_quarto.yml does not contain expected website > navbar")

        if isinstance(title, type(None)):
            tmp["title"] = False
        else:
            tmp["title"] = title

        if isinstance(logo, str):
            tmp["logo"] = logo
        elif "logo" in tmp.keys():
            del tmp["logo"]

        self._save_yaml(content)


    def _load_yaml(self):
        """Load Existing YML File

        Loads the existing _quarto.yml file.
        """
        from os.path import join
        import yaml
        ymlfile = join(self.config_get('quarto_dir'), "_quarto.yml")
        with open(ymlfile, "r") as fid:
            content = yaml.load("".join(fid.readlines()), yaml.SafeLoader)
        return content


    def _save_yaml(self, content):
        """Save (Updated) YML File

        Writes the dictionary back to `_quarto.yml`.
        """
        from os.path import join
        import yaml
        assert isinstance(content, dict), TypeError("argument `content` expected to be dict")
        ymlfile = join(self.config_get('quarto_dir'), "_quarto.yml")
        with open(ymlfile, "w+") as fid: fid.write(yaml.dump(content))


    def _add_website_option(self, key, value):
        assert isinstance(key, str), TypeError("argument `key` must be str")
        assert isinstance(value, str), TypeError("argument `value` must be str")

        content = self._load_yaml()

        # Access existing navbar left. If this fails, it does not exist
        # in the _quarto.yml and an exception will be thrown.
        try:
            tmp = content["website"]
        except:
            raise Exception(f"\"{ymlfile}\" does not contain website > navbar > left")

        tmp[key] = value
        self._save_yaml(content)

    def add_repo_url(self, url, branch = "main"):
        """Adding Soruce Code Repository URL

        Args:
            url (str): URL (e.g., to the github repository).
            branch (str): Branch name, defaults to "main".

        Raises:
            TypeError: If `url` or `branch` are not str.
            ValueError: If `url` does not look like a URL.
        """

        from re import match

        if not isinstance(url, str): raise TypeError("argument `url` must be str")
        if not isinstance(branch, str): raise TypeError("argument `url` must be str")
        if not match("^https?:\/\/", url):
            raise ValueError(f"url (\"{url}\") does not look like a valid URL")

        self._add_website_option("repo-url", url)
        self._add_website_option("repo-branch", branch)

    def add_issue_url(self, url):
        """Adding URL to Issue Trackign Page

        Args:
            url (str): URL (e.g., to the github issues page).

        Raises:
            TypeError: If `url` is not str.
            ValueError: If `url` does not look like a URL.
        """

        from re import match

        if not isinstance(url, str): raise TypeError("argument `url` must be str")
        if not match("^https?:\/\/", url):
            raise ValueError(f"url (\"{url}\") does not look like a valid URL")

        self._add_website_option("issue-url", url)


    def add_scss(self, file):
        from os.path import isfile, join
        if not isinstance(file, str):
            raise TypeError("argument `file` must be str")
        elif not isfile(join(self.config_get("quarto_dir"), file)):
            raise FileNotFoundError(f"missing \"{join(self.config_get('quarto_dir'), file)}\"")

        content = self._load_yaml()

        # Access existing navbar left. If this fails, it does not exist
        # in the _quarto.yml and an exception will be thrown.
        try:
            tmp = content["format"]["html"]["theme"]
        except:
            raise Exception(f"\"{ymlfile}\" does not contain format > html > theme")

        # Append in second position
        if not file in tmp:
            if not isinstance(tmp, list) or len(tmp) == 0:
                content["format"]["html"]["theme"] = [file]
            else:
                content["format"]["html"]["theme"] = [tmp[0], file] + tmp[1:]

        self._save_yaml(content)




