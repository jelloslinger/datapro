# -*- coding: utf-8 -*-

from copy import deepcopy

import pytz


def dict_merge(master, merge):
    """Recursively merge dicts
    (originally found at https://www.xormedia.com/recursively-merge-dictionaries-in-python/)

    Args:
        master (dict): base dictionary
        merge (dict): dictionary with entries to be merged into the base dictionary

    Returns:
        dict: resulting dictionary from `merge` merged into `master`
    """
    result = deepcopy(master)
    for k, v in iter(merge.items()):
        if k in result and isinstance(result[k], dict) and isinstance(merge[k], dict):
            result[k] = dict_merge(result[k], merge[k])
        else:
            result[k] = deepcopy(v)
    return result


def to_utc(dt, tz, is_dst=False):
    # TODO - cleanup docstring / is this the right spot for this function?
    """
    Takes in a naive datetime and timezone, and returns a naive datetime, converted to UTC.
    Note that the nature of DST means that dates will be off by one hour, for one hour per year (if the given tz is DST-aware).
    This is because, during roll-back, an hour occurs twice, and we don't know which hour (before or after the daylight savings switch) a naive datetime is talking about.
    Naive: 12:30am (DST=True) -> 1:30am (DST=True) -> 1:30am (DST=False) -> 2:30am (DST=False)
    UTC:    4:30am            -> 5:30am            -> 6:30am             -> 7:30am
    If we're guessing that is_dst is off, it means UTC 6am-7am happens twice (which is wrong!), just like Eastern 1am-2am
    """
    return dt - pytz.timezone(tz).utcoffset(dt, is_dst=is_dst)