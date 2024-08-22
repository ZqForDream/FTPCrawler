# -*- coding:utf-8 -*-
"""
@SoftWare: PyCharm
@Project: FTPCrawler
@Author: 蜀山徐长卿
@File: main.py
@Time: 2024/6/12 15:29
"""
from time import sleep

from handle_api import FTPCrawler

if __name__ == '__main__':
    while True:
        try:
            ftp_1 = FTPCrawler(host='gnss.bev.gv.at', path='/pub/obs', start_date='20240101', end_date='20240103', prefixes=['DNMU', 'GLSV', 'MIKL', 'POLV', 'SULP'],
                               save_dirname='乌克兰', replace_suffixes={'obs_suffix': '_30S_MO.crx', 'nav_suffix': '_MN.rnx', 'pos_suffix': '_30S_MO.pos'})
            ftp_1.download_process()
            # ftp_1.parse_process()
        except:
            sleep(30)
            continue
        break

    while True:
        try:
            ftp_2 = FTPCrawler(host='igs.gnsswhu.cn', path='/pub/gps/data/daily', attach_fixed_paths=['o', 'n'], start_date='20240101', end_date='20240103',
                               prefixes=['bshm', 'drag', 'ramo'], save_dirname='以色列',
                               replace_suffixes={'obs_suffix': '.o', 'nav_suffix': '.n', 'pos_suffix': '.pos'})
            ftp_2.download_process()
            # ftp_2.parse_process()
        except:
            sleep(30)
            continue
        break
