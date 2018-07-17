import sys
import numpy as np
import time
#from matplotlib.colors import ListedColormap, NoNorm
#import matplotlib.pyplot as plt
import csv

# add argument for file name as follows:
# python log_to_csv.py file_name.log

ID_BIT_LEN = 11
SAMPLE_SIZE = 100


###holds all features of a sample
class Entry:
    def __init__(self, label, can_id, can_id_bin,
                 id_priority, can_data, compressed_data, can_data_matrix, can_data_trimmed,
                 time_interval, time_stamp,
                 time_interval_for_id):
        self.label = label
        self.can_id = can_id
        self.can_id_bin = can_id_bin
        self.id_priority = id_priority
        self.compressed_data = compressed_data
        self.time_interval = time_interval
        self.can_data = can_data
        self.can_data_matrix = can_data_matrix
        self.can_data_trimmed = can_data_trimmed
        self.time_stamp = time_stamp
        self.time_interval_for_id = time_interval_for_id
        self.data_len = len(can_data)

    def __str__(self):
        s = "\n===================================="
        s += "\n\tlabel : " + str(self.label)
        s += "\n\tid : " + str(self.can_id)
        s += "\n\tid_bin : " + str(self.can_id_bin)
        s += "\n\tpriority : " + str(self.id_priority)
        s += "\n\tdata len : " + str(self.data_len)
        s += "\n\ttime interval (id) : " + str(self.time_interval_for_id)
        s += "\n\ttime_interval (global) : " + str(self.time_interval)
        s += "\n\tcan_data : " + str(self.can_data)
        s += "\n\tcompressed_data : " + str(self.compressed_data)
        s += "\n\tcan_data_trimmed\n" + str(self.can_data_trimmed)
        return s

    # order is can_id_bin, id_priority, time_interval_for_id, time_interval,
    # can_data, can_data_trimmed, and label
    def get_trimmed_data(self):
        data = []
        for i in range(len(self.can_id_bin)):
            data.append(self.can_id_bin[i])
        data.append(self.id_priority)
        data.append(self.time_interval_for_id)
        data.append(self.time_interval)
        for i in range(len(self.compressed_data)):
            data.append(self.compressed_data[i])
        for i in range(len(self.can_data_trimmed)):
            for j in range(len(self.can_data_trimmed[0])):
                data.append(self.can_data_trimmed[i, j])
        data += self.label
        return data

    def get_categorical_data(self):
        data = []
        data.append(self.can_id)
        # data.append(self.id_priority)
        data.append(self.time_interval_for_id)
        data.append(self.time_interval)
        for i in range(len(self.compressed_data)):
            data.append(self.compressed_data[i])
        for i in range(len(self.can_data_trimmed)):
            for j in range(len(self.can_data_trimmed[0])):
                data.append(self.can_data_trimmed[i, j])
        data += self.label
        return data


# _____________________________________________________________________________________________________
#
# helper functions
# _____________________________________________________________________________________________________

def hex2int(val):
    if val is "":
        return 0
    return int(val, 16)


# returns a list of 1.0s and 0.0s that represent the binary of the integer input
def binary_encode(number, bits):
    l = [float(x) for x in bin(number)[2:]]
    while len(l) < bits:
        l = [0.0] + l
    return l


# transform a list of integers into a matrix
# numbers = list of integers
# bits = number of bits to allocate per int
def list2matrix(numbers, bits):
    row_len = len(numbers)
    col_len = bits
    m = np.array([-1.0] * (row_len * col_len)).reshape((row_len, col_len))
    for i in range(len(numbers)):
        m[i] = binary_encode(numbers[i], bits)
    return m


def get_can_data(s):
    can_data = []
    for i in range(0, len(s), 2):
        can_data.append(hex2int(s[i:i + 2]))
    while len(can_data) < 8:
        can_data.append(0)
    return can_data


def compress_can_data(can_data):
    l = []
    for num in can_data:
        l.append(float(num / 255.0))
    return l


def get_time_interval(time_stamp):
    if len(entries) > 0:
        return time_stamp - entries[-1].time_stamp
    else:
        return 0.0


# returns a list of field names
def gen_field_names():
    l = []
    for i in range(11):
        l.append("can_id_" + str(i))
    l.append("priority")
    l.append("id_time_interval")
    l.append("global_time_interval")
    for i in range(8):
        l.append("can_data_byte_" + str(i))
    for i in range(64):
        l.append("can_data_bit_" + str(i))

    l.append("label_0")
    l.append("label_1")
    return l


def gen_field_names_v2():
    l = []
    l.append("can_id")
    l.append("id_time_interval")
    l.append("global_time_interval")
    for i in range(8):
        l.append("can_data_byte_" + str(i))
    for i in range(64):
        l.append("can_data_bit_" + str(i))

    l.append("label_0")
    l.append("label_1")
    return l


# finds the time interval from when the can_id was last seen
# NOTE: only looks back 16 messages in the past
def get_time_interval_for_id(can_id, time_stamp):
    entry = find_last_entry_with_id(can_id, 16)
    if entry is not None:
        return time_stamp - entry.time_stamp
    return 0.0


# returns a list with -1.0 for values that haven't changed
# if can_id hasn't been seen before, then returns [-1.0,...,-1.0]
# only looks back 16 entries in the past
def get_changed_values(can_id, curr_data):
    prev_entry = find_last_entry_with_id(can_id, 64)
    m = list2matrix(curr_data, 8)
    if prev_entry is not None:
        prev_data = prev_entry.can_data
        assert (len(prev_data) == len(curr_data)), "Length of Data are not equal"
        prev_m = list2matrix(prev_data, 8)
        for r in range(m.shape[0]):
            for c in range(m.shape[1]):
                if m[r, c] == prev_m[r, c]:
                    m[r, c] = -1.0
    return m


def find_last_entry_with_id(can_id, search_limit):
    assert (search_limit > 0)
    if len(entries) is 0:
        return None
    index_last = len(entries) - 1
    for i in range(index_last, max(index_last - search_limit, -1), -1):
        if entries[i].can_id == can_id:
            return entries[i]
    return None


# _____________________________________________________________________________________________________
#
# main
# _____________________________________________________________________________________________________

assert (len(sys.argv) > 1)
file_name = sys.argv[-1]

with open(file_name) as f:
    f = f.readlines()

entries = []
'''

m = list2matrix([0,1,2,3,4,5,6,7], 5)
print(m)
'''
field_names = gen_field_names()
start_time = time.time()
dict_list = []
for line in f:
    words = line.split(" ")
    time_stamp = float(words[0][1:-1])
    time_interval = get_time_interval(time_stamp)
    data = words[2].split("#")
    label = words[3][:-1]
    label = [0.0, 1.0] if label == "0" else [1.0, 0.0]
    can_id = hex2int(data[0])
    can_id_bin = binary_encode(can_id, ID_BIT_LEN)
    id_priority = 1.0 - float(can_id / 2 ** ID_BIT_LEN)
    can_data_str = data[1][:-1]
    can_data = get_can_data(can_data_str)
    compressed_data = compress_can_data(can_data)
    can_data_matrix = list2matrix(can_data, 8)
    can_data_trimmed = get_changed_values(can_id, can_data)
    time_interval_for_id = get_time_interval_for_id(can_id, time_stamp)
    e = Entry(label, can_id, can_id_bin, id_priority,
              can_data, compressed_data, can_data_matrix,
              can_data_trimmed, time_interval, time_stamp,
              time_interval_for_id)
    dict_list.append(dict(list(zip(field_names, e.get_trimmed_data()))))
    entries.append(e)
    '''
    print(e)
    print(dict_list[-1])
    if len(entries) > SAMPLE_SIZE:
        print("Reached SAMPLE_SIZE limit")
        break
    #'''
# print("Processed " + str(SAMPLE_SIZE) + " entries in " +str(time.time() - start_time)[0:4] + " seconds")
print(("Processed entries in " + str(time.time() - start_time)[0:4] + " seconds"))


# ____________________________________________________________________________________________________
#
# write to CSV
# _____________________________________________________________________________________________________


def csv_dict_writer(path, fieldnames, data):
    """
    Writes a CSV file using DictWriter
    """
    with open(path, "w") as out_file:
        writer = csv.DictWriter(out_file, delimiter=',', fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow(row)


start_time = time.time()

path = str(time.time()).replace(".", "") + "data.csv"
csv_dict_writer(path, field_names, dict_list)

print(("Wrote CSV file in " + str(time.time() - start_time)[0:4] + " seconds"))

