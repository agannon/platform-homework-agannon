import sqlite3
from functools import wraps


def validate_type_field(string):
    """
    Returns True and a cleaned value for field TYPE if it is acceptable
    False and error otherwise
    :param string: string to be validated
    :return: (bool, str)
    """
    if isinstance(string, str):
        if string.lower() in ('temperature', 'humidity'):
            return True, string.lower()
    return False, "The only allowed sensor types are 'temperature' and 'humidity'"


def validate_value_field(number):
    """
    Returns True and input if it is an integer in the range [0,100]
    False and error otherwise
    :param number: number to be validated
    :return: (bool, Union[str, int])
    """
    if isinstance(number, int):
        if 0 <= number <= 100:
            return True, number
    return False, "The only allowed values are integers between 0 and 100 inclusive"


def build_sql_from_get(request, selection):
    # from IPython import embed
    # embed()
    get_data = request.values
    start = get_data.get('start', None)
    end = get_data.get('end', None)
    sensor_type = get_data.get('type', None)
    # Execute the query
    sql = selection
    if start:
        sql += f'AND date_created >= {start} '
    if end:
        sql += f'AND date_created <= {end} '
    if sensor_type:
        sql += f'AND type = "{sensor_type}" '
    return sql

def handle_database_connection(app):
    """
    Decorator that takes the app name and sets up the database connection
    for a request and then closes it when done.
    :param app:
    :return:
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Set the db that we want and open the connection
            if app.config['TESTING']:
                conn = sqlite3.connect('test_database.db')
            else:
                conn = sqlite3.connect('database.db')
            conn.row_factory = sqlite3.Row
            kwargs['conn'] = conn
            return_value = func(*args, **kwargs)
            conn.close()
            return return_value
        return wrapper
    return decorator
