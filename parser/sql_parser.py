from lark import Lark


class SqlParser:
    def __init__(self):
        self.parser = None

    def build_parser(self):
        self.parser = Lark('''
        sql: ddl
        ddl: (create_table | alter_table | drop_table | create_index)
        create_table: CREATE TABLE [IF NOT EXISTS] ID \
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
        create_index: CREATE [UNIQUE] INDEX ID [index_type] ON ID "(" index_col_name ("," index_col_name)* ")" \
                      [index_option] [lock_option ("," lock_option)*]
        lock_option: LOCK ["="] (DEFAULT | NONE | SHARED | EXCLUSIVE)
        alter_table: ALTER TABLE ID [alter_specification ("," alter_specification)*]
        alter_specification: ADD [COLUMN] ID column_definition [FIRST | AFTER ID]
                           | ADD [COLUMN] "(" ID column_definition ("," column_definition)* ")"
                           | ADD (INDEX | KEY) [ID] \
                                 [index_type] "(" index_col_name ("," index_col_name)* ")" \
                                 [index_option ("," index_option)*]
                           | ADD PRIMARY KEY \
                                 [index_type] "(" index_col_name ("," index_col_name)* ")" \
                                 [index_option ("," index_option)*]
                           | ADD UNIQUE [INDEX | KEY] [ID] \
                                 [index_type] "(" index_col_name ("," index_col_name)* ")" \
                                 [index_option ("," index_option)*]
                           | ADD FOREIGN KEY [ID] "(" index_col_name ("," index_col_name)* ")" \
                                 reference_definition
                           | ALTER [COLUMN] ID (SET DEFAULT STRING | DROP DEFAULT)
                           | CHANGE [COLUMN] ID ID column_definition [FIRST | AFTER ID]
                           | [DEFAULT] CHARACTER SET ["="] ID [COLLATE ["="] ID]
                           | CONVERT TO CHARACTER SET ID [COLLATE ID]
                           | DROP [COLUMN] ID
                           | DROP (INDEX|KEY) ID
                           | DROP PRIMARY KEY
                           | DROP FOREIGN KEY ID
                           | LOCK ["="] (DEFAULT | NONE | SHARED | EXCLUSIVE)
                           | MODIFY [COLUMN] ID column_definition [FIRST | AFTER ID]
                           | ORDER BY ID ("," ID)*
                           | RENAME (INDEX|KEY) ID TO ID
                           | RENAME [TO | AS] ID
        drop_table: DROP TABLE [IF EXISTS] ID ("," ID)* [RESTRICT | CASCADE]
        ACTION: "action"i
        ADD: "add"i
        AFTER: "after"i
        ALTER: "alter"i
        AS: "as"i
        ASC: "asc"i
        AUTO_INCREMENT: "auto_increment"i
        BTREE: "btree"i
        BY: "by"i
        CASCADE: "cascade"i
        CHANGE: "change"i
        CHARACTER: "character"i
        COLLATE: "collate"i
        COLUMN: "column"i
        CONVERT: "convert"i
        CREATE: "create"i
        DATE: "date"i
        DATETIME: "datetime"i
        DECIMAL: "decimal"i
        DEFAULT: "default"i
        DELETE: "delete"i
        DESC: "desc"i
        DOUBLE: "double"i
        DROP: "drop"i
        ENUM: "enum"i
        EXCLUSIVE: "exclusive"i
        EXISTS: "exists"i
        FIRST: "first"i
        FOREIGN: "foreign"i
        HASH: "hash"i
        ID: /[a-zA-Z_][a-zA-Z0-9_]*/
        IF: "if"i
        INDEX: "index"i
        INT: "int"i
        JSON: "json"i
        KEY: "key"i
        KEY_BLOCK_SIZE: "key_block_size"i
        LOCK: "lock"i
        MODIFY: "modify"i
        NO: "no"i
        NONE: "none"i
        NOT: "not"i
        NULL: "null"i
        ON: "on"i
        ORDER: "order"i
        PARSER: "parser"i
        PRIMARY: "primary"i
        REFERENCES: "references"i
        RENAME: "rename"i
        RESTRICT: "restrict"i
        SET: "set"i
        SHARED: "shared"i
        TABLE: "table"i
        TEXT: "text"i
        TIME: "time"i
        TIMESTAMP: "timestamp"i
        TO: "to"i
        UNIQUE: "unique"i
        UPDATE: "update"i
        USING: "using"i
        WITH: "with"i
        %import common.NUMBER
        %import common.WS
        %import common.ESCAPED_STRING -> STRING
        %ignore WS
         ''', start='sql')

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
    b = sql_parser.parse('''
    ALTER TABLE provider ADD PRIMARY KEY(person,place,thing)
    ''')
    print(a)
    print(b)
