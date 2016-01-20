import psycopg2


def get_name_variants(connection, name):
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute('select number, name from name_variants where upper(name) LIKE %(name)s',
                   {'name': "%{}%".format(name.upper())})
    rows = cursor.fetchall()

    result = []
    for row in rows:
        result.append({
            'name': row['name'],
            'number': row['number']
        })
    return result
