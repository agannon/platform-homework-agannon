from flask import Flask, render_template, request, Response
from flask.json import jsonify
import json
import sqlite3
import time
from statistics import median, quantiles, mode

from utils import validate_type_field, validate_value_field, build_sql_from_get, handle_database_connection

app = Flask(__name__)

# Setup the SQLite DB
conn = sqlite3.connect('database.db')
conn.execute('CREATE TABLE IF NOT EXISTS readings (device_uuid TEXT, type TEXT, value INTEGER, date_created INTEGER)')
conn.close()

@app.route('/devices/<string:device_uuid>/readings/', methods = ['POST', 'GET'])
@handle_database_connection(app)
def request_device_readings(device_uuid, conn):
    """
    This endpoint allows clients to POST or GET data specific sensor types.

    POST Parameters:
    * type -> The type of sensor (temperature or humidity)
    * value -> The integer value of the sensor reading
    * date_created -> The epoch date of the sensor reading.
        If none provided, we set to now.

    Optional Query Parameters:
    * start -> The epoch start time for a sensor being created
    * end -> The epoch end time for a sensor being created
    * type -> The type of sensor value a client is looking for
    """
    cur = conn.cursor()

    if request.method == 'POST':
        # Grab the post parameters
        post_data = json.loads(request.data)
        sensor_type = post_data.get('type')
        value = post_data.get('value')
        date_created = post_data.get('date_created', int(time.time()))

        # validate data
        validations = {
            'sensor_type': validate_type_field(sensor_type),
            'value': validate_value_field(value)
        }

        errors = [x for x in validations.values() if not x[0]]
        if errors:
            return '\n'.join(x[1] for x in errors), 400

        sensor_type = validations.get('sensor_type', sensor_type)[1]
        value = validations.get('value', value)[1]

        # Insert data into db
        cur.execute('insert into readings (device_uuid,type,value,date_created) VALUES (?,?,?,?)',
                    (device_uuid, sensor_type, value, date_created))

        conn.commit()

        # Return success
        return 'success', 201
    else:
        selection = f'select * from readings where device_uuid="{device_uuid}" '
        sql = build_sql_from_get(request, selection)
        print(sql)
        cur.execute(sql)
        rows = cur.fetchall()

        # Return the JSON
        return jsonify([dict(zip(['device_uuid', 'type', 'value', 'date_created'], row)) for row in rows]), 200

@app.route('/devices/<string:device_uuid>/readings/max/', methods = ['GET'])
@handle_database_connection(app)
def request_device_readings_max(device_uuid, conn):
    """
    This endpoint allows clients to GET the max sensor reading for a device.

    Mandatory Query Parameters:
    * type -> The type of sensor value a client is looking for

    Optional Query Parameters
    * start -> The epoch start time for a sensor being created
    * end -> The epoch end time for a sensor being created
    """
    cur = conn.cursor()

    selection = f'select MAX(value) from readings where device_uuid="{device_uuid}" '
    sql = build_sql_from_get(request, selection)
    cur.execute(sql)
    row = cur.fetchone()

    return jsonify(dict(zip(['value'], row))), 200

@app.route('/devices/<string:device_uuid>/readings/min/', methods = ['GET'])
@handle_database_connection(app)
def request_device_readings_min(device_uuid, conn):
    """
    This endpoint allows clients to GET the max sensor reading for a device.

    Mandatory Query Parameters:
    * type -> The type of sensor value a client is looking for

    Optional Query Parameters
    * start -> The epoch start time for a sensor being created
    * end -> The epoch end time for a sensor being created
    """
    cur = conn.cursor()

    selection = f'select MIN(value) from readings where device_uuid="{device_uuid}" '
    sql = build_sql_from_get(request, selection)
    cur.execute(sql)
    row = cur.fetchone()

    return jsonify(dict(zip(['value'], row))), 200

@app.route('/devices/<string:device_uuid>/readings/mode/', methods = ['GET'])
@handle_database_connection(app)
def request_device_readings_mode(device_uuid, conn):
    """
    This endpoint allows clients to GET the max sensor reading for a device.

    Mandatory Query Parameters:
    * type -> The type of sensor value a client is looking for

    Optional Query Parameters
    * start -> The epoch start time for a sensor being created
    * end -> The epoch end time for a sensor being created
    """
    cur = conn.cursor()

    selection = f'select value from readings where device_uuid="{device_uuid}" '
    sql = build_sql_from_get(request, selection)
    cur.execute(sql)
    rows = cur.fetchall()
    mode_value = mode([x['value'] for x in rows]) if rows else None

    return jsonify({'value': mode_value}), 200

@app.route('/devices/<string:device_uuid>/readings/median/', methods = ['GET'])
@handle_database_connection(app)
def request_device_readings_median(device_uuid, conn):
    """
    This endpoint allows clients to GET the median sensor reading for a device.

    Mandatory Query Parameters:
    * type -> The type of sensor value a client is looking for

    Optional Query Parameters
    * start -> The epoch start time for a sensor being created
    * end -> The epoch end time for a sensor being created
    """
    cur = conn.cursor()

    selection = f'select value from readings where device_uuid="{device_uuid}" '
    sql = build_sql_from_get(request, selection)
    cur.execute(sql)
    rows = cur.fetchall()
    median_value = int(median([x['value'] for x in rows])) if rows else None

    return jsonify({'value': median_value}), 200

@app.route('/devices/<string:device_uuid>/readings/mean/', methods = ['GET'])
@handle_database_connection(app)
def request_device_readings_mean(device_uuid, conn):
    """
    This endpoint allows clients to GET the mean sensor readings for a device.

    Mandatory Query Parameters:
    * type -> The type of sensor value a client is looking for

    Optional Query Parameters
    * start -> The epoch start time for a sensor being created
    * end -> The epoch end time for a sensor being created
    """
    cur = conn.cursor()

    selection = f'select AVG(value) from readings where device_uuid="{device_uuid}" '
    sql = build_sql_from_get(request, selection)
    cur.execute(sql)
    row = cur.fetchone()
    mean_value = int(row[0]) if row[0] else None

    return jsonify({'value': mean_value}), 200

@app.route('/devices/<string:device_uuid>/readings/quartiles/', methods = ['GET'])
@handle_database_connection(app)
def request_device_readings_quartiles(device_uuid, conn):
    """
    This endpoint allows clients to GET the 1st and 3rd quartile
    sensor reading value for a device.

    Mandatory Query Parameters:
    * type -> The type of sensor value a client is looking for
    * start -> The epoch start time for a sensor being created
    * end -> The epoch end time for a sensor being created
    """
    cur = conn.cursor()

    selection = f'select value from readings where device_uuid="{device_uuid}" '
    sql = build_sql_from_get(request, selection)
    cur.execute(sql)
    rows = cur.fetchall()
    quartiles = [int(q) for q in quantiles(([x['value'] for x in rows]))] if len(rows) >= 2 else [None] * 3
    quartile_dict = {
        'quartile_1': quartiles[0],
        'quartile_3': quartiles[2]
    }


    return jsonify(quartile_dict), 200

@app.route('/devices/summaries/', methods = ['GET'])
@handle_database_connection(app)
def request_readings_summary(conn):
    """
    This endpoint allows clients to GET a full summary
    of all sensor data in the database per device.

    Optional Query Parameters
    * type -> The type of sensor value a client is looking for
    * start -> The epoch start time for a sensor being created
    * end -> The epoch end time for a sensor being created
    """
    cur = conn.cursor()

    selection = f'select * from readings WHERE 1=1 '
    sql = build_sql_from_get(request, selection)
    sql += 'ORDER BY device_uuid '
    cur.execute(sql)
    rows = cur.fetchall()
    devices = {}
    for row in rows:
        if row['device_uuid'] in devices:
            devices[row['device_uuid']].append(row['value'])
        else:
            devices[row['device_uuid']] = [row['value']]
    payload = []
    for k, v in devices.items():
        quartiles = [int(q) for q in quantiles(v)] if len(v) >= 2 else [None] * 3
        payload.append(
            {
                'device_uuid': k,
                'number_of_readings': len(v),
                'max_reading_value': max(v),
                'median_reading_value': int(median(v)),
                'mean_reading_value': sum(v) // len(v),
                'quartile_1_value': quartiles[0],
                'quartile_3_value': quartiles[2]
            }
        )

    return jsonify(payload), 200

if __name__ == '__main__':
    app.run()
