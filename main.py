# -*- coding:utf-8 -*-
"""
@SoftWare: PyCharm
@Project: FTPCrawler
@Author: 蜀山徐长卿
@File: main.py.py
@Time: 2024/4/26 下午4:19
"""

import ftplib
import os.path

from datetime import datetime, timedelta


class FTPCrawler:
    def __init__(self, host='localhost', path='/', username='anonymous', password='anonymous', start_date='', end_date='', prefixs: list = None):
        if prefixs is None:
            prefixs = []
        self.host = host
        self.path = path
        self.username = username
        self.password = password
        self.start_date = start_date
        self.end_date = end_date
        self.prefixs = prefixs
        self.cache_date, self.cache_year, self.cache_day = None, None, None

        self.ftp = ftplib.FTP(self.host)
        self.login()

        if start_date == '' or len(start_date) != 8:
            self.start_date = datetime.now().strftime('%Y%m%d')
        if end_date == '' or len(start_date) != 8:
            self.end_date = datetime.now().strftime('%Y%m%d')
        print('下载日期范围:', self.start_date, '-', self.end_date)
        self.start_year, self.start_day = self.date_analysis(self.start_date)
        self.end_year, self.end_day = self.date_analysis(self.end_date)

        if not os.path.exists('.cache'):
            os.mkdir('.cache')
        self.cache_filename = f'.cache/{host}'
        if not os.path.exists(self.cache_filename):
            with open(self.cache_filename, 'w'):
                print('创建缓存文件:', self.cache_filename)

    def login(self):
        try:
            self.ftp.login(self.username, self.password)
            print(f'登录FTP成功：{self.host}')
        except ftplib.all_errors as e:
            print(f'登录FTP失败: {e}')

    def date_analysis(self, date_string):
        # 将日期字符串转换为datetime对象
        date_obj = datetime.strptime(date_string, '%Y%m%d')

        # 获取当年的开始日期
        current_year = datetime.now().year
        start_of_year = datetime(current_year, 1, 1)

        # 计算日期在当年的天数
        days_in_year = (date_obj - start_of_year).days + 1

        # print(f'{date_string}是当年的第{days_in_year}天')
        return current_year, days_in_year

    def get_files_list(self):
        files = []
        try:
            self.ftp.retrlines('LIST', lambda x: files.append(x.split()))
        except EOFError:
            print('获取文件列表 [失败]')
            print('错误：FTP连接异常中断！！！')
            exit(-1)
        return files

    def make_download_dir(self, dst_folder_name):
        for prefix in self.prefixs:
            download_dir = os.path.join(dst_folder_name, prefix).replace('\\', '/')
            if not os.path.exists(download_dir):
                os.makedirs(download_dir)

    def get_cache_date(self):
        with open(self.cache_filename, 'r') as f:
            data = f.readlines()
            if len(data):
                self.cache_date = data[-1].strip('\n')
                self.cache_date = (datetime.strptime(self.cache_date, '%Y%m%d') + timedelta(days=1)).strftime('%Y%m%d')
            else:
                self.cache_date = self.start_date
        self.cache_year, self.cache_day = self.date_analysis(self.cache_date)

    def update_cache_date(self, date: str):
        with open(self.cache_filename, 'a') as f:
            f.write(date + '\n')

    def download_files(self, dst_folder_name='default', attach_src_path=''):
        self.get_cache_date()
        print(f'当前起始的下载日期：{self.cache_date}')
        for year in range(self.cache_year, self.end_year + 1):
            for day in range(self.cache_day, self.end_day + 1):
                # 切换到要下载的文件夹
                dirname = f'{year}/{format(day, "03")}'
                file_path = os.path.join(self.path, dirname, attach_src_path).replace('\\', '/')
                try:
                    self.ftp.cwd(file_path)
                    self.ftp.pwd()
                    print(f'切换到文件夹: {file_path} [成功]')
                except EOFError:
                    print(f'切换到文件夹: {file_path} [失败]')
                    print('错误：FTP连接异常中断！！！')
                    exit(-1)
                except ftplib.error_perm:
                    print(f'{file_path}文件夹不存在，跳过')
                    continue

                # 获取文件夹中的文件列表
                files_list = self.get_files_list()
                if len(files_list) == 0:
                    print(f'{file_path}文件夹还未更新，正常退出')
                    exit(0)
                # print(f'文件列表: {files_list}')
                self.make_download_dir(dst_folder_name)

                # 下载文件夹中的文件
                for file in files_list:
                    filename = file[8]
                    for prefix in self.prefixs:
                        if filename.startswith(prefix):
                            with open(os.path.join(dst_folder_name, prefix, filename).replace('\\', '/'), 'wb') as f:
                                try:
                                    self.ftp.retrbinary(f'RETR {filename}', f.write)
                                except EOFError:
                                    print(f'下载文件: {filename} [失败]')
                                    print('错误：FTP连接异常中断！！！')
                                    exit(-1)
                            print(f'下载文件: {filename} [成功]')
                            break
                self.update_cache_date(self.cache_date)
                self.cache_date = (datetime.strptime(self.cache_date, '%Y%m%d') + timedelta(days=1)).strftime('%Y%m%d')

        try:
            self.ftp.quit()
        except EOFError:
            pass
        print('关闭FTP连接')


ftp_1 = FTPCrawler(host='gnss.bev.gv.at', path='/pub/obs', start_date='20240401', end_date='20240403', prefixs=['DNMU', 'GLSV', 'MIKL', 'POLV', 'SULP'])
ftp_1.download_files('乌克兰')
ftp_2 = FTPCrawler(host='igs.gnsswhu.cn', path='/pub/gps/data/daily', start_date='20240401', end_date='20240403', prefixs=['bshm', 'drag', 'ramo'])
ftp_2.download_files('以色列', '24o')
