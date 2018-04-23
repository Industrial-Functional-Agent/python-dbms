from models import CreateTable


def parse_tree(tree):
    if tree.data == "sql":
        t = tree.children[0]
        if t.data == "ddl":
            t = t.children[0]
            if t.data == "create_table":
                return CreateTable.parse_create_table(t)
    raise RuntimeWarning("invalid tree {}".format(tree))
