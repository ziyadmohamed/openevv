#!/usr/bin/env python3
"""A language's alphabet, and what each character of it is.

The alphabet is the value names of the input statement's first field, and
beside it in the same statement is a record for every one of those names: what
case the character is, whether it is a letter or a digit or punctuation,
whether it is a vowel or a consonant or a glide, whether it carries an accent,
and the phoneme it stands for on its own. Which is letter-to-sound at its
simplest, and it is data rather than code.

Both are in `lang/<tag>/<tag>.statements`, the alphabet as `value' lines and
the records as the `variants' bytes of the same statement -- one record of five
bytes per name, in the order the names are in. Reading those bytes by eye and
writing them by hand is how a letter quietly comes out as a digit, so this
reads and writes them by name.

    tools/module/alphabet.py show <tag>              every character and what it is
    tools/module/alphabet.py show <tag> <char>...    only the ones named
    tools/module/alphabet.py add <tag> <byte> <field>=<value>...
    tools/module/alphabet.py set <tag> <byte> <field>=<value>...

`add' puts a character at a byte value nothing in the alphabet claims yet, so
that no existing code changes meaning: the dictionaries are keyed by these
codes and moving one would move every word that used it. The byte is what the
engine will see for that character once it arrives, in hex.

    tools/module/alphabet.py add plpl b1 case=lower type=letter letter=vow \\
                              accent='~yes' phoneme=a

`set' rewrites the record of a byte the alphabet already claims, leaving its
name and every other byte's code exactly where it is -- no line moves, so
nothing that keyed on a code shifts under it. It is how a slot that used to
mean one letter comes to mean another: a language built on a chassis whose
alphabet it does not want reuses those slots for its own letters rather than
renumbering the lot. Whatever code points arrive as that byte are then its
new letter's, which is `<tag>.codepoints' work.

    tools/module/alphabet.py set ukua c0 case=lower type=letter letter=vow \\
                              accent='~yes' phoneme=a

usage: as above; `show' with no character lists the lot
"""

import os
import sys

# tools/evv.py says where the tree is, so that no tool counts directories to
# find it. The one thing this line has to know is that the directory above a
# tool's group is tools itself.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from evv import ROOT

# Which statement holds the characters, and the five fields a record carries
# in the order they sit in it.
STATEMENT = "inp"
RECORD = ("case", "type", "letter", "accent", "phoneme")
# What each of those is called in the statement itself.
FIELD = {"case": "letcase", "type": "character_type", "letter": "letter_type",
         "accent": "accent", "phoneme": "phon_form"}


def path_of(tag):
    return os.path.join(ROOT, "lang", tag, "%s.statements" % tag)


def read(tag):
    """The statement's lines, its alphabet, its field values and its records.

    The file is kept as its lines so that writing it back changes only what
    was asked for: everything else, including every other statement, goes
    back exactly as it came.
    """
    lines = open(path_of(tag)).read().split("\n")
    first = last = None
    names = []
    values = {}
    field = None
    variants = bytearray()
    var_at = []

    for i, line in enumerate(lines):
        if line == "statement %s" % STATEMENT:
            first = i
            continue
        if first is not None and last is None:
            if line.startswith("statement ") or line == "end":
                last = i
                continue
            w = line.split()
            if line.startswith("  field "):
                field = w[1]
                values.setdefault(field, [])
            elif line.startswith("    value") and field:
                text = line[len("    value"):]
                text = text[1:] if text.startswith(" ") else text
                text = text.replace("\\s", " ").replace("\\\\", "\\")
                values[field].append(text)
                if field == "name":
                    names.append(text)
            elif w and w[0] == "variants":
                var_at.append(i)
                variants += bytes(int(x, 16) for x in w[1:])
    if first is None:
        raise SystemExit("module/alphabet: %s has no %s statement"
                         % (tag, STATEMENT))
    return lines, first, last, names, values, bytes(variants), var_at


def named(values, field, v):
    table = values.get(FIELD[field], [])
    return table[v] if 0 <= v < len(table) else str(v)


def number(values, field, text):
    table = values.get(FIELD[field], [])
    if text in table:
        return table.index(text)
    raise SystemExit("module/alphabet: %s has no %s called %r"
                     % (FIELD[field], field, text))


def show(tag, want):
    _l, _f, _t, names, values, variants, _at = read(tag)
    print("%s: %d characters, %d bytes of records"
          % (tag, len(names), len(variants)))
    for code, ch in enumerate(names):
        if want and ch not in want:
            continue
        r = variants[code * 5:code * 5 + 5]
        if len(r) < 5:
            print("%3d  %-4s no record" % (code, ch))
            continue
        print("%3d  %-4s %-6s %-6s %-5s %-5s says %s"
              % (code, ch if ch.strip() else "' '",
                 named(values, "case", r[0]), named(values, "type", r[1]),
                 named(values, "letter", r[2]), named(values, "accent", r[3]),
                 named(values, "phoneme", r[4])))
    return True


def add(tag, byte, args):
    lines, first, last, names, values, variants, var_at = read(tag)
    want = want_of(args)

    ch = bytes([int(byte, 16)]).decode("latin-1")
    if ch in names:
        raise SystemExit("module/alphabet: %s already has that character, as"
                         " code %d" % (tag, names.index(ch)))
    if len(variants) != len(names) * 5 + 5:
        raise SystemExit("module/alphabet: %d names and %d bytes of records is"
                         " not one record each" % (len(names), len(variants)))

    record = bytes(number(values, k, want[k]) for k in RECORD)
    written = ch.replace("\\", "\\\\").replace(" ", "\\s")

    # The name goes after the last one of the field it belongs to, and the
    # record after the last of the records, so every code that exists keeps
    # the meaning it had.
    at_name = max(i for i in range(first, last)
                  if lines[i].startswith("    value")
                  and i < min([j for j in range(first, last)
                               if lines[j].startswith("  field ")
                               and lines[j].split()[1] != "name"]
                              or [last]))
    lines.insert(at_name + 1, "    value %s" % written)

    at_var = max(j for j in var_at) + 1        # the line after the last one
    lines.insert(at_var, "  variants %s"
                 % " ".join("%02x" % b for b in record))

    open(path_of(tag), "w").write("\n".join(lines))
    print("%s: %s is code %d now, %s"
          % (tag, ch, len(names),
             ", ".join("%s %s" % (k, want[k]) for k in RECORD)))
    return True


def want_of(args):
    """The five field values a record needs, from field=value arguments."""
    want = {}
    for a in args:
        if "=" not in a:
            raise SystemExit("module/alphabet: %r is not field=value" % a)
        k, v = a.split("=", 1)
        if k not in RECORD:
            raise SystemExit("module/alphabet: a record has no %r; it has %s"
                             % (k, ", ".join(RECORD)))
        want[k] = v
    for k in RECORD:
        if k not in want:
            raise SystemExit("module/alphabet: say what its %s is" % k)
    return want


def set_(tag, byte, args):
    lines, first, last, names, values, variants, var_at = read(tag)
    want = want_of(args)

    ch = bytes([int(byte, 16)]).decode("latin-1")
    if ch not in names:
        raise SystemExit("module/alphabet: %s has no character at byte %s to"
                         " set; `add' puts one there" % (tag, byte))
    code = names.index(ch)
    if (code + 1) * 5 > len(variants):
        raise SystemExit("module/alphabet: %s has %d bytes of records, too few"
                         " for code %d" % (tag, len(variants), code))

    # A record straddles the variants lines -- they hold many bytes each, not
    # one record apiece -- so splice the five bytes into the flat array and
    # lay it back out over the very same lines, each keeping its own length.
    record = bytes(number(values, k, want[k]) for k in RECORD)
    flat = bytearray(variants)
    flat[code * 5:code * 5 + 5] = record
    at = 0
    for i in var_at:
        n = len(lines[i].split()) - 1
        lines[i] = "  variants %s" % " ".join("%02x" % b for b in flat[at:at + n])
        at += n

    open(path_of(tag), "w").write("\n".join(lines))
    print("%s: code %d (byte %s) is %s now"
          % (tag, code, byte,
             ", ".join("%s %s" % (k, want[k]) for k in RECORD)))
    return True


def main(argv):
    if len(argv) < 2:
        print(__doc__.strip())
        return 2
    what, tag = argv[0], argv[1]
    if what == "show":
        return 0 if show(tag, set(argv[2:])) else 1
    if what == "add" and len(argv) > 2:
        return 0 if add(tag, argv[2], argv[3:]) else 1
    if what == "set" and len(argv) > 2:
        return 0 if set_(tag, argv[2], argv[3:]) else 1
    print(__doc__.strip())
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
