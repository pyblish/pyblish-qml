import os
import re

exclude = "\.py$"


def parse():
    template = """<!DOCTYPE RCC><RCC version="1.0">
    <qresource>
%s
    </qresource>
</RCC>"""

    base = r"pyblish_qml\qml"
    qrc_files = []
    for root, dirs, files in os.walk(base):
        for f in files:
            if re.findall(exclude, f):
                continue

            qrc_files.append(os.path.join(root[len(base) + 1:], f))

    return template % "\n".join(("\t\t<file>%s</file>" % f for f in qrc_files))


def write(qrc):
    with open("resources.qrc", "w") as f:
        f.write(qrc)


if __name__ == '__main__':
    write(parse())
