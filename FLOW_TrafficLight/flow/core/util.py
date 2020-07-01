"""A collection of utility functions for Flow."""

import csv
import errno
import os
from lxml import etree
from xml.etree import ElementTree
import random
import matplotlib.pyplot as plt


def makexml(name, nsl):
    """Create an xml file."""
    xsi = "http://www.w3.org/2001/XMLSchema-instance"
    ns = {"xsi": xsi}
    attr = {"{%s}noNamespaceSchemaLocation" % xsi: nsl}
    t = etree.Element(name, attrib=attr, nsmap=ns)
    return t


def printxml(t, fn):
    """Print information from a dict into an xml file."""
    etree.ElementTree(t).write(
        fn, pretty_print=True, encoding='UTF-8', xml_declaration=True)


def ensure_dir(path):
    """Ensure that the directory specified exists, and if not, create it."""
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise
    return path


def get_truncated_normal(mean=0, sd=1800, low=0, upp=10):
    while True:
        rd = random.normalvariate(mean, sd)
        if rd >= low and rd <= upp:
            return int(rd)


def generate_demands(segment_id_pairs, network_name, horizon, is_uniform, num_of_vehicles, save_hist=True):

    """Generate a xml file of routes.

    format: <vehicle id="0" departLane="?" arrivalLane="?" depart="0"/>

    Args:
      is_uniform: bool, if false then generate a normal distribuiton
      num_of_vehicles: total vehicles in an hour.
      segment_id_pairs: a list of pair of string [(start_segment, end_segment), ...]
        where start_segment and end_segment is the segment id in sumo.
    Returns:
      A string of printable xml route file.
    """
    mean = horizon / 2
    std = 10
    vehicle_str = dict()
    for i in range(num_of_vehicles):
        vehicle_id = "v_%d" % i
        # select one from segemtn_id_pairs as depart & arrival
        route = random.choice(segment_id_pairs)

        if is_uniform:
            time = random.choice(range(0, horizon))
        else:
            # we center demand around horizon/2
            time = get_truncated_normal(mean, std, 0, horizon)

        vehicle_str[time] = dict(name=vehicle_id, vtype="human", route=route, depart=str(time),
                                 departSpeed="10")
    sorted_ids = sorted(vehicle_str.keys())

    # store histogram of demand
    if save_hist:
        home_dir = os.path.expanduser('~')
        ensure_dir('%s' % home_dir + '/ray_results/real_time_metrics/hist')
        hist_path = home_dir + '/ray_results/real_time_metrics/hist/'

        if is_uniform:
            title_flag = "Random Distribution"
        else:
            title_flag = "Peak Distribution: Mean = {} secs, Standard Dev ={} secs,".format(mean, std)

        plt.hist(vehicle_str.keys(), edgecolor='white')
        plt.ylabel("Frequency")
        plt.xlabel("Depart time INTO the Network (secs)")
        plt.title("Demand Data \n {} vehicles \n".format(num_of_vehicles) + title_flag)
        plt.savefig(hist_path + '%s.png' % network_name)
        plt.close()

    return sorted_ids, vehicle_str


def emission_to_csv(emission_path, output_path=None):
    """Convert an emission file generated by sumo into a csv file.

    Note that the emission file contains information generated by sumo, not
    flow. This means that some data, such as absolute position, is not
    immediately available from the emission file, but can be recreated.

    Parameters
    ----------
    emission_path : str
        path to the emission file that should be converted
    output_path : str
        path to the csv file that will be generated, default is the same
        directory as the emission file, with the same name
    """
    parser = etree.XMLParser(recover=True)
    tree = ElementTree.parse(emission_path, parser=parser)
    root = tree.getroot()

    # parse the xml data into a dict
    out_data = []
    for time in root.findall('timestep'):
        t = float(time.attrib['time'])

        for car in time:
            out_data.append(dict())
            try:
                out_data[-1]['time'] = t
                out_data[-1]['CO'] = float(car.attrib['CO'])
                out_data[-1]['y'] = float(car.attrib['y'])
                out_data[-1]['CO2'] = float(car.attrib['CO2'])
                out_data[-1]['electricity'] = float(car.attrib['electricity'])
                out_data[-1]['type'] = car.attrib['type']
                out_data[-1]['id'] = car.attrib['id']
                out_data[-1]['eclass'] = car.attrib['eclass']
                out_data[-1]['waiting'] = float(car.attrib['waiting'])
                out_data[-1]['NOx'] = float(car.attrib['NOx'])
                out_data[-1]['fuel'] = float(car.attrib['fuel'])
                out_data[-1]['HC'] = float(car.attrib['HC'])
                out_data[-1]['x'] = float(car.attrib['x'])
                out_data[-1]['route'] = car.attrib['route']
                out_data[-1]['relative_position'] = float(car.attrib['pos'])
                out_data[-1]['noise'] = float(car.attrib['noise'])
                out_data[-1]['angle'] = float(car.attrib['angle'])
                out_data[-1]['PMx'] = float(car.attrib['PMx'])
                out_data[-1]['speed'] = float(car.attrib['speed'])
                out_data[-1]['edge_id'] = car.attrib['lane'].rpartition('_')[0]
                out_data[-1]['lane_number'] = car.attrib['lane'].\
                    rpartition('_')[-1]
            except KeyError:
                del out_data[-1]

    # sort the elements of the dictionary by the vehicle id
    out_data = sorted(out_data, key=lambda k: k['id'])

    # default output path
    if output_path is None:
        output_path = emission_path[:-3] + 'csv'

    # output the dict data into a csv file
    keys = out_data[0].keys()
    with open(output_path, 'w') as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(out_data)


def trip_info_emission_to_csv(emission_path, output_path=None):
    """Convert an emission file generated by sumo into a csv file.

    Note that the emission file contains information generated by sumo, not
    flow. This means that some data, such as absolute position, is not
    immediately available from the emission file, but can be recreated.

    Parameters
    ----------
    emission_path : str
        path to the emission file that should be converted
    output_path : str
        path to the csv file that will be generated, default is the same
        directory as the emission file, with the same name
    """
    parser = etree.XMLParser(recover=True)
    tree = ElementTree.parse(emission_path, parser=parser)
    root = tree.getroot()

    # parse the xml data into a dict
    out_data = []
    for car in root.findall("tripinfo"):
        # t = float(time.attrib['time'])

    # for car in info:
        out_data.append(dict())
        try:
            out_data[-1]['travel_times'] = float(car.attrib['duration'])
            out_data[-1]['arrival'] = float(car.attrib['arrival'])
            out_data[-1]['id'] = car.attrib['id']
        except KeyError:
            del out_data[-1]

    # sort the elements of the dictionary by the vehicle id
    out_data = sorted(out_data, key=lambda k: k['id'])

    # default output path
    if output_path is None:
        output_path = emission_path[:-3] + 'csv'

    # output the dict data into a csv file
    # keys = out_data[0].keys()
    # with open(output_path, 'w') as output_file:
    #     dict_writer = csv.DictWriter(output_file, keys)
    #     dict_writer.writeheader()
    #     dict_writer.writerows(out_data)

    return out_data