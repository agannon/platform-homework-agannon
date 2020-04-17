import json
import pytest
import sqlite3
import time
import unittest
import statistics

from app import app


class SensorRoutesTestCases(unittest.TestCase):

    def setUp(self):
        # Setup the SQLite DB
        conn = sqlite3.connect('test_database.db')
        conn.execute('DROP TABLE IF EXISTS readings')
        conn.execute(
            'CREATE TABLE IF NOT EXISTS readings (device_uuid TEXT, type TEXT, value INTEGER, date_created INTEGER)')

        self.device_uuid = 'test_device'

        # Setup some sensor data
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        self.setup_time = time.time()

        cur.execute('insert into readings (device_uuid,type,value,date_created) VALUES (?,?,?,?)',
                    (self.device_uuid, 'temperature', 22, int(self.setup_time) - 100))
        cur.execute('insert into readings (device_uuid,type,value,date_created) VALUES (?,?,?,?)',
                    (self.device_uuid, 'temperature', 50, int(self.setup_time) - 50))
        cur.execute('insert into readings (device_uuid,type,value,date_created) VALUES (?,?,?,?)',
                    (self.device_uuid, 'temperature', 100, int(self.setup_time)))
        cur.execute('insert into readings (device_uuid,type,value,date_created) VALUES (?,?,?,?)',
                    (self.device_uuid, 'humidity', 73, int(self.setup_time + 50)))

        cur.execute('insert into readings (device_uuid,type,value,date_created) VALUES (?,?,?,?)',
                    ('other_uuid', 'temperature', 22, int(self.setup_time)))
        cur.execute('insert into readings (device_uuid,type,value,date_created) VALUES (?,?,?,?)',
                    ('other_uuid', 'temperature', 30, int(self.setup_time)))
        conn.commit()

        app.config['TESTING'] = True

        self.client = app.test_client

    def test_device_readings_get(self):
        # Given a device UUID
        # When we make a request with the given UUID
        request = self.client().get('/devices/{}/readings/'.format(self.device_uuid))

        # Then we should receive a 200
        self.assertEqual(request.status_code, 200)

        # And the response data should have three sensor readings
        self.assertTrue(len(json.loads(request.data)) == 4)

    def test_device_readings_post(self):
        # Given a device UUID
        # When we make a request with the given UUID to create a reading
        request = self.client().post('/devices/{}/readings/'.format(self.device_uuid), data=
        json.dumps({
            'type': 'temperature',
            'value': 100
        }))

        # Then we should receive a 201
        self.assertEqual(request.status_code, 201)

        # And when we check for readings in the db
        conn = sqlite3.connect('test_database.db')
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute('select * from readings where device_uuid="{}"'.format(self.device_uuid))
        rows = cur.fetchall()

        # We should have five
        self.assertTrue(len(rows) == 5)

    def test_device_readings_get_temperature(self):
        """
        This test should be implemented. The goal is to test that
        we are able to query for a device's temperature data only.
        """
        request = self.client().get('/devices/{}/readings/?type=temperature'.format(self.device_uuid))

        self.assertEqual(len(request.json), 3)

    def test_device_readings_get_humidity(self):
        """
        This test should be implemented. The goal is to test that
        we are able to query for a device's humidity data only.
        """
        request = self.client().get('/devices/{}/readings/?type=humidity'.format(self.device_uuid))

        self.assertEqual(len(request.json), 1)

    def test_device_readings_get_past_dates(self):
        """
        This test should be implemented. The goal is to test that
        we are able to query for a device's sensor data over
        a specific date range. We should only get the readings
        that were created in this time range.
        """
        request = self.client().get(f'/devices/{self.device_uuid}/readings/'
                                    f'?start={int(self.setup_time - 75)}'
                                    f'&end={int(self.setup_time + 25)}')

        self.assertEqual(len(request.json), 2)

    def test_device_readings_min(self):
        """
        This test should be implemented. The goal is to test that
        we are able to query for a device's min sensor reading.
        """
        request = self.client().get('/devices/{}/readings/min/'.format(self.device_uuid))

        self.assertEqual(request.json.get('value', None), 22)

    def test_device_readings_max(self):
        """
        This test should be implemented. The goal is to test that
        we are able to query for a device's max sensor reading.
        """
        request = self.client().get('/devices/{}/readings/max/'.format(self.device_uuid))

        self.assertEqual(request.json.get('value', None), 100)

    def test_device_readings_median(self):
        """
        This test should be implemented. The goal is to test that
        we are able to query for a device's median sensor reading.
        """
        request = self.client().get('/devices/{}/readings/median/'.format(self.device_uuid))

        self.assertEqual(request.json.get('value', None), 61)

    def test_device_readings_mean(self):
        """
        This test should be implemented. The goal is to test that
        we are able to query for a device's mean sensor reading value.
        """
        request = self.client().get('/devices/{}/readings/mean/'.format(self.device_uuid))

        self.assertEqual(request.json.get('value', None), 61)

    def test_device_readings_mode(self):
        """
        This test should be implemented. The goal is to test that
        we are able to query for a device's mode sensor reading value.
        """
        request = self.client().get('/devices/{}/readings/mode/'.format(self.device_uuid))

        self.assertEqual(request.json.get('value', None), 22)

    def test_device_readings_quartiles(self):
        """
        This test should be implemented. The goal is to test that
        we are able to query for a device's 1st and 3rd quartile
        sensor reading value.
        """
        request = self.client().get('/devices/{}/readings/quartiles/'.format(self.device_uuid))

        self.assertEqual(request.json.get('quartile_1', None), 29)
        self.assertEqual(request.json.get('quartile_3', None), 93)

    def test_device_readings_quartiles_not_enough_data(self):
        request = self.client().get('/devices/{}/readings/quartiles/?type=humidity'.format(self.device_uuid))

        self.assertEqual(request.json.get('quartile_1', None), None)
        self.assertEqual(request.json.get('quartile_3', None), None)

    def test_summary_results_temperature(self):
        request = self.client().get('/devices/summaries/?type=temperature')

        expected_list = [{
            'device_uuid': self.device_uuid,
            'number_of_readings': 3,
            'max_reading_value': 100,
            'median_reading_value': 50,
            'mean_reading_value': 57,
            'quartile_1_value': 22,
            'quartile_3_value': 100
        },
        {
            'device_uuid': 'other_uuid',
            'number_of_readings': 2,
            'max_reading_value': 30,
            'median_reading_value': 26,
            'mean_reading_value': 26,
            'quartile_1_value': 20,
            'quartile_3_value': 32
        }
        ]
        self.assertIn(request.json[0], expected_list)
        self.assertIn(request.json[1], expected_list)

    def test_summary_results_humidity(self):
        request = self.client().get('/devices/summaries/?type=humidity')

        expected_list = [{
            'device_uuid': self.device_uuid,
            'number_of_readings': 1,
            'max_reading_value': 73,
            'median_reading_value': 73,
            'mean_reading_value': 73,
            'quartile_1_value': None,
            'quartile_3_value': None
        },
        ]
        self.assertIn(request.json[0], expected_list)

    def test_invalid_value_post(self):
        request = self.client().post('/devices/{}/readings/'.format(self.device_uuid), data=
        json.dumps({
            'type': 'temperature',
            'value': 200
        }))

        # Then we should receive a 400
        self.assertEqual(request.status_code, 400)
        self.assertIn("The only allowed values are integers between 0 and 100 inclusive", str(request.data))

        request = self.client().post('/devices/{}/readings/'.format(self.device_uuid), data=
        json.dumps({
            'type': 'temperature',
            'value': -10
        }))
        # Then we should receive a 400
        self.assertEqual(request.status_code, 400)
        self.assertIn("The only allowed values are integers between 0 and 100 inclusive", str(request.data))

        # And when we check for readings in the db
        conn = sqlite3.connect('test_database.db')
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute('select * from readings where device_uuid="{}"'.format(self.device_uuid))
        rows = cur.fetchall()

        # We should have four (no new one)
        self.assertEqual(len(rows), 4)

    def test_invalid_type_post(self):
        request = self.client().post('/devices/{}/readings/'.format(self.device_uuid), data=
        json.dumps({
            'type': 'flavor',
            'value': 50
        }))

        # Then we should receive a 400
        self.assertEqual(request.status_code, 400)
        self.assertIn("The only allowed sensor types are 'temperature' and 'humidity'", str(request.data))

        # And when we check for readings in the db
        conn = sqlite3.connect('test_database.db')
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute('select * from readings where device_uuid="{}"'.format(self.device_uuid))
        rows = cur.fetchall()

        # We should have four (no new one)
        self.assertEqual(len(rows), 4)

