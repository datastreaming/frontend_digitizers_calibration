import bisect


def find_minmax(data, window_size=21):

    min_val = None
    max_val = None
    sorted_list = []

    # fill in the window
    for i in range(0, len(data), window_size):
        del sorted_list[:]
        if i + window_size < (len(data)):
            for j in range(i, i + window_size):
                bisect.insort_left(sorted_list, data[j])
        else:
            for j in range(len(data)-window_size, len(data)):
                bisect.insort_left(sorted_list, data[j])

        median = sorted_list[(window_size//2)+1]
        if min_val is None or median < min_val:
            min_val = median
        if max_val is None or median > max_val:
            max_val = median

    return [min_val, max_val]
