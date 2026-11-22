"""Arithmetic and library operations used by the translated controller."""

import functools
import math
import os
import struct
import sys


_f32 = struct.Struct("=f")


def go_f32(value):
    return _f32.unpack(_f32.pack(value))[0]


def go_len(value):
    return 0 if value is None else len(value)


def go_div(a, b):
    if b:
        return a / b
    if not a or math.isnan(a):
        return math.nan
    return math.copysign(math.inf, a) * math.copysign(1, b)


def go_intdiv(a, b):
    quotient = abs(a) // abs(b)
    return -quotient if (a < 0) != (b < 0) else quotient


def go_remainder(a, b):
    return a - go_intdiv(a, b) * b


def go_intcast(value, width):
    value = int(value)
    sign = 1 << (width - 1)
    return ((value + sign) % (sign * 2)) - sign


def go_inf(sign):
    return -math.inf if sign < 0 else math.inf


def go_isinf(x, sign):
    return math.isinf(x) and (sign == 0 or (sign > 0) == (x > 0))


def go_nan():
    return math.nan


def go_string(value):
    return bytes(value).decode("utf-8", "surrogateescape")


def go_copy(destination, source):
    n = min(len(destination), len(source))
    destination[:n] = source[:n]
    return n


def go_getenv(name):
    return os.getenv(name, "")


def go_Contains(string, substring):
    return substring in string


def go_Sprintf(fmt, *args):
    # The controller's trace labels use simple numeric, string and Go %v formats.
    return fmt.replace("%v", "%s") % args


def go_Fprintf(file, fmt, *args):
    return file.write(go_Sprintf(fmt, *args))


def go_SliceStable(items, less):
    def compare(a, b):
        if less(a, b):
            return -1
        if less(b, a):
            return 1
        return 0

    indexes = sorted(range(len(items)), key=functools.cmp_to_key(compare))
    items[:] = [items[i] for i in indexes]


go_Slice = go_SliceStable


class GoOnce:
    def __init__(self):
        self.done = False

    def Do(self, func):
        if not self.done:
            self.done = True
            func()
