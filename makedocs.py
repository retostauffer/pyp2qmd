#!/usr/bin/env python3
# -------------------------------------------------
# Building quarto manual pages for python package
# -------------------------------------------------

### Tutorial
##extract = mydoc.extract.PyExtract(source)
##add = extract.extract('add')

import sys
import os
import re
import yaml
import re
import argparse
from importlib import import_module # Dynamic module import
import inspect                      # Find functions/classes in package
import mydocstring                  # Parsing functions and classes (extracting docstring)
import docstring_parser             # Parsing docstring

class docParser:
    def __init__(self, file):
        if not isinstance(file, str):
            raise TypeError("argument `file` must be str")
        if not os.path.isfile(file):
            raise FileNotFoundError(f"file \"{file}\" not found")

        try:
            with open(file, "r") as fid:
                self._src = "".join(fid.readlines())
        except Exception as e:
            raise Exception(e)

        # Find functions
        fun = self.find_functions()

    def find_functions(self):
        pattern = re.compile(r"^def\s(.*)(?=(\())", re.M)
        function_names = []
        for rec in pattern.findall(self.source()):
            function_names.append(rec[0])

        print(f"[DEV] {function_names=}")
        return function_names

        
    def source(self):
        return self._src

def parse_input_args():

    # Allowed action options
    allowed_action = ["init", "document"]

    import argparse
    parser = argparse.ArgumentParser("Creating qmd documentation from python package")
    parser.add_argument("action", nargs = 1, type = str,
            help = f"Action to perform, one of: {', '.join(allowed_action)}")
    parser.add_argument("-p", "--package", type = str,
            help = "Name of the python package.")
    parser.add_argument("-o", "--output_dir", type = str, default = "_quarto",
            help = "Name of the output directory to store the qmd file")
    parser.add_argument("--overwrite", default = False, action = "store_true",
            help = "Only used if action = create; will overwrite _quarto.yml if needed.")
    parser.add_argument("--man_dir", type = str, default = "man",
            help = "Folder to store the function/class manuals qmds, " + \
                    "ceated inside the --output_dir folder. Must start with [A-Za-z].")
    parser.add_argument("--docstringstyle", type = str, default = "GOOGLE",
            help = "Docstring type (format).")
    parser.add_argument("--include_hidden", default = False, action = "store_true",
            help = "If set, hidden functions and methods will also be documented " + \
                    "(functions/methods starting with _ or __)")

    # Parsing input args
    args = parser.parse_args()

    args.action = args.action[0]
    if not args.action in allowed_action:
        parser.print_help()
        sys.exit("\nUsage error: invalid \"action\" (see help).")

    if args.package is None:
        parser.print_help()
        sys.exit("\nUsage error: argument -p/--package must be set.")

    ymlfile = f"{args.output_dir}/_quarto.yml"
    if args.action == "create" and isfile(ymlfile):
        parser.print_help()
        sys.exit(f"\nUsage error: action is set to \"{args.action}\" " + \
                 f"but the file \"{ymlfile}\" " + \
                 f"already exists. Remove folder \"{args.output_dir}\" or use " + \
                 f"--overwrite; be aware, will overwrite the existing \"{ymlfile}\".")

    if not re.match("^[A-Za-z]", args.man_dir):
        parser.print_help()
        sys.exit(f"\nUsage error: man_dir must start with [A-Za-z].")

    return args


def create_quarto_yml(args):
    """

    Returns:
    bool: Returns `True` if the yml file is created the first time
    by calling this function, else `False` (file did already exist).
    """
    import os
    ymlfile = f"{args.output_dir}/_quarto.yml"

    if args.action == "init":
        res = True
        # If yml already exists and overwrite = False, error
        if os.path.isfile(ymlfile) and not args.overwrite:
            raise Exception(f"action = {args.action}, overwrite = {args.overwrite} " + \
                    f"but file \"{ymlfile}\" already exists; stop!")

        # If output directory does not yet exist, create.
        if not os.path.isdir(args.output_dir):
            try:
                os.makedirs(args.output_dir)
            except:
                raise Exception(f"Unable to create output folder \"{args.output_dir}\"")

        # Content of the yml file
        content = {"project": {"type": "website"},
                     "website": {"title": args.package,
                        "navbar": {"search": True,
                            "right": [{"icon": "github", "href": "https://github.com/dummy/entry", "aria-label": "gsdata GitHub"}]},
                        "sidebar": {"collapse-level": 1,
                           "contents": [{"text": "Home", "file": "index.qmd"}]
                        }
                     },
                     "format": {"html": {"theme": ["quarto", "pyp.scss"]}},
                     "execute": {"cache": True}
                   }

        # Else create (overwrite) the file
        with open(ymlfile, "w+") as fid: fid.write(yaml.dump(content))

    # Else (not init): Ensure the output folder and the yml file exists, else
    # init must be used.
    else:
        res = False
        if not os.path.isdir(args.output_dir):
            raise Exception(f"Output folder \"{args.output_dir}\" does not exist. " + \
                    "You may first need to call the script with action = init")
        elif not os.path.isfile(ymlfile):
            raise Exception(f"yml file \"{ymlfile}\" does not exist. " + \
                    "You may first need to call the script with action = init")

    # Create references dir if not existing
    refdir = os.path.join(args.output_dir, args.man_dir)
    if not os.path.isdir(refdir):
        try:
            os.makedirs(refdir)
        except Exception as e:
            raise Exception(e)

    return res

def write_index(args):
    """
    Write index

    Returns:
    bool : True if index was newly created, else False.
    """
    import os
    import re
    from datetime import datetime as dt
    qmdfile = f"{args.output_dir}/index.qmd"
    res = False
    if not os.path.isfile(qmdfile):
        res = True
        # Sorry, indent is important
        content = f"""
        # {args.package} Package Documentation

        This page has been automatically generated by
        pyp2qmd (Python package documentation to quarto),
        converting the docstrings of all loaded functions
        and methods available via `{args.package}.*` into
        quarto markdown files (`.qmd).

        ### Function reference

        Contains the documentation/reference of all functions,
        including description, usage, arguments, exceptions,
        as well as evaluated examples.

        ### Class reference

        The documentation/reference of all classes including
        description, usge, arguments, _methods_, exceptions,
        and evaluated examples (if any).

        For each method listed on the class reference page,
        a quarto markdown file is generated as well, altough
        not listed in the navigation. The documentation can
        be accessed by visiting the class reference, and then
        click on the method of interest.
        
        _Generated: {dt.now() : %Y-%m-%d %H:%M}_.
        """

        # There is for sure a single nice regex instead of
        # this approach (currently the regex kills empty lines).
        content = re.sub(r"^(?!\s*$)\s+", "", content, flags = re.MULTILINE)
        with open(qmdfile, "w+") as fid: fid.write(content)

    return res


def write_sass(args):
    """
    Write sass

    Returns:
    bool : True sass file was created/replaced, else False.
    """
    import os
    scssfile = f"{args.output_dir}/pyp.scss"
    res = False
    if not os.path.isfile(scssfile) or args.action == "init":
        res = True
        # Sorry, indent is important
        content = """
/*-- scss:defaults --*/
// Base document colors
$body-bg: white;
$body-color: black;
//$link-color: #75AADB;
$link-color: #4287f5;

/*-- scss:custom --*/
// Styling of the <dl> lists
dl.pyp-list {
    dd {
        margin-left: 2em;
    }
}
div.cell-output-display {
    margin: 1em 0;
    padding: 0.5em 0.5em;
    pre {
        background-color: #e0e7ff;
    }
}
        """
        with open(scssfile, "w+") as fid: fid.write(content)

    return res

def update_quarto_yml(args, section, mans):

    import yaml

    assert isinstance(section, str)
    assert isinstance(mans, dict)
    assert all([isinstance(x, str) for x in mans])
    ymlfile = f"{args.output_dir}/_quarto.yml"

    # Read existing 
    with open(ymlfile, "r") as fid:
        content = yaml.load("".join(fid.readlines()), yaml.SafeLoader)

    # Dictionary to extend the content
    tmp = []
    for key,val in mans.items():
        tmp.append({"text": key, "file": val})
    tmp = {"section": section, "contents": tmp}

    # Append and overwrite _quarto.yml with new content
    content["website"]["sidebar"]["contents"].append(tmp)
    with open(ymlfile, "w+") as fid: fid.write(yaml.dump(content))


class manPage:
    def __init__(self, package, typ, name, docstrings):
        if not isinstance(package, str):
            raise TypeError("argument `package` must be str (package name)")
        if not isinstance(typ, str):
            raise TypeError("argument `typ` must be str")
        elif not typ in ["function", "class"]:
            raise ValueError("argument `typ` must be \"function\" or \"class\"")
        if not isinstance(name, str):
            raise TypeError("argument `name` must be str (original class or function name)")

        # Store args
        self._package    = package
        self._typ        = typ
        self._name       = name
        self._docstrings = docstrings

        # Checking docstrings input
        self._check_docstrings_input(docstrings)

    def _check_docstrings_input(self, x):
        """_check_docstrings_input(x)

        Checking user input when initializing object of class manPage

        Args:
            x: dictionary of dictionaries containing the Docstring extracted
                via docstring_parser and the Signature extracted via inspect.

        Returns:
            No return, will throw errors if the user's input is incorrect.
        """
        arg = "docstrings"
        if not isinstance(x, dict):
            raise TypeError(f"argument `{arg}` must be dict")
        for key,rec in x.items():
            if not isinstance(rec, dict):
                raise TypeError(f"elements in `{arg}` must be dict")
            elif not "docstring" in rec.keys() or not "signature" in rec.keys() or not "module" in rec.keys():
                raise ValueError(f"dictionaries in `{arg}` must contain \"docstring\", \"signature\", and \"module\"")
            elif not isinstance(rec["docstring"], docstring_parser.common.Docstring):
                raise TypeError(f"\"docstring\" must inherit docstring_parser.common.Docstring")
            elif not isinstance(rec["signature"], inspect.Signature):
                raise TypeError(f"\"signature\" must inherit inspect.Signature")
            elif not isinstance(rec["module"], str):
                raise TypeError(f"\"module\" must be str")

    def get(self, attr, name = None):
        """get(attr, name = None)

        Args:
            attr (str): attribute to extract from the docstring.
            name (None, str): The function or class name for which the
                attribute should be extracted. If None: name with which
                the object has been initialized (main function/class).

        Return:
            Returns the attribute from the docstring, type depends on
            what is stored in docstring_parser.common.Docstring.
        """
        if name is None: name = self._name
        assert isinstance(name, str), "name must be string"
        assert isinstance(attr, str), "attr must be string"
        res = getattr(self._docstrings[name]["docstring"], attr)

        if attr in ["short_description", "long_description"] and res is not None:
            res = self._fix_references(res)

        return res

    def _fix_references(self, x):
        import re

        # Replace sphinx refs with quarto refs
        matches = re.findall(r":py:(?:func|class):`.*?`", x)
        for m in matches:
            tmp = re.search("`(.*?)(?=`)", m).group(1)
            x   = x.replace(m, f"[{tmp}]({tmp}.qmd)")

        return x

    def signature(self, name = None):
        """signature(name = None)

        Args:
            name (None, str): The function or class name for which the
                attribute should be extracted. If None: name with which
                the object has been initialized (main function/class).

        Return:
            (str) Returns signature as string.
        """
        if name is None: name = self._name
        assert isinstance(name, str), "attr must be string"
        return str(self._docstrings[name]["signature"]) # str(inspect.Signature)


    def fullname(self, name = None):
        """fullname(name = None)

        Args:
            name (None, str): The function or class name for which the
                attribute should be extracted. If None: name with which
                the object has been initialized (main function/class).

        Return:
            (str) Full module name/path without package name, e.g.
            `colorlib.HCL` for function `HCL` in module `colorspace.colorlib`.
        """
        if name is None: name = self._name
        assert isinstance(name, str), "attr must be string"
        res = f"{str(self._docstrings[name]['module'])}.{name}"
        return re.sub(f"^{self._package}\.", "", res)

    def _repr_args(self):
        res = "<dl class=\"pyp-list param-list\">\n"
        for arg in self.get("params"):
            short_arg = re.search("^([\*\w]+)", arg.args[1]).group(1).replace("*", "")
            # Building html table row
            res += "  <dt style = \"white-space: nowrap; font-family: monospace; vertical-align: top\">\n" + \
                   f"   <code id=\"{self._package}_:_{short_arg}\">{arg.args[1]}</code>\n" + \
                   "  </dt>\n" + \
                   f" <dd>{arg.description}</dd>\n"

        return res + "</dl>"

    def _repr_examples(self, x):
        assert isinstance(x, str)
        res = "```{python}\n" + \
              "#| echo: true\n" + \
              "#| error: true\n" + \
              "#| warning: true\n" + \
              x + \
              "\n```\n\n"
        return res

    def _prepare_example(self, x):
        """prepapre_example(x)
 
        Args:
            x (str): The example extracted from the docstring.
 
        Return:
        str : Modified example to be ready for quarto.
        """
        # Comment 'text' (can be included in the py example section)
        x = re.sub(r"^(?!(>>>))", "## ", x, flags = re.MULTILINE)
        # Removing empty lines
        x = re.sub(r"^##\s+?$", "", x, flags = re.MULTILINE)
        # Remove >>> code identifiers
        x = re.sub(r"^>>>\s+?", "", x, flags = re.MULTILINE)
        return x
 
    def _split_example(self, x):
        """split_example(x)
 
        Args:
            x: str, the example extracted from the docstring.
 
        Return:
        list: List of strings. If we find `#:` at the start of a line
        we split the example at this position in multiple segments.
        """
        return re.split(r"\n(?=#:)", x, flags = re.MULTILINE)

    def __repr__(self):
        if self.get("short_description") is None:
            res  = "## WARNING(short_description missing) {.unnumbered}\n\n"
        else:
            res  = "## " + self.get("short_description") + " {.unnumbered}\n\n"

        if self.get("long_description"):
            res += "### Description\n\n"
            res += self.get("long_description")
        #else:
        #    res += "WARNING(long_description missing)"

        res += "\n\n### Usage\n\n"
        res += "<pre><code class='language-python'>" + \
               f"{self.fullname()}{self.signature()}" + \
               "</code></pre>"

        # Function arguments
        res += "\n\n### Arguments\n\n"
        res += self._repr_args()

        # Return value
        if self.get("returns"):
            res += "\n\n### Return\n\n"
            res += f"{self.get('returns').description}"

        # If is class, append methods
        if self._typ == "class" and len(self._docstrings) > 1:

            res += "\n\n### Methods\n\n"

            res += "<dl class=\"pyp-list method-list\">\n"
            for key,rec in self._docstrings.items():
                # Skipping main class (else infinite recursion)
                if key == self._name: continue
                link = ".".join([self.fullname(), re.search(r"[^.]+$", key).group(0)]) + ".qmd"
                res += "    <dt style = \"white-space: nowrap; font-family: monospace; vertical-align: top\">\n" + \
                       f"       <code>[{key}{self.signature(key)}]({link})</code>\n    </dt>\n"
                tmp = self.get('short_description', key)
                if tmp is None:
                    tmp = "WARNING(short_description missing)"
                else:
                    tmp = re.sub(f"^{key}", "", tmp)
                res += f"    <dd>{tmp}</dd>\n"
            res += "</dl>\n"

 
        # If we have examples:
        if self.get("examples"):
            examples = []
            for tmp in [ex.description for ex in self.get("examples")]:
                # Prepare example and possibly split it.
                tmp       = self._prepare_example(tmp)
                examples += self._split_example(tmp)

            
            res += "\n\n### Examples\n\n"
            for tmp in examples:
                res += self._repr_examples(tmp)
            res += "\n"
 
        return res

# Testing a function
def py2quarto(obj, package, include_hidden = False):
    """py2quarto(obj)

    Args:
        obj: function or class.
        package (str): name of the package for which the documentation
            is created.
        include_hidden (bool): Defaults to `False`. If set,
            hidden functions and methods (_*, __*) will also
            be documented.
    """

    if not inspect.isfunction(obj) and not inspect.isclass(obj):
        raise TypeError("argument `obj` must be a function or class")
    if not isinstance(package, str):
        raise TypeError("argument `package` must be str")
    if not isinstance(include_hidden, bool):
        raise TypeError("argument `include_hidden` must be boolean True or False")

    def extract_docstrings(obj, parent, style, include_hidden):
        if not parent is None and not isinstance(parent, manPage):
            raise TypeError("argument `parent` must be None or a of class manPage")
        dstyle = getattr(docstring_parser.DocstringStyle, style.upper())

        # Extract class docstring
        docstrings = {}

        # If parent is None, extract docstring of main function or class.
        if parent is None:
            class_docstring = docstring_parser.parse(inspect.getdoc(obj), dstyle)
            if class_docstring:
                module = re.sub(f"^{package}\.", "", obj.__module__)
                docstrings[obj.__name__] = {"docstring": class_docstring,
                                            "signature": inspect.signature(obj),
                                            "module":    obj.__module__}

        # If parent is a class object we extractt he members of that object,
        # i.e., the methods of a class. Only meaningful for classes, obviously.
        else:
            # Extract method/function docstrings
            for name,func in get_members(obj).items():

                name = re.search(r"[^.]+$", name).group(0)
                if not include_hidden and name.startswith("_"): continue

                # Else check if is function
                if inspect.isfunction(func):
                    try:
                        doc = docstring_parser.parse(inspect.getdoc(func), dstyle)
                    except Exception as e:
                        print(f"Problem extracting docstring from:   {func.__name__} ({name})")
                        raise Exception(e)

                    # Setting up the displayed name for the manuals; a combination
                    # of the parent `obj` and the visible name of the function.
                    fn_name = ".".join([parent.fullname(), func.__name__])

                    fn_module = re.sub(f"^{package}\.", "", obj.__module__)
                    docstrings[fn_name] = {"docstring": doc,
                                           "signature": inspect.signature(func),
                                           "module":    ".".join([func.__module__, obj.__name__])}

                    # For this function (method) we'll also write 
                    # a qmd page, tough it will not be added/included
                    # in the navigation.
                    fn_man = py2quarto(func, package, args.include_hidden)
                    print(f"[DEVEL]     - adding man page for method {fn_man.fullname()}")
                    fn_qmdfile = os.path.join(args.output_dir, args.man_dir,
                                              f"{fn_name}.qmd")
                                              #f"{fn_fullname()}.qmd")
                    print(f"              {fn_qmdfile}")
                    with open(fn_qmdfile, "w+") as fid: print(fn_man, file = fid)

        return docstrings

    docstrings = extract_docstrings(obj, None, args.docstringstyle, include_hidden)

    # Generate manPage object
    u = manPage(package    = args.package,
                typ        = "function" if inspect.isfunction(obj) else "class",
                name       = obj.__name__,
                docstrings = docstrings)

    if inspect.isclass(obj):
        docstrings = extract_docstrings(obj, u, args.docstringstyle, include_hidden)
        sys.exit(333)

    # Returning object of class manPageFunction or manPageClass
    return u

def get_members(pkg, predicate = None):
    from inspect import getmembers
    result = {}
    # Extract all members (given predicate) which have
    # a __qualname__ (functions, classes), the rest will be ignored
    for rec in getmembers(pkg, predicate):
        try:
            result[".".join([rec[1].__module__, rec[1].__qualname__])] = rec[1]
        except:
            pass
    return result

# -------------------------------------------------
# -------------------------------------------------
if __name__ == "__main__":

    # Parsing user args
    args = parse_input_args()

    # If args.action is init, crate _quarto.yml
    yml_newly_created = create_quarto_yml(args)

    # Wirte sass (if not existing _or_ action = "init")
    write_sass(args)
    # Write index (if not existing)
    write_index(args)

    # Trying to import the module
    try:
        pkg = import_module(args.package)
    except Exception as e:
        raise Exception(e)

    # Extracting functions and classes
    import inspect
    functions = get_members(pkg, inspect.isfunction)
    classes   = get_members(pkg, inspect.isclass)

    ##print(f"{functions.keys()=}")
    ##print(f"{classes.keys()=}")
    ##print("\n\n")

    #f_test = py2quarto(functions[list(functions.keys())[3]], args.package)
    #c_test = py2quarto(classes[list(classes.keys())[3]], args.package)
    #sys.exit(" --- uuuuuuu --- ")

    # -------------------------------------------------
    # Create man pages for functions
    # -------------------------------------------------
    man_func_created = {}
    for key,fun in functions.items():
        print(f"[DEVEL] Create man page function {key}")
        man     = py2quarto(fun, args.package, args.include_hidden)
        qmdfile = os.path.join(args.output_dir, args.man_dir, f"{man.fullname()}.qmd")
        with open(qmdfile, "w+") as fid:
            print(man, file = fid)
        man_func_created[key] = f"{args.man_dir}/{os.path.basename(qmdfile)}"
    #print(f"{man_func_created=}")
    print(f"Number of function manuals created: {len(man_func_created)}")

    # Adding Function references to _quarto.yml
    if yml_newly_created and len(man_func_created) > 0:
        update_quarto_yml(args, "Function reference", man_func_created)


    # -------------------------------------------------
    # Create man pages for classtions
    # -------------------------------------------------
    man_class_created = {}
    for key,cls in classes.items():
        print(f"[DEVEL] Create man page class {key}")
        man     = py2quarto(cls, args.package, args.include_hidden)
        qmdfile = os.path.join(args.output_dir, args.man_dir, f"{man.fullname()}.qmd")
        with open(qmdfile, "w+") as fid:
            print(man, file = fid)

        man_class_created[key] = f"{args.man_dir}/{os.path.basename(qmdfile)}"
    #print(f"{man_class_created=}")
    print(f"Number of class manuals created: {len(man_class_created)}")

    #test = py2quarto(clss[1])
    #print(test)

    # Adding Function references to _quarto.yml
    if yml_newly_created and len(man_class_created) > 0:
        update_quarto_yml(args, "Class reference", man_class_created)

