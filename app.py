import sys
import urllib
import urllib.request as request
import argparse, json
from decimal import Decimal
from math import sin, cos, atan2, sqrt


def rad(deg):
    return Decimal(deg) * Decimal(3.141592653589793238) / 180


def get_data_from_url(url):
    try:
        data = request.urlopen(url).read().decode('utf-8')
    except urllib.error.HTTPError as err:
        sys.exit('Failed to get data from that url, {0}'.format(err))
    return data


def prepare_and_filter(data):
    data_str = str(data).replace('\n', ',')
    data_str = '[' + data_str[:-1] + ']'
    data_list = json.loads(data_str, parse_float=Decimal)
    data_list = sorted(data_list, key=lambda record: record['ts'])
    # (0.0, 0.0) is a point in sea somwhere near Africa
    data_list = filter(lambda x: 'control_switch_on' in x or (x['geo']['lat'], x['geo']['lon']) != (0, 0), data_list)
    return data_list


def distance(point1, point2):
    if point1 == point2:
        return 0.0
    else:
        r = 6371000  # the Earth radius, m
        point1 = list(map(lambda x: rad(x), point1))
        point2 = list(map(lambda x: rad(x), point2))
        dlat = point2[0] - point1[0]
        dlon = point2[1] - point1[1]
        a = sin(dlat / 2) ** 2 + cos(point1[0]) * cos(point2[0]) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return r * c


def distances_by_movement(data_list):
    output = {
        'undefined': [],
        'control_switch_on': [],
        'control_switch_off': []
    }

    autopilot = None
    point_a = None

    for item in data_list:
        if 'control_switch_on' in item:
            autopilot = item['control_switch_on']
            continue

        geo_point = item['geo']
        point_b = (geo_point['lat'], geo_point['lon'])
        if not point_a:
            point_a = point_b
            continue

        calculated_dist = distance(point_a, point_b)
        point_a = point_b
        if calculated_dist == 0:
            continue

        if autopilot is None:
            output['undefined'].append(calculated_dist)
        elif autopilot:
            output['control_switch_on'].append(calculated_dist)
        elif not autopilot:
            output['control_switch_off'].append(calculated_dist)

    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('url', type=str, help='path to data resource')
    args = parser.parse_args()

    data = get_data_from_url(args.url)
    prepared_data = prepare_and_filter(data)
    distances = distances_by_movement(prepared_data)

    print('autopilot on: ', sum(distances['control_switch_on']), ' m')
    print('autopilot off: ', sum(distances['control_switch_off']), ' m')
    print('autopilot unknown: ', sum(distances['undefined']), ' m')
