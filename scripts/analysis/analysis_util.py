from schema import Schema


def remove_json_types(columns: Schema.ColumnList):
    non_json_columns = Schema.ColumnList([])
    for col in columns:
        if col.type == 'json':
            continue

        children = col.get_children()
        if children:
            col.children = remove_json_types(children)
            if col.type == 'map' and len(col.children) < 2:
                continue
            if (col.type == 'struct' or col.type == 'list') and len(col.children) == 0:
                continue

        non_json_columns.append(col)

    return non_json_columns
