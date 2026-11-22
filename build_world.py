"""Compile the map query and grid-search accelerators."""

from Cython.Build import cythonize
from setuptools import Extension, setup

setup(
    name="campus_geometry",
    ext_modules=cythonize(
        [
            Extension(
                "spatial", ["spatial.pyx"], language="c++", extra_compile_args=["-O3", "-ffp-contract=off"]
            )
        ],
        compiler_directives={"language_level": 3},
    ),
)
