"""Minimal S-expression reader/writer for KiCad files."""
import re

class Sym(str):
    """Bare symbol token (unquoted)."""
    __slots__ = ()

_tok = re.compile(r'\s*(?:(\()|(\))|"((?:[^"\\]|\\.)*)"|([^\s()"]+))', re.S)

def parse(text):
    pos = 0; stack = [[]]
    n = len(text)
    while pos < n:
        m = _tok.match(text, pos)
        if not m:
            break
        pos = m.end()
        if m.group(1):
            stack.append([])
        elif m.group(2):
            lst = stack.pop(); stack[-1].append(lst)
        elif m.group(3) is not None:
            escapes = {'n': '\n', 'r': '\r', 't': '\t', '"': '"', '\\': '\\'}
            stack[-1].append(re.sub(r'\\([nrt"\\])', lambda match: escapes[match[1]], m.group(3)))
        elif m.group(4) is not None:
            stack[-1].append(Sym(m.group(4)))
        else:
            break
    return stack[0]

def _fmt_atom(a):
    if isinstance(a, Sym):
        return str(a)
    if isinstance(a, bool):
        return 'yes' if a else 'no'
    if isinstance(a, int):
        return str(a)
    if isinstance(a, float):
        s = ('%.6f' % a).rstrip('0').rstrip('.')
        return s if s not in ('-0', '') else '0'
    s = str(a).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
    return '"%s"' % s

def dump(node, indent=0):
    """Serialize a nested list to KiCad-style text."""
    if not isinstance(node, list):
        return _fmt_atom(node)
    if not node:
        return '()'
    # short lists on one line if all atoms
    if all(not isinstance(x, list) for x in node):
        return '(' + ' '.join(_fmt_atom(x) for x in node) + ')'
    pad = '\t' * indent
    out = '(' + ' '.join(_fmt_atom(x) for x in node[:1])
    first_list = True
    i = 1
    while i < len(node) and not isinstance(node[i], list):
        out += ' ' + _fmt_atom(node[i]); i += 1
    for x in node[i:]:
        if isinstance(x, list):
            out += '\n' + pad + '\t' + dump(x, indent + 1)
        else:
            out += ' ' + _fmt_atom(x)
    out += '\n' + pad + ')'
    return out

def find(node, key):
    """First child list whose head == key."""
    for x in node:
        if isinstance(x, list) and x and x[0] == key:
            return x
    return None

def find_all(node, key):
    return [x for x in node if isinstance(x, list) and x and x[0] == key]

def S(*args):
    """Build node: S('at', 1, 2) -> [Sym('at'), 1, 2]"""
    return [Sym(args[0])] + list(args[1:])
