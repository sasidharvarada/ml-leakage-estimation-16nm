"""Output folders per run variant. Default (rail) keeps the original paths;
--no-rail writes to a no_rail/ subfolder of each output category."""
import os


def subdir(no_rail):
    return "no_rail" if no_rail else ""


def out(base, no_rail, *parts):
    return os.path.join(base, subdir(no_rail), *parts)