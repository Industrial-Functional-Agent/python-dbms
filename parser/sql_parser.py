from lark import Lark


class SqlParser:
    def __init__(self):
        self.parser = None

    def build_parser(self):
        self.parser = Lark('''
        create: CREATE TABLE [IF NOT EXIST] ID \
                "(" create_definition ("," create_definition)* ")"
        create_definition: ID column_definition
                         | PRIMARY KEY [index_type] \
                           "(" index_col_name ("," index_col_name)* ")" \
                           [index_option ("," index_option)*] 
                         | UNIQUE [INDEX | KEY] [ID] [index_type] \
                           "(" index_col_name ("," index_col_name)* ")" \
                            [index_option ("," index_option)*]
                         | FOREIGN KEY [ID] \
                           "(" index_col_name ("," index_col_name)* ")" \
                           reference_definition
        column_definition: data_type [NOT NULL | NULL] \
                           [DEFAULT (STRING|NUMBER)] [AUTO_INCREMENT]
        data_type: INT
                 | DOUBLE
                 | DECIMAL
                 | DATE
                 | TIME ["(" NUMBER ")"]
                 | TIMESTAMP ["(" NUMBER ")"]
                 | DATETIME ["(" NUMBER ")"]
                 | TEXT ["(" NUMBER ")"] [CHARACTER SET ID] [COLLATE ID]
                 | ENUM "(" ID ("," ID)* ")" [CHARACTER SET ID] [COLLATE ID]
                 | SET "(" ID ("," ID)* ")" [CHARACTER SET ID] [COLLATE ID]
                 | JSON
        reference_definition: REFERENCES ID (index_col_name ("," index_col_name)*) \
                              [ON DELETE reference_option] \
                              [ON UPDATE reference_option]
        reference_option: RESTRICT
                        | CASCADE 
                        | SET NULL 
                        | NO ACTION 
                        | SET DEFAULT
        index_option: KEY_BLOCK_SIZE ["="] NUMBER
                    | index_type
                    | WITH PARSER ID
        index_type: USING (BTREE | HASH)
        index_col_name: ID ["(" NUMBER ")"] [ASC | DESC]
        ACTION: "action"i
        ASC: "asc"i
        AUTO_INCREMENT: "auto_increment"i
        BTREE: "btree"i
        CASCADE: "cascade"i
        CHARACTER: "character"i
        COLLATE: "collate"i
        CREATE: "create"i
        DATE: "date"i
        DATETIME: "datetime"i
        DECIMAL: "decimal"i
        DEFAULT: "default"i
        DELETE: "delete"i
        DESC: "desc"i
        DOUBLE: "double"i
        ENUM: "enum"i
        EXIST: "exist"i
        FOREIGN: "foreign"i
        HASH: "hash"i
        ID: /[a-zA-Z_][a-zA-Z0-9_]*/
        IF: "if"i
        INDEX: "index"i
        INT: "int"i
        JSON: "json"i
        KEY: "key"i
        KEY_BLOCK_SIZE: "key_block_size"i
        NO: "no"i
        NOT: "not"i
        NULL: "null"i
        ON: "on"i
        PARSER: "parser"i
        PRIMARY: "primary"i
        REFERENCES: "references"i
        RESTRICT: "restrict"i
        SET: "set"i
        TABLE: "table"i
        TEXT: "text"i
        TIME: "time"i
        TIMESTAMP: "timestamp"i
        UNIQUE: "unique"i
        UPDATE: "update"i
        USING: "using"i
        WITH: "with"i
        %import common.NUMBER
        %import common.WS
        %import common.ESCAPED_STRING -> STRING
        %ignore WS
         ''', start='create')

        return self.parser

    def parse(self, txt):
        return self.parser.parse(txt)


if __name__ == '__main__':
    sql_parser = SqlParser()
    sql_parser.build_parser()
    a = sql_parser.parse('''
      create table a(
      num INT,
      name TEXT(20),
      PRIMARY KEY (num)
    )
    ''')
    print(a)
