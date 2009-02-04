"""
Helper functions for pythm
"""


def is_numeric(val):
    try:
        val + 1
        return True
    except Exception,e:
        return False

def format_time(value):
    if value < 0:
        return ""
    min = int(value / 60)
    sec = int(value) % 60
    if sec < 10:
        sec = "0" + str(sec)
    return str(min) + ":" + str(sec)