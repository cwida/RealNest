import duckdb


class Schema:
    class Column:
        name: str
        type: str
        children: 'Schema.ColumnList'

        def __init__(self, name: str, coltype: duckdb.typing.DuckDBPyType | None):
            self.name = name
            if coltype is None:
                return

            self.type = coltype.id if coltype.__repr__() != 'JSON' else 'json'
            try:
                if coltype.id != 'decimal':
                    self.children = Schema.ColumnList(coltype.children)
            except duckdb.InvalidInputException:
                pass

        def __eq__(self, other):
            return self.name == other.name and self.type == other.type and self.get_children() == other.get_children()

        def get_children(self):
            return self.children if hasattr(self, 'children') else None

        def duckdb_type(self):
            match self.type:
                case "list":
                    return duckdb.list_type(self.children[0].duckdb_type())
                case "struct":
                    return duckdb.struct_type(self.children.duckdb_schema())
                case "map":
                    return duckdb.map_type(self.children[0].duckdb_type(), self.children[1].duckdb_type())
                case _:
                    return duckdb.type(self.type)

        @classmethod
        def from_json(cls, j: dict):
            column = cls(j['name'], None)
            column.type = j['type']
            if 'children' in j:
                column.children = Schema.ColumnList.from_json(j['children'])
            return column

    class ColumnList(list[Column]):
        def __init__(self, cols: list[tuple[str, duckdb.typing.DuckDBPyType]]):
            super().__init__([Schema.Column(name, coltype) for name, coltype in cols])

        def merge(self, other: 'Schema.ColumnList'):
            self_dict = {col.name: col for col in self}

            for col in other:
                if col.name not in self_dict:
                    self_dict[col.name] = col
                    self.append(col)
                    continue

                self_col = self_dict[col.name]
                if col == self_col:
                    continue

                if self_col.type != col.type:
                    print(f"Incompatible schema for key {col.name}: {self_col.type} != {col.type}")
                    return

                if self_col.get_children() is not None:
                    self_col.children.merge(col.children)

        def duckdb_schema(self):
            return {col.name: col.duckdb_type() for col in self}

        def __eq__(self, other):
            return len(self) == len(other) and all(self[i] == other[i] for i in range(len(self)))

        @classmethod
        def from_json(cls, j: list[dict]):
            column_list = cls([])
            column_list.extend(Schema.Column.from_json(col) for col in j)
            return column_list

    columns: ColumnList

    def __init__(self, cols: list[tuple[str, duckdb.typing.DuckDBPyType]]):
        self.columns = Schema.ColumnList(cols)

    def merge(self, other: 'Schema'):
        self.columns.merge(other.columns)

    def duckdb_schema(self):
        return self.columns.duckdb_schema()

    @classmethod
    def from_json(cls, j: dict):
        schema = cls([])
        schema.columns = Schema.ColumnList.from_json(j['columns'])
        return schema
