


def demofun_allfine(x = "demo", *args, **kwargs):
    """Demo Function: All fine

    This function is used for testing/demonstrating the
    :py:class:`DocConverter <pyp2qmd.DocConverter.DocConverter>`.
    Docstring all fine, properly includes a title, description, all arguments
    are documented as well as the (dummy) return and exceptions rased.

    Args:
        x (str): Dummy input argument, defaults to \"demo\".
        *args: Takes up all unnamed input arguments, unused.
        **kwargs: Takes up all named arguments, unused.

    Returns:
        str: Simply returns `x` at the end.

    Raises:
        TypeError: If argument `x` is not str.
    """
    if not isinstance(x, str):
        raise TypeError("argument `x` is not str")

    return x


def demofun_wrong(x = "demo", *args, **kwargs):
    """Demo Function: Invalid Docstring

    This function is used for testing/demonstrating the
    :py:class:`DocConverter <pyp2qmd.DocConverter.DocConverter>`.
    Docstring not properly specified, missing documentation for arguments,
    and return.
    """
    if not isinstance(x, str):
        raise TypeError("argument `x` is not str")

    return x


def demofun_wrong2(x = "demo", *args, **kwargs):
    """
    """
    if not isinstance(x, str):
        raise TypeError("argument `x` is not str")

    return x

