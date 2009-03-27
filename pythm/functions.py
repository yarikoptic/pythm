"""
Helper functions for pythm
"""


def is_numeric(val):
    try:
        val + 1
        return True
    except:
        return False

def format_time(value):
    if value < 0:
        return ""
    min = int(round(value / 60))
    sec = int(round(value % 60))
    if sec < 10:
        sec = "0" + str(sec)
    return str(min) + ":" + str(sec)
