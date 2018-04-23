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

    @classmethod
    def parse_create_table(cls, tree):
        is_if_not_exist = len([c for c in tree.children if type(c) is Token and c.type == 'IF']) > 0
        tbl_name = next(c.value for c in tree.children if type(c) is Token and c.type == 'ID')
        create_definitions = [CreateDefinition.parse_create_definition(c)
                              for c in tree.children
                              if type(c) is Tree and c.data == 'create_definition']
        return cls(is_if_not_exist, tbl_name, create_definitions)


class CreateDefinition:
    """
    create_definition:
        col_name column_definition
        PRIMARY KEY [index_type] (index_col_name,...) [index_option] ...
        UNIQUE [INDEX|KEY] [index_name] [index_type] (index_col_name,...) [index_option] ...
        FOREIGN KEY [index_name] (index_col_name,...) reference_definition
    """

    @staticmethod
    def parse_create_definition(tree):
        if tree.children[0].type == 'ID':
            col_name = next(c.value for c in tree.children if type(c) is Token and c.type == 'ID')
            column_definition = next(ColumnDefinition.parse_column_definition(c)
                                     for c in tree.children
                                     if type(c) is Tree and c.data == 'column_definition')
            return Column(col_name, column_definition)
        elif tree.children[0].type == 'PRIMARY':
            index_type = next((CreateDefinition.parse_index_type(c) for c in tree.children
                              if type(c) is Tree and c.data == 'index_type'),
                              'btree')
            index_col_names = [CreateDefinition.parse_index_col_name(c) for c in tree.children
                               if type(c) is Tree and c.data == 'index_col_name']
            return PrimaryKey(index_type, index_col_names)
        elif tree.children[0].type == 'UNIQUE':
            index_name = next(c.value for c in tree.children if type(c) is Token and c.type == 'ID')
            index_type = next((CreateDefinition.parse_index_type(c) for c in tree.children
                              if type(c) is Tree and c.data == 'index_type'),
                              'btree')
            index_col_names = [CreateDefinition.parse_index_col_name(c) for c in tree.children
                               if type(c) is Tree and c.data == 'index_col_name']
            return Unique(index_name, index_type, index_col_names)
        elif tree.children[0].type == "FOREIGN":
            pass
        else:
            raise SyntaxError("Not proper token: {}".format(tree.children[0]))

    @classmethod
    def parse_index_type(cls, tree):
        return tree.children[1].value  # btree | hash

    @classmethod
    def parse_index_col_name(cls, tree):
        return tree.children[0].value

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

    @staticmethod
    def parse_column_definition(tree):
        assert tree.data == "column_definition"

        data_type = DataType.parse_data_type(tree.children[0])
        remainder = tree.children[1:]
        allow_null = ColumnDefinition.parse_allow_null(remainder)
        default = ColumnDefinition.parse_default(remainder)
        is_auto_increment = ColumnDefinition.parse_is_auto_increment(remainder)

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

    @staticmethod
    def parse_data_type(tree):
        assert tree.data == "data_type"

        name = tree.children[0].type
        number = DataType.parse_number(tree)
        fsp = number if name in ['TIME', 'TIMESTAMP', 'DATETIME'] else None
        length = number if name == 'TEXT' else None
        character_set = DataType.parse_character_set(tree)
        collate = DataType.parse_collate(tree)
        # TODO implement values in ENUM, SET
        # | ENUM "(" ID ("," ID)* ")" [CHARACTER SET ID] [COLLATE ID]
        # | SET "(" ID ("," ID)* ")" [CHARACTER SET ID] [COLLATE ID]
        values = None

        return DataType(name, fsp, length, character_set, collate, values)

    @staticmethod
    def parse_number(tree):
        indexes = [i for i, j in enumerate(tree.children) if j.type == 'NUMBER']
        return int(tree.children[indexes[0]].value) if len(indexes) > 0 else None

    @staticmethod
    def parse_character_set(tree):
        indexes = [i for i, j in enumerate(tree.children) if j.type == "CHARACTER"]
        return tree.children[indexes[0] + 2].value if len(indexes) > 0 else None

    @staticmethod
    def parse_collate(tree):
        indexes = [i for i, j in enumerate(tree.children) if j.type == "COLLATE"]
        return tree.children[indexes[0] + 1].value if len(indexes) > 0 else None


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
