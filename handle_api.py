# -*- coding:utf-8 -*-
"""
@SoftWare: PyCharm
@Project: FTPCrawler
@Author: 蜀山徐长卿
@File: handle_api.py.py
@Time: 2024/4/26 下午4:19
"""

import ftplib
import gzip
import os
from datetime import datetime, timedelta
from typing import List

from pywinauto import application
from pywinauto.application import ProcessNotFoundError, Application
from pywinauto.keyboard import send_keys

from log import MyLog

log = MyLog()
current_dir = os.path.dirname(os.path.abspath(__file__))
rtkpost_path = 'tools/rtkpost.exe'
rtkplot_path = 'tools/rtkplot.exe'


def unzip(filepath: str):
    if filepath.endswith('.gz'):
        with gzip.GzipFile(filepath, 'rb') as gz:
            with open(filepath.replace('.gz', ''), 'wb') as f:
                f.write(gz.read())
            log.info(f'解压文件：{filepath} [成功]')


def open_application(app_name: str, backend: str = 'win32'):
    app = application.Application(backend=backend).start(app_name)
    main_window = app.window(class_name='TPlot')
    main_window.print_control_identifiers()


def rtkpost(obs_file: str, nav_file: str, pos_file: str):
    try:
        app = application.Application(backend='uia').connect(path=rtkpost_path)
    except ProcessNotFoundError:
        app = application.Application(backend='uia').start(rtkpost_path, work_dir=os.path.dirname(rtkpost_path))
    main_window = app.window(class_name='TMainForm')
    main_window.wait('ready', timeout=120, retry_interval=5)
    # print(main_window.print_control_identifiers())
    panel = main_window.child_window(class_name="TPanel", found_index=2).child_window(class_name="TPanel", found_index=1)
    rinex_obs_edit = panel.child_window(class_name="TComboBox", found_index=5).child_window(class_name="Edit")
    rinex_obs_edit.type_keys('^a {DEL}').type_keys(obs_file)
    rinex_nav_edit = panel.child_window(class_name="TComboBox", found_index=4).child_window(class_name="Edit")
    rinex_nav_edit.type_keys('^a {DEL}').type_keys(nav_file)
    execute_button = main_window.child_window(class_name="TPanel", found_index=1).child_window(title="Execute", class_name="TBitBtn")
    execute_button.click()
    if os.path.exists(pos_file):
        app.window(class_name='TConfDialog').child_window(title="Overwrite", class_name="TButton").click()
    execute_button.wait('exists', timeout=120, retry_interval=5)


def rtkplot(pos_file: str, obs_file: str, nav_file: str, obs_suffix: str):
    try:
        app = application.Application(backend='uia').connect(path=rtkplot_path)
    except ProcessNotFoundError:
        app = application.Application(backend='uia').start(rtkplot_path, work_dir=os.path.dirname(rtkplot_path))
    main_window = app.window(class_name='TPlot')
    tool_bar = main_window.child_window(class_name="TPanel", found_index=0).child_window(class_name="TPanel", found_index=1)
    combobox_mode = tool_bar.child_window(class_name="TPanel", found_index=2).child_window(control_type="ComboBox")
    __rtkplot_file_dlg__(app, 'File->Open Solution-1...', 'Open Solution 1', pos_file, 'open')
    __rtkplot_file_dlg__(app, 'File->Open Obs Data...', 'Open Obs/Nav Data', obs_file, 'open')
    __rtkplot_file_dlg__(app, 'File->Open Nav Data...', 'Open Obs/Nav Data', nav_file, 'open')
    combobox_mode.select('Position')
    __rtkplot_file_dlg__(app, 'File->Save Image...', 'Save Image', obs_file.replace(obs_suffix, '_Position.jpg'), 'save')
    # 界面发生变化，需要重新获取控件
    combobox_mode = tool_bar.child_window(class_name="TPanel", found_index=3).child_window(control_type="ComboBox")
    combobox_mode.select('Residuals')
    __rtkplot_file_dlg__(app, 'File->Save Image...', 'Save Image', obs_file.replace(obs_suffix, '_Residuals.jpg'), 'save')
    combobox_mode.select('SNR/MP/EL')
    combobox_frequency_point = tool_bar.child_window(class_name="TPanel", found_index=1).child_window(control_type="ComboBox")
    # 必须要expand才能获取到下拉框中的值
    combobox_frequency_point.expand()
    frequency_point_texts = combobox_frequency_point.wrapper_object().expand().children(control_type='List')[0].children_texts()
    # 调用uia_controls.py中的ComboBoxWrapper类的select方法，combobox_frequency_point需为ComboBoxWrapper对象才可调用此select方法，
    # 通过查看源码分析得出，WindowSpecification类中的wrapper_object()可获得ComboBoxWrapper对象,获取后即与select方法中的self相同
    for fpt in frequency_point_texts:
        combobox_frequency_point.expand().select(fpt)
        __rtkplot_file_dlg__(app, 'File->Save AZ/EL/SNR/MP...', 'Save Data', obs_file.replace(obs_suffix, '_' + fpt + '.txt'), 'save')


def __rtkplot_file_dlg__(app: Application, menu_option: str, file_dlg_title: str, filepath: str, option: str):
    main_window = app.window(class_name='TPlot')
    main_window.wait('ready', timeout=120, retry_interval=5)
    menu_item = main_window.child_window(title='应用程序', control_type="MenuBar").child_window(title="File", control_type="MenuItem")
    main_window.menu_select(menu_option)
    file_dlg = app.window(title=file_dlg_title)
    file_dlg.wait('ready', timeout=120, retry_interval=5)
    file_dlg.child_window(class_name="Edit").type_keys(filepath)
    send_keys('{ENTER}')
    if os.path.exists(filepath) and filepath.endswith('.txt') and option == 'save':
        file_dlg.child_window(title='确认另存为').child_window(title="是(Y)", control_type="Button").click()
        log.info(f'保存[{filepath}]')
    menu_item.wait('enabled', timeout=120, retry_interval=5)


def date_analysis(date_string: str):
    # 将日期字符串转换为datetime对象
    date_obj = datetime.strptime(date_string, '%Y%m%d')

    # 获取当年的开始日期
    current_year = date_obj.year
    start_of_year = datetime(current_year, 1, 1)

    # 计算日期在当年的天数
    days_in_year = (date_obj - start_of_year).days + 1

    # log.info(f'{date_string}是当年的第{days_in_year}天')
    return current_year, days_in_year


def get_date(year: int, day: int) -> str:
    start_of_year = datetime(year, 1, 1)
    date = start_of_year + timedelta(days=day - 1)
    return date.strftime('%Y%m%d')


def get_file_data(filename):
    data = []
    with open(filename, 'r') as f:
        for line in f.readlines():
            data.append(line.strip('\n'))
    return data


def update_file_data(filename: str, data: str):
    with open(filename, 'a') as f:
        f.write(data + '\n')


class FTPCrawler:
    def __init__(self, host='localhost', path='/', attach_fixed_paths: List[str] = None, username='anonymous', password='anonymous', start_date='', end_date='',
                 prefixes: List[str] = None, save_dirname='default', replace_suffixes: dict = None):
        if replace_suffixes is None:
            log.error('错误：请指定参数[replace_suffixes]')
            return
        self.__host = host
        self.__path = path
        self.__attach_fixed_paths = attach_fixed_paths if attach_fixed_paths is not None else ['']
        self.__username = username
        self.__password = password
        self.__start_date = start_date if start_date != '' else datetime.now().strftime('%Y%m%d')
        self.__end_date = end_date if end_date != '' else datetime.now().strftime('%Y%m%d')
        self.__prefixes = prefixes if prefixes is not None else ['']
        self.__save_dirname = save_dirname
        self.__replace_suffixes = replace_suffixes

        if (len(self.__start_date) != 8) or (len(self.__end_date) != 8):
            log.error('错误：请输入8位数字格式日期，例如：20230101')
            return
        if datetime.strptime(self.__start_date, "%Y%m%d") > datetime.strptime(self.__end_date, "%Y%m%d"):
            log.error('错误：开始日期大于结束日期')
            return

        self.__ftp = None

        log.info(f'下载日期范围：[{self.__start_date}-{self.__end_date}]')
        # 解析日期
        self.__start_year, self.__start_day = date_analysis(self.__start_date)
        self.__end_year, self.__end_day = date_analysis(self.__end_date)
        self.__current_year, self.__current_day = date_analysis(datetime.now().strftime('%Y%m%d'))
        self.__datetime_list = []
        if self.__start_year == self.__end_year:
            for day in range(self.__start_day, self.__end_day + 1):
                self.__datetime_list.append((self.__start_year, day))
        elif self.__start_year < self.__end_year:
            for year in range(self.__start_year, self.__end_year + 1):
                max_day = date_analysis(f'{year}1231')[1]
                if year == self.__start_year:
                    for day in range(self.__start_day, max_day + 1):
                        self.__datetime_list.append((year, day))
                elif year == self.__end_year:
                    for day in range(1, self.__end_day + 1):
                        self.__datetime_list.append((year, day))
                else:
                    for day in range(1, max_day + 1):
                        self.__datetime_list.append((year, day))
        else:
            log.error('开始日期不能大于结束日期')
            raise Exception('开始日期不能大于结束日期')
        # 创建日期缓存文件
        if not os.path.exists('.cache'):
            os.mkdir('.cache')

    def __get_files_list(self):
        files = []
        try:
            self.__ftp.retrlines('LIST', lambda x: files.append(x.split()))
        except EOFError:
            log.error('获取文件列表 [失败]')
            log.error('错误：FTP连接异常中断！！！')
            raise Exception('获取文件列表 [失败]')
        return files

    def __make_download_dir(self, dst_folder_name: str):
        for prefix in self.__prefixes:
            download_dir = os.path.join(dst_folder_name, prefix).replace('\\', '/')
            if not os.path.exists(download_dir):
                os.makedirs(download_dir)

    def download_process(self, decompress=True, fixed_download_count=6):
        """

        @param decompress: 对下载的数据文件是否进行解压
        @param fixed_download_count: 当下载的某一日期没有匹配到任何数据文件时，最多下载此次数，直至有匹配的数据文件
        """
        try:
            self.__ftp = ftplib.FTP(self.__host)
            self.__ftp.login(self.__username, self.__password)
            log.info(f'登录FTP成功：[{self.__host}]')
        except ftplib.all_errors as e:
            log.error(f'登录FTP失败: {e}')
            raise Exception(f'登录FTP失败: {e}')
        for date in self.__datetime_list:
            for year, day in date:
                for attach_fixed_path in self.__attach_fixed_paths:
                    if not self.__download_process(year, day, attach_fixed_path, decompress, fixed_download_count):
                        self.__ftp.quit()
                        return
        self.__ftp.quit()
        log.info('关闭FTP连接')

    def parse_process(self):
        for _ in self.__datetime_list:
            self.__data_parsing()

    def __download_process(self, year: int, day: int, attach_fixed_path: str, decompress: bool, fixed_download_count: int) -> bool:
        if attach_fixed_path == '':
            cache_filename = f'.cache/download-{self.__host}'
        else:
            cache_filename = f'.cache/download-{self.__host}[{attach_fixed_path}]'
        if not os.path.exists(cache_filename):
            with open(cache_filename, 'w'):
                log.info(f'创建下载日期缓存文件：[{cache_filename}]')
        cache_file_data = get_file_data(cache_filename)
        # 获取已缓存的日期
        cache_date = [date.split(',')[0] for date in cache_file_data]
        download_date = get_date(year, day)
        if year >= self.__current_year and day >= self.__current_day:
            log.info(f'下载日期大于等于当前日期：[{download_date}]，退出')
            return False
        if download_date in cache_date:
            current_count = cache_file_data.count(download_date + ',0')
            if (download_date + ',0') in cache_file_data and current_count < fixed_download_count:
                log.info(f'[{cache_filename}]已存在下载日期{current_count}次：[{download_date},0]，进行第{current_count + 1}次下载')
            elif (download_date + ',0') in cache_file_data and current_count >= fixed_download_count:
                log.info(f'[{cache_filename}]已存在下载日期{current_count}次：[{download_date},0]，超过固定下载次数，跳过')
                return True
            else:
                log.info(f'[{cache_filename}]已存在下载日期：[{download_date}]，跳过')
                return True
        # 切换到要下载的文件夹
        dirname = f'{year}/{format(day, "03")}'
        file_path = os.path.join(self.__path, dirname, attach_fixed_path).replace('\\', '/')
        try:
            self.__ftp.cwd(file_path)
            self.__ftp.pwd()
            log.info(f'切换到文件夹: {file_path} [成功]')
        except EOFError:
            log.error(f'切换到文件夹: {file_path} [失败]')
            log.error('错误：FTP连接异常中断！！！')
            raise Exception('FTP连接异常中断！！！')
        except (ftplib.error_reply, ftplib.error_perm, ftplib.error_temp, ftplib.error_proto) as e:
            log.error(f'错误：{e}')
            raise Exception(f'错误：{e}')

        # 获取文件夹中的文件列表
        files_list = self.__get_files_list()
        if len(files_list) == 0:
            log.info(f'文件夹为空：[{file_path}]，跳过')
            return True
        # log.info(f'文件列表: {files_list}')
        self.__make_download_dir(self.__save_dirname)
        self.__download_files(cache_filename, file_path, files_list, decompress, download_date)
        return True

    def __download_files(self, cache_filename: str, file_path: str, files_list: List[str], decompress: bool, download_date: str):
        # 下载文件夹中的文件
        count = 0
        for file in files_list:
            filename = file[8]
            for prefix in self.__prefixes:
                if prefix == 'SULP' and self.__replace_suffixes.get('nav_suffix'):
                    self.__replace_suffixes['nav_suffix'] = '_30S_MN.rnx'
                elif prefix != 'SULP' and self.__replace_suffixes.get('nav_suffix'):
                    self.__replace_suffixes['nav_suffix'] = '_MN.rnx'
                if filename.startswith(prefix):
                    if filename.endswith(self.__replace_suffixes.get('obs_suffix') + '.gz'):
                        new_folder_name = filename.replace(self.__replace_suffixes.get('obs_suffix') + '.gz', '')
                    elif filename.endswith(self.__replace_suffixes.get('nav_suffix') + '.gz'):
                        new_folder_name = filename.replace(self.__replace_suffixes.get('nav_suffix') + '.gz', '')
                    else:
                        return
                    new_dirname = os.path.join(self.__save_dirname, prefix, new_folder_name)
                    if not os.path.exists(new_dirname):
                        os.makedirs(new_dirname)
                    filepath = os.path.join(new_dirname, filename)
                    with open(filepath, 'wb') as f:
                        try:
                            self.__ftp.retrbinary(f'RETR {filename}', f.write)
                        except EOFError:
                            log.error(f'下载文件: {filepath} [失败]')
                            log.error('错误：FTP连接异常中断！！！')
                            exit(-1)
                    log.info(f'下载文件: {filepath} [成功]')
                    # 解压
                    if decompress:
                        unzip(filepath)
                    count += 1
                    break
        if count == 0:
            log.info(f'文件夹中未找到匹配文件：[{file_path}]')
        else:
            log.info(f'文件夹中找到{count}个匹配文件：[{file_path}]')
        # 更新缓存日期
        date = ','.join([download_date, str(count)])
        update_file_data(cache_filename, date)
        log.info(f'[{cache_filename}]更新缓存日期：{date}')

    def __data_parsing(self):
        # 解析数据
        cache_filename = f'.cache/parsing-{self.__host}'
        if not os.path.exists(cache_filename):
            with open(cache_filename, 'w'):
                log.info(f'创建解析数据缓存文件：[{cache_filename}]')
        file_lst = get_file_data(cache_filename)
        for prefix in self.__prefixes:
            dirname = os.path.join(self.__save_dirname, prefix)
            for son_dir in os.listdir(dirname):
                for file in os.listdir(os.path.join(dirname, son_dir)):
                    if prefix == 'SULP' and self.__replace_suffixes.get('nav_suffix'):
                        self.__replace_suffixes['nav_suffix'] = '_30S_MN.rnx'
                    elif prefix != 'SULP' and self.__replace_suffixes.get('nav_suffix'):
                        self.__replace_suffixes['nav_suffix'] = '_MN.rnx'
                    if file.endswith(self.__replace_suffixes.get('obs_suffix')) and file.replace(
                            self.__replace_suffixes.get('obs_suffix'), self.__replace_suffixes.get('nav_suffix')) in os.listdir(os.path.join(dirname, son_dir)):
                        if file in file_lst:
                            log.info(f'[{cache_filename}]已存在缓存文件名：[{file}]，跳过')
                            continue
                        obs_file = os.path.join(current_dir, os.path.join(dirname, son_dir), file)
                        nav_file = os.path.join(current_dir, os.path.join(dirname, son_dir),
                                                file.replace(self.__replace_suffixes.get('obs_suffix'), self.__replace_suffixes.get('nav_suffix')))
                        pos_file = os.path.join(current_dir, os.path.join(dirname, son_dir),
                                                file.replace(self.__replace_suffixes.get('obs_suffix'), self.__replace_suffixes.get('pos_suffix')))
                        log.info(f'rtkpost.exe开始解析：[{obs_file}], [{nav_file}]')
                        rtkpost(obs_file, nav_file, pos_file)
                        log.info('rtkplot.exe开始另存为')
                        rtkplot(pos_file, obs_file, nav_file, self.__replace_suffixes.get('obs_suffix'))
                        update_file_data(cache_filename, file)
                        log.info(f'[{cache_filename}]更新缓存文件名：[{file}]')
