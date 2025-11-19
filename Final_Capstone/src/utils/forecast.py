import numpy as np


def simple_forecast(avg_daily, days_ahead=3):
    # avg_daily may be a scalar or list
    if hasattr(avg_daily, '__iter__'):
        arr = np.array(avg_daily[-30:])
        daily = float(arr.mean()) if len(arr)>0 else 0.0
    else:
        daily = float(avg_daily or 0.0)
    return int(np.ceil(daily * days_ahead))