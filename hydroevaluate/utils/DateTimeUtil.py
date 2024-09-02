# -*- coding: utf-8 -*-
# @Author  : gaoyu
# @Time    : 2023/6/5 1:35 PM
# @Function:
import calendar
import datetime
import re
import time

import numpy as np
from dateutil.relativedelta import relativedelta


def str_to_date(_date_time_str):
    """
    字符串转日期
    如果存在 / 转为 -
    把日期空格后的时分秒去掉
    :param _date_time_str:
    :return:
    """
    _date_time_str = _date_time_str.replace("/", "-")
    _date_time_str = re.sub(r' .*', "", _date_time_str)
    return datetime.datetime.strptime(_date_time_str, '%Y-%m-%d')


def str_to_date_time(_date_time_str):
    """
    字符串转日期
    如果存在 / 转为 -
    把日期空格后的时分秒去掉
    :param _date_time_str:
    :return:
    """
    try:
        _date_time_str = _date_time_str.replace("/", "-")
        _date_time_str = re.sub(r'\..*', "", _date_time_str)
        return datetime.datetime.strptime(_date_time_str, '%Y-%m-%d %H:%M:%S')
    except Exception as e:
        # logger.error(e)
        _date_time_str = _date_time_str.replace("/", "-")
        _date_time_str = re.sub(r' .*', "", _date_time_str)
        return datetime.datetime.strptime(_date_time_str, '%Y-%m-%d')


def date_time_minute():
    """
        :return: 当前时间   时分秒
    """
    return datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M')


def date_time_second():
    """
        :return: 当前时间   时分秒
    """
    return datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')


def now():
    """

    :return: 当前时间
    """
    return datetime.datetime.now()


def date_time():
    """
        :return: 当前时间   时分秒
    """
    return datetime.datetime.strftime(now(), '%Y-%m-%d %H:%M:%S')


def year():
    """
        :return: 当前时间   时分秒
    """
    return datetime.datetime.strftime(now(), '%Y')


def month():
    """
        :return: 当前时间   时分秒
    """
    return datetime.datetime.strftime(now(), '%m')


def date_time_str(_time):
    """
        :return: 当前时间   时分秒
    """
    try:
        return datetime.datetime.strftime(_time, '%Y-%m-%d %H:%M:%S')
    except:
        return datetime.datetime.strftime(str_to_date_time(str(_time).rstrip().lstrip()), '%Y-%m-%d %H:%M:%S')


def date_to_str(_time):
    return datetime.datetime.strftime(_time, '%Y-%m-%d')


def time_stamp():
    return int(time.time())


def date_time_to_time_stamp(dt):
    """
    转为java13位时间戳
    Args:
        dt: 时间

    Returns:

    """
    try:
        time_array = time.strptime(str(dt), "%Y-%m-%d %H:%M:%S")
    except:
        time_array = time.strptime(str(dt), '%Y-%m-%d %H:%M:%S.%f')
    _time_stamp = time.mktime(time_array)
    return int(_time_stamp * 1000)


def date_time_to_time_diff(dt1, dt2):
    """
    时间戳相减
    Args:
        dt1: 时间1
        dt2: 时间2

    Returns:

    """
    return date_time_to_time_stamp(dt1) - date_time_to_time_stamp(dt2)


def date_time_to_time_current_diff(dt1):
    """
    时间戳与当前相减
    Args:
        dt1: 时间1

    Returns:

    """
    return date_time_to_time_stamp(dt1) - time_stamp() * 1000


def numpy_datetime64_to_datetime(dt64):
    """
    numpy.datetime64转datatime
    :param dt64:
    :return:
    """
    dt64 = np.datetime64(dt64, 's')
    dt = dt64.astype(datetime.datetime)
    return date_time_str(dt)


def iterate_year(year):
    """
    取出一年内所有天
    :param year:
    :return:
    """
    start_date = datetime.date(year, 1, 1)  # 设置开始日期
    end_date = datetime.date(year, 12, 31)  # 设置结束日期

    current_date = start_date
    while current_date <= end_date:
        current_date += datetime.timedelta(days=1)

        print(
            str(current_date.strftime("%Y")) + '/' + \
            str(current_date.strftime("%m")) + '/' + \
            str(current_date.strftime("%d"))
        )


def date_conversation(year, day):
    """
    已知年份和一年中的第几天
    :param year: 年份
    :param day: 一年中的第几天
    :return: 年月日
    """
    # 输入的字符串类型的年和日转换为整型
    year = int(year)
    day = int(day)
    # first_day：此年的第一天
    # 类型：datetime
    first_day = datetime.datetime(year, 1, 1)
    # 用一年的第一天+天数-1，即可得到我们期望的日期
    # -1是因为当年的第一天也算一天
    wanted_day = first_day + datetime.timedelta(day - 1)
    # 返回需要的字符串形式的日期
    wanted_day = datetime.datetime.strftime(wanted_day, '%Y-%m-%d')
    return wanted_day


def get_month_range(year, month):
    """
    取一个月的第一天和最后一天
    :param year:
    :param month:
    :return:
    """
    # 1号是周几，和一个月有多少天
    weekday, month_range = calendar.monthrange(year, month)

    str_month = f"0{str(month)}" if len(str(month)) == 1 else str(month)
    return (
        f"{str(year)}-{str_month}-01",
        f"{str(year)}-{str_month}-{str(month_range)}",
    )


def next_day(start_date):
    """
    下一天
    :param start_date: 当前时间
    :return:
    """
    start_date += datetime.timedelta(days=1)
    return datetime.datetime.strftime(start_date, '%Y-%m-%d'), \
           datetime.datetime.strftime(start_date, '%Y'), \
           datetime.datetime.strftime(start_date, '%m'), \
           datetime.datetime.strftime(start_date, '%d')


def next_hour(start_date):
    """
    下一小时
    :param start_date: 当前时间
    :return:
    """
    start_date += datetime.timedelta(hours=1)
    # 23点判断
    return start_date, \
           datetime.datetime.strftime(start_date, '%Y%m%d') + datetime.datetime.strftime(start_date, '%H'), \
           datetime.datetime.strftime(start_date, '%Y'), \
           datetime.datetime.strftime(start_date, '%m'), \
           datetime.datetime.strftime(start_date, '%d'), \
           datetime.datetime.strftime(start_date, '%H')


def time_stamp_to_date(ts):
    """
    java时间戳转日期
    :param ts:
    :return:
    """
    ts = int(ts) / 1000
    # 转换为其他日期格式,如:"%Y-%m-%d %H:%M:%S"
    timeArray = time.localtime(ts)
    return time.strftime("%Y-%m-%d %H:%M:%S", timeArray)


def month_add(inteval: int):
    return datetime.date.today() + relativedelta(months=inteval)


def date_to_datetime(_date):
    _date_time = datetime.datetime.strftime(_date, '%Y-%m-%d %H:%M:%S')
    return datetime.datetime.strptime(_date_time, '%Y-%m-%d %H:%M:%S')


if __name__ == '__main__':
    # print(len(str(time_stamp() * 1000)))
    # print(date_time_to_time_stamp(now()))
    # print(str(date_time_second()))
    # print(str_to_date_time('2020-06-10 08:00:00.000'))
    # print(str_to_date_time('2021-10-16 13:00:00'))
    # print(str_to_date_time('2021-10-16'))
    # 测试代码
    # print(type(str_to_date_time("2000-12-28 11:30:00")))

    # print(get_month_range(2024, 2))
    # print(get_month_range(2023, 2))
    # print(get_month_range(2023, 3))
    # print(get_month_range(2023, 10))
    # print(year(), month())
    # print(type(year()), type(month()))
    # print(next_hour(datetime.datetime.strptime("2024-02-28 23:00:00", '%Y-%m-%d  %H:%M:%S')))
    # print(date_to_str(now() + datetime.timedelta(days=-30)))
    # print(date_to_str(now() + datetime.timedelta(days=1)))
    # print(time_stamp_to_date(1715616000000))
    #
    # current_date = "2024-01-01 17:00:00"
    #
    # print(int(current_date))
    # print(date_to_str(now() + datetime.timedelta(days=-30)))
    # print(date_to_str(now() + datetime.timedelta(days=1)))

    print(date_time_str(now()))
    # print(date_to_datetime(month_add(-2)))
    print(date_time_str(date_to_datetime(month_add(-2))))

    # str_path = datetime.datetime.strptime(current_date, '%Y-%m-%d %H:%M:%S')
    # str_path = datetime.datetime.strftime(str_path, '%Y_%m_%d_%H')
    # print(str_path)
