import os


def migrate(database, migrations_path):
    from playhouse.kv import KeyValue

    files = sorted(os.listdir(migrations_path))
    kv = KeyValue(database=database)
    for f in files:
        if not f.endswith(".sql"):
            continue

        if "migration_" + f in kv:
            continue

        print(f"Migration {f}...")
        with open(f"{migrations_path}/{f}") as fh:
            cursor = database.execute_sql(fh.read())
            kv["migration_" + f] = "completed"
            cursor.close()


def query_search(qs, q, cols):
    """
        This makes it possible to search for e.g. "uuid javascript"
        and it will find places where one of the columns have uuid
        AND one/more column also have javascript.
    """
    import operator
    from functools import reduce
    search_clause = True
    for word in q.split(" "):
        word_clause = [(col ** f"%%{word}%%") for col in cols]
        search_clause = search_clause & reduce(operator.or_, word_clause)

    return search_clause

