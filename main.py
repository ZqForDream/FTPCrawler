# -*- coding:utf-8 -*-
"""
@SoftWare: PyCharm
@Project: FTPCrawler
@Author: 蜀山徐长卿
@File: main.py.py
@Time: 2024/4/26 下午4:19
"""

import ftplib
import gzip
import os
from datetime import datetime, timedelta

from pywinauto import application, Application
from pywinauto.keyboard import send_keys

from log import MyLog

log = MyLog()
current_dir = os.path.dirname(os.path.abspath(__file__))


def unzip(filepath):
    if filepath.endswith('.gz'):
        with gzip.GzipFile(filepath, 'rb') as gz:
            with open(filepath.replace('.gz', ''), 'wb') as f:
                f.write(gz.read())
            log.info(f'解压文件：{filepath} [成功]')


def open_application():
    app = application.Application(backend='uia').start('rtkplot.exe')
    return app


def obs_save2_txt(app: Application, file_fullpath: str):
    main_window = app.window(class_name='TPlot')
    main_window.wait('ready')
    send_keys('^o')
    file_dlg = app.window(title='Open Obs/Nav Data')
    file_dlg.wait('ready')
    file_dlg.child_window(class_name="Edit").type_keys(file_fullpath.replace('.gz', ''))
    send_keys('{ENTER}')
    main_window.wait('ready')
    main_window.menu_select('File->Save AZ/EL/SNR/MP ...')
    file_dlg = app.window(title='Save Data')
    file_dlg.wait('ready')
    file_dlg.child_window(class_name="Edit").type_keys(file_fullpath.replace('.24o.gz', ''))
    send_keys('{ENTER}')


def date_analysis(date_string):
    # 将日期字符串转换为datetime对象
    date_obj = datetime.strptime(date_string, '%Y%m%d')

    # 获取当年的开始日期
    current_year = datetime.now().year
    start_of_year = datetime(current_year, 1, 1)

    # 计算日期在当年的天数
    days_in_year = (date_obj - start_of_year).days + 1

    # log.info(f'{date_string}是当年的第{days_in_year}天')
    return current_year, days_in_year


def get_date(year: int, day: int) -> str:
    start_of_year = datetime(year, 1, 1)
    date = start_of_year + timedelta(days=day - 1)
    return date.strftime('%Y%m%d')


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
        self.cache_date, self.cache_year, self.cache_day = [], None, None

        self.ftp = ftplib.FTP(self.host)
        self.login()

        if start_date == '':
            self.start_date = datetime.now().strftime('%Y%m%d')
        if end_date == '':
            self.end_date = datetime.now().strftime('%Y%m%d')
        if start_date != '' and len(start_date) != 8:
            log.error(f'start_date格式错误：{start_date}')
            exit(-1)
        if end_date != '' and len(end_date) != 8:
            log.error(f'end_date格式错误：{end_date}')
            exit(-1)
        log.info(f'下载日期范围:{self.start_date}-{self.end_date}')
        self.start_year, self.start_day = date_analysis(self.start_date)
        self.end_year, self.end_day = date_analysis(self.end_date)

        if not os.path.exists('.cache'):
            os.mkdir('.cache')
        self.cache_filename = f'.cache/{host}'
        if not os.path.exists(self.cache_filename):
            with open(self.cache_filename, 'w'):
                log.info(f'创建缓存文件:.cache/{self.cache_filename}')
        if host == 'igs.gnsswhu.cn':
            self.app = open_application()

    def login(self):
        try:
            self.ftp.login(self.username, self.password)
            log.info(f'登录FTP成功：{self.host}')
        except ftplib.all_errors as e:
            log.info(f'登录FTP失败: {e}')

    def get_files_list(self):
        files = []
        try:
            self.ftp.retrlines('LIST', lambda x: files.append(x.split()))
        except EOFError:
            log.error('获取文件列表 [失败]')
            log.error('错误：FTP连接异常中断！！！')
            exit(-1)
        return files

    def make_download_dir(self, dst_folder_name):
        for prefix in self.prefixs:
            download_dir = os.path.join(dst_folder_name, prefix).replace('\\', '/')
            if not os.path.exists(download_dir):
                os.makedirs(download_dir)

    def get_cache_date(self):
        with open(self.cache_filename, 'r') as f:
            lines = [x.strip('\n') for x in f.readlines()]
        for line in lines:
            self.cache_date.append(line.split(',')[0] if len(line.split(',')) else 'None')

    def update_cache_date(self, date: str):
        if date in self.cache_date:
            return
        with open(self.cache_filename, 'a') as f:
            f.write(date + '\n')
            log.info(f'更新缓存日期：{date}')

    def download_files(self, dst_folder_name='default', attach_src_path=''):
        self.get_cache_date()
        for year in range(self.start_year, self.end_year + 1):
            for day in range(self.start_day, self.end_day + 1):
                current_date = get_date(year, day)
                if current_date in self.cache_date:
                    log.info(f'{current_date}日期已存在，跳过')
                    continue
                # 切换到要下载的文件夹
                dirname = f'{year}/{format(day, "03")}'
                file_path = os.path.join(self.path, dirname, attach_src_path).replace('\\', '/')
                try:
                    self.ftp.cwd(file_path)
                    self.ftp.pwd()
                    log.info(f'切换到文件夹: {file_path} [成功]')
                except EOFError:
                    log.error(f'切换到文件夹: {file_path} [失败]')
                    log.error('错误：FTP连接异常中断！！！')
                    exit(-1)
                except ftplib.error_perm:
                    log.info(f'{file_path}文件夹不存在，跳过')
                    continue

                # 获取文件夹中的文件列表
                files_list = self.get_files_list()
                if len(files_list) == 0:
                    log.info(f'{file_path}文件夹还未更新，跳过')
                    continue
                # log.info(f'文件列表: {files_list}')
                self.make_download_dir(dst_folder_name)

                # 下载文件夹中的文件
                count = 0
                for file in files_list:
                    filename = file[8]
                    for prefix in self.prefixs:
                        if filename.startswith(prefix):
                            filepath = os.path.join(dst_folder_name, prefix, filename)
                            with open(filepath, 'wb') as f:
                                try:
                                    self.ftp.retrbinary(f'RETR {filename}', f.write)
                                except EOFError:
                                    log.error(f'下载文件: {filepath} [失败]')
                                    log.error('错误：FTP连接异常中断！！！')
                                    exit(-1)
                            log.info(f'下载文件: {filepath} [成功]')
                            unzip(filepath)
                            if '24o' in filename:
                                obs_save2_txt(self.app, os.path.join(current_dir, filepath))
                            count += 1
                            break
                if count == 0:
                    log.info(f'{file_path}文件夹中未找到匹配文件')
                else:
                    log.info(f'{file_path}文件夹中找到{count}个匹配文件')
                self.update_cache_date(','.join([current_date, str(count)]))

        try:
            self.ftp.quit()
        except EOFError:
            pass
        log.info('关闭FTP连接')


if __name__ == '__main__':
    ftp_1 = FTPCrawler(host='gnss.bev.gv.at', path='/pub/obs', start_date='20240513', prefixs=['DNMU', 'GLSV', 'MIKL', 'POLV', 'SULP'])
    ftp_1.download_files('乌克兰')
    ftp_2 = FTPCrawler(host='igs.gnsswhu.cn', path='/pub/gps/data/daily', start_date='20240513', prefixs=['bshm', 'drag', 'ramo'])
    ftp_2.download_files('以色列', '24o')
