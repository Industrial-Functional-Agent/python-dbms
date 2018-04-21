from models import CreateTable


def parse_tree(tree):
    if tree.data == "create":
        return CreateTable.parse_create(tree)
