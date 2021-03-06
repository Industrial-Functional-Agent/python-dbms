from lark.lexer import Token
from lark.tree import Tree


class CreateTable:
    """
    CREATE TABLE [IF NOT EXISTS] tbl_name (create_definition,...)
    """
    def __init__(self, is_if_not_exist, tbl_name, create_definitions):
        self.is_if_not_exist = is_if_not_exist
        self.tbl_name = tbl_name
        self.create_definitions = create_definitions

    @staticmethod
    def parse_create_table(tree):
        is_if_not_exist = len([c for c in tree.children if type(c) is Token and c.type == 'IF']) > 0
        tbl_name = next(c.value for c in tree.children if type(c) is Token and c.type == 'ID')
        create_definitions = [CreateDefinition.parse_create_definition(c)
                              for c in tree.children
                              if type(c) is Tree and c.data == 'create_definition']
        return CreateTable(is_if_not_exist, tbl_name, create_definitions)


class CreateDefinition:
    """
    create_definition:
        col_name column_definition
        PRIMARY KEY [index_type] (index_col_name,...) [index_option] ...
        UNIQUE [INDEX|KEY] [index_name] [index_type] (index_col_name,...) [index_option] ...
        FOREIGN KEY [index_name] (index_col_name,...) reference_definition
    """

    @classmethod
    def parse_create_definition(cls, tree):
        if tree.children[0].type == 'ID':
            col_name = next(c.value for c in tree.children if type(c) is Token and c.type == 'ID')
            column_definition = next(ColumnDefinition.parse_column_definition(c)
                                     for c in tree.children
                                     if type(c) is Tree and c.data == 'column_definition')
            return Column(col_name, column_definition)
        elif tree.children[0].type == 'PRIMARY':
            index_type = next((cls.parse_index_type(c) for c in tree.children
                              if type(c) is Tree and c.data == 'index_type'),
                              'btree')
            index_col_names = [cls.parse_index_col_name(c) for c in tree.children
                               if type(c) is Tree and c.data == 'index_col_name']
            return PrimaryKey(index_type, index_col_names)
        elif tree.children[0].type == 'UNIQUE':
            index_name = next(c.value for c in tree.children if type(c) is Token and c.type == 'ID')
            index_type = next((cls.parse_index_type(c) for c in tree.children
                              if type(c) is Tree and c.data == 'index_type'),
                              'btree')
            index_col_names = [cls.parse_index_col_name(c) for c in tree.children
                               if type(c) is Tree and c.data == 'index_col_name']
            return Unique(index_name, index_type, index_col_names)
        elif tree.children[0].type == "FOREIGN":
            index_name = next((c.value for c in tree.children
                               if type(c) is Token and c.type == 'ID'),
                              None)
            index_col_names = [cls.parse_index_col_name(c) for c in tree.children
                               if type(c) is Tree and c.data == 'index_col_name']
            reference_definition = next(c for c in tree.children
                                        if type(c) is Tree and c.data == "reference_definition")
            return ForeignKey(index_name, index_col_names,
                              cls.parse_reference_definition(reference_definition))
        else:
            raise RuntimeError("Not proper syntax: {}".format(tree))

    @staticmethod
    def parse_index_type(tree):
        return tree.children[1].value  # btree | hash

    @staticmethod
    def parse_index_col_name(tree):
        return tree.children[0].value

    @classmethod
    def parse_reference_definition(cls, tree):
        tbl_name = next(c.value for c in tree.children if type(c) is Token and c.type == 'ID')
        index_col_names = [cls.parse_index_col_name(c) for c in tree.children
                           if type(c) is Tree and c.data == 'index_col_name']
        idx_delete = next((idx for idx, c in enumerate(tree.children)
                           if type(c) is Token and c.type == 'DELETE'),
                          None)
        idx_update = next((idx for idx, c in enumerate(tree.children)
                           if type(c) is Token and c.type == 'UPDATE'),
                          None)
        on_delete_reference_option = None
        on_update_reference_option = None
        if idx_delete is not None:
            on_delete_reference_option = cls.parse_reference_option(tree.children[idx_delete + 1])
        if idx_update is not None:
            on_update_reference_option = cls.parse_reference_option(tree.children[idx_update + 1])
        return ReferenceDefinition(tbl_name, index_col_names,
                                   on_delete_reference_option, on_update_reference_option)

    @staticmethod
    def parse_reference_option(tree):
        return "_".join(tree.children)  # e.g. SET_NULL


class Column(CreateDefinition):
    def __init__(self, col_name, column_definition):
        self.col_name = col_name
        self.column_definition = column_definition


class ColumnDefinition:
    """
    column_definition:
        data_type [NOT NULL | NULL] [DEFAULT default_value] [AUTO_INCREMENT]
    """
    def __init__(self, data_type, allow_null=True, default=None, is_auto_increment=False):
        self.data_type = data_type
        self.allow_null = allow_null
        self.default = default
        self.is_auto_increment = is_auto_increment

    @classmethod
    def parse_column_definition(cls, tree):
        assert tree.data == "column_definition"

        data_type = DataType.parse_data_type(tree.children[0])
        remainder = tree.children[1:]
        allow_null = cls.parse_allow_null(remainder)
        default = cls.parse_default(remainder)
        is_auto_increment = cls.parse_is_auto_increment(remainder)

        return ColumnDefinition(data_type, allow_null, default, is_auto_increment)

    @staticmethod
    def parse_allow_null(children):
        return len([token for token in children if token.type == "NOT"]) == 0

    @staticmethod
    def parse_default(children):
        indexes = [i for i, j in enumerate(children) if j.type == "DEFAULT"]
        if len(indexes) == 0:
            return None
        else:
            token = children[indexes[0] + 1]
            assert token.type in ['STRING', 'NUMBER'], "Unsupported default token: " + repr(token)
            return token.value if token.type == 'STRING' else int(token.value)

    @staticmethod
    def parse_is_auto_increment(children):
        return len([token for token in children if token.type == "AUTO_INCREMENT"]) > 0


class DataType:
    def __init__(self, name, fsp=None, length=None, character_set=None, collate=None, values=None):
        self.name = name
        self.fsp = fsp
        self.length = length
        self.character_set = character_set
        self.collate = collate
        self.values = values

    @classmethod
    def parse_data_type(cls, tree):
        assert tree.data == "data_type"

        name = cls.parse_name(tree.children[0])
        number = cls.parse_number(tree)
        fsp = number if name in ['TIME', 'TIMESTAMP', 'DATETIME'] else None
        length = number if name == 'TEXT' else None
        character_set = cls.parse_character_set(tree)
        collate = cls.parse_collate(tree)
        values = cls.parse_values(tree)

        return DataType(name, fsp, length, character_set, collate, values)

    @staticmethod
    def parse_name(child):
        if type(child) is Token:
            return child.type
        elif type(child) is Tree:
            if child.data == "enum":
                return "ENUM"
            elif child.data == "set":
                return "SET"
        raise RuntimeError("Not proper syntax: {}".format(child))

    @staticmethod
    def parse_number(tree):
        indexes = [i for i, j in enumerate(tree.children)
                   if type(j) is Token and j.type == 'NUMBER']
        return int(tree.children[indexes[0]].value) if len(indexes) > 0 else None

    @staticmethod
    def parse_character_set(tree):
        indexes = [i for i, j in enumerate(tree.children)
                   if type(j) is Token and j.type == "CHARACTER"]
        return tree.children[indexes[0] + 2].value if len(indexes) > 0 else None

    @staticmethod
    def parse_collate(tree):
        indexes = [i for i, j in enumerate(tree.children)
                   if type(j) is Token and j.type == "COLLATE"]
        return tree.children[indexes[0] + 1].value if len(indexes) > 0 else None

    @staticmethod
    def parse_values(tree):
        if type(tree.children[0]) is Token:
            return None
        elif type(tree.children[0]) is Tree:
            if tree.children[0].data in ["enum", "set"]:
                return [t.value.strip('\'') for t in tree.children[0].children[1:]]
        raise RuntimeError("Not proper syntax: {}".format(tree))


class PrimaryKey(CreateDefinition):
    """
    PRIMARY KEY [index_type] (index_col_name,...) [index_option] ...
    index_option 은 어려워보여서 일단 스킵...
    """
    def __init__(self, index_type, index_col_names):
        self.index_type = index_type
        self.index_col_names = index_col_names


class Unique(CreateDefinition):
    """
    UNIQUE[INDEX | KEY] [index_name][index_type](index_col_name, ...) [index_option]...
    index_option 은 어려워보여서 일단 스킵...
    """
    def __init__(self, index_name, index_type, index_col_names):
        self.index_name = index_name
        self.index_type = index_type
        self.index_col_names = index_col_names


class ForeignKey(CreateDefinition):
    """
    FOREIGN KEY[index_name](index_col_name, ...) reference_definition
    """
    def __init__(self, index_name, index_col_names, reference_definition):
        self.index_name = index_name
        self.index_col_names = index_col_names
        self.reference_definition = reference_definition


class ReferenceDefinition:
    """
    reference_definition:
        REFERENCES tbl_name (index_col_name,...)
        [ON DELETE reference_option]
        [ON UPDATE reference_option]
    """
    def __init__(self, tbl_name, index_col_names,
                 on_delete_reference_option, on_update_reference_option):
        self.tbl_name = tbl_name
        self.index_col_names = index_col_names
        self.on_delete_reference_option = on_delete_reference_option
        self.on_update_reference_option = on_update_reference_option
