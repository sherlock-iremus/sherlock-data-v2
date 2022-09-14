import json
from lxml import etree
import re
import sys

tree = etree.parse(sys.argv[1])
root = tree.getroot()


def clean_text(t):
    if t:
        return re.sub(r"[\n]*", "", t)
    return ""


def explore(node, path):
    n_text = 1
    n_nodes = {}

    children = []
    if node.text:
        children.append(
            {
                "id": "/" + "/".join([*path, f"text()[{n_text}]"]),
                "text": clean_text(node.text),
            }
        )
        n_text += 1
    for child in node:
        if child.xpath("local-name()") not in n_nodes:
            n_nodes[child.xpath("local-name()")] = 0
        n_nodes[child.xpath("local-name()")] += 1
        c = {
            "id": "/"
            + "/".join(
                [
                    *path,
                    child.xpath("local-name()")
                    + f"[{n_nodes[child.xpath('local-name()')]}]",
                ]
            ),
            "tag": child.xpath("local-name()"),
            "children": explore(
                child,
                [
                    *path,
                    child.xpath("local-name()")
                    + f"[{n_nodes[child.xpath('local-name()')]}]",
                ],
            ),
        }
        if child.attrib:
            c["attributes"] = dict(child.attrib)
        children.append(c)
        if child.tail:
            children.append(
                {
                    "id": "/" + "/".join([*path, f"text()[{n_text}]"]),
                    "text": clean_text(child.tail),
                }
            )
            n_text += 1

    return children


with open(sys.argv[2], "w", encoding="utf-8") as outfile:
    json.dump(
        {
            "id:": "/" + root.xpath("local-name()") + "[1]",
            "tag": root.xpath("local-name()"),
            "attributes": dict(root.attrib),
            "children": explore(root, [root.xpath("local-name()") + "[1]"]),
        },
        outfile,
        ensure_ascii=False,
    )
