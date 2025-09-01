import datetime as dt

def business_seconds(start: dt.datetime, end: dt.datetime, bh_start=9, bh_end=17, bh_days={0,1,2,3,4}) -> int:
    if end <= start:
        return 0
    total = 0
    cur = start
    while cur.date() <= end.date():
        day_start = cur.replace(hour=bh_start, minute=0, second=0, microsecond=0)
        day_end = cur.replace(hour=bh_end, minute=0, second=0, microsecond=0)
        if day_start.date() != cur.date():
            day_start = dt.datetime.combine(cur.date(), dt.time(bh_start, 0, 0, tzinfo=cur.tzinfo))
            day_end = dt.datetime.combine(cur.date(), dt.time(bh_end, 0, 0, tzinfo=cur.tzinfo))
        if cur.weekday() in bh_days:
            s = max(cur, day_start)
            e = min(end, day_end)
            if e > s:
                total += int((e - s).total_seconds())
        cur = (cur + dt.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return total
