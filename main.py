# -*- coding:utf-8 -*-
"""
@SoftWare: PyCharm
@Project: FTPCrawler
@Author: 蜀山徐长卿
@File: main.py
@Time: 2024/6/12 15:29
"""
from handle_api import FTPCrawler

if __name__ == '__main__':
    ftp_1 = FTPCrawler(host='gnss.bev.gv.at', path='/pub/obs', start_date='20240401', end_date='20240401', prefixes=['DNMU', 'GLSV', 'MIKL', 'POLV', 'SULP'],
                       save_dirname='乌克兰', replace_suffixes={'obs_suffix': '_30S_MO.crx', 'nav_suffix': '_MN.rnx', 'pos_suffix': '_30S_MO.pos'})
    ftp_1.process()
    ftp_2 = FTPCrawler(host='igs.gnsswhu.cn', path='/pub/gps/data/daily', attach_fixed_paths=['24o', '24n'], start_date='20240401', end_date='20240401',
                       prefixes=['bshm', 'drag', 'ramo'], save_dirname='以色列',
                       replace_suffixes={'obs_suffix': '.24o', 'nav_suffix': '.24n', 'pos_suffix': '.pos'})
    ftp_2.process()
