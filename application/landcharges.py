import psycopg2
import logging
from flask import Response
import json


def get_all_land_charges(connection, type_filter):
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if type_filter == '':
        cursor.execute('SELECT number, class, date, type FROM documents')
    else:
        cursor.execute('SELECT number, class, date, type FROM documents WHERE type=%(type)s', {'type': type_filter})
    rows = cursor.fetchall()

    result = []
    for row in rows:
        result.append({
            'reg_no': row['number'],
            'class': row['class'],
            'date': row['date'],
            'type': row['type']
        })

    cursor.close()
    connection.close()
    return result


def get_land_charge_record(connection, number, charge_class, date):
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute('SELECT time, registration_no, priority_notice, reverse_name, property_county, '
                   'registration_date, class_type, remainder_name, punctuation_code, name, address, '
                   'occupation, counties, amendment_info, property, parish_district, priority_notice_ref '
                   'FROM lc_mock '
                   'WHERE registration_no = %(no)s AND class_type = %(type)s AND registration_date = %(date)s', {
                       'no': number, 'type': charge_class, 'date': date
                   })
    rows = cursor.fetchall()
    result = []
    for row in rows:
        print(row)
        result.append({
            'time': row['time'].isoformat(),
            'registration_no': row['registration_no'],
            'priority_notice': row['priority_notice'],
            'reverse_name': row['reverse_name'],
            'property_county': row['property_county'],
            'registration_date': row['registration_date'].strftime('%Y-%m-%d'),
            'class_type': row['class_type'],
            'remainder_name': row['remainder_name'],
            'punctuation_code': row['punctuation_code'],
            'name': row['name'],
            'address': row['address'],
            'occupation': row['occupation'],
            'counties': row['counties'],
            'amendment_info': row['amendment_info'],
            'property': row['property'],
            'parish_district': row['parish_district'],
            'priority_notice_ref': row['priority_notice_ref']
        })
    return result


def get_document_record(connection, number, charge_class, date):
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute('SELECT class, number, date, orig_class, orig_number, orig_date, canc_ind, type, timestamp '
                   'FROM documents WHERE number = %(no)s AND class = %(type)s AND date = %(date)s', {
                       'no': number, 'type': charge_class, 'date': date
                   })
    rows = cursor.fetchall()
    result = []
    for row in rows:
        result.append({
            'reg_no': row['number'],
            'class': row['class'],
            'date': row['date'],
            'orig_class': row['orig_class'],
            'orig_number': row['orig_number'],
            'orig_date': row['orig_date'],
            'canc_ind': row['canc_ind'],
            'type': row['type'],
            'timestamp': row['timestamp'].isoformat()
        })
    return result


def get_document_record_by_orig_or_current(cursor, number, charge_class, date):
    cursor.execute('SELECT class, number, date, orig_class, orig_number, orig_date, canc_ind, type, timestamp '
                   'FROM documents WHERE (orig_number = %(no)s AND orig_class = %(type)s AND orig_date = %(date)s) OR '
                   '(number = %(no)s AND class = %(type)s AND date = %(date)s)', {
                       'no': number, 'type': charge_class, 'date': date
                   })
    rows = cursor.fetchall()
    result = []
    for row in rows:
        result.append({
            'reg_no': row['number'],
            'class': row['class'],
            'date': row['date'],
            'orig_class': row['orig_class'],
            'orig_number': row['orig_number'],
            'orig_date': row['orig_date'],
            'canc_ind': row['canc_ind'],
            'type': row['type'],
            'timestamp': row['timestamp'].isoformat()
        })
    return result


def do_records_match(a, b):
    return a['class'] == b['class'] and \
           a['reg_no'] == b['reg_no'] and \
           a['date'] == b['date']


def does_list_contain(list_to_test, item):
    test = next((i for i in list_to_test if do_records_match(i, item)), None)
    return test is not None


def get_history_recurse(cursor, results, number, charge_class, date):
    init_results = get_document_record_by_orig_or_current(cursor, number, charge_class, date)

    to_process = []
    for item in init_results:
        if not does_list_contain(results, item):
            to_process.append(item)
            results.append(item)

    for item in to_process:
        get_history_recurse(cursor, results, item['reg_no'], item['class'], item['date'])
        get_history_recurse(cursor, results, item['orig_number'], item['orig_class'], item['orig_date'])


def get_document_history(connection, number, charge_class, date):
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    results = []
    get_history_recurse(cursor, results, number, charge_class, date)
    return results


def synchronise(connection, data):
    try:
        cursor = connection.cursor()
        cursor.execute("INSERT INTO lc_mock (time, registration_no, "
                       "priority_notice, reverse_name, property_county, "
                       "registration_date, class_type, remainder_name, "
                       "punctuation_code, name, address, "
                       "occupation, counties, amendment_info, "
                       "property, parish_district, priority_notice_ref) "
                       "VALUES (%(time)s, %(registration_no)s, %(priority_notice)s, %(reverse_name)s, "
                       "%(property_county)s, %(registration_date)s, %(class_type)s, %(remainder_name)s, "
                       "%(punctuation_code)s, %(name)s, %(address)s, %(occupation)s, %(counties)s, "
                       "%(amendment_info)s, %(property)s, %(parish_district)s, %(priority_notice_ref)s) ",
                       {"time": data['time'],
                        "registration_no": data['registration_no'],
                        "priority_notice": data['priority_notice'],
                        "reverse_name": data['reverse_name'],
                        "property_county": data['property_county'],
                        "registration_date": data['registration_date'],
                        "class_type": data['class_type'],
                        "remainder_name": data['remainder_name'],
                        "punctuation_code": data['punctuation_code'],
                        "name": data['name'],
                        "address": data['address'],
                        "occupation": data['occupation'],
                        "counties": data['counties'],
                        "amendment_info": data['amendment_info'],
                        "property": data['property'],
                        "parish_district": data['parish_district'],
                        "priority_notice_ref": data['priority_notice_ref']})

    except psycopg2.OperationalError as error:
        logging.error(error)
        return Response("Failed to insert to database: {}".format(error), status=500)

    connection.commit()
    cursor.close()
    connection.close()
    return Response("Record added to db2", status=200)