# -*- coding: utf-8 -*-
from enum import Enum
from error import error
from cgi import escape
from collections import defaultdict

import traceback

import time
from datetime import datetime, timedelta
from flask import request, url_for, render_template

from linebot.models import TextSendMessage

class webpage(object):
    def __init__(self):
        self._error_route = 'Error'
        self._query_route = 'FullQuery'
        self._info_route = 'FullInfo'
        self._text_route = 'Text'
        self._page_content = {self._error_route: defaultdict(unicode), 
                              self._query_route: defaultdict(unicode), 
                              self._info_route: defaultdict(unicode), 
                              self._text_route: defaultdict(unicode)}

    def rec_error(self, err_sum, channel_id):
        timestamp = str(int(time.time()))
        err_detail = u'錯誤發生時間: {}\n'.format(datetime.now() + timedelta(hours=8))
        err_detail += u'頻道ID: {}'.format(channel_id)
        err_detail += u'\n\n'
        err_detail += traceback.format_exc().decode('utf-8')

        print err_detail.encode('utf-8')
        self._page_content[self._error_route][timestamp] = err_detail

        err_list = u'詳細錯誤URL: {}\n錯誤清單: {}'.format(
            request.url_root + url_for('get_error_message', timestamp=timestamp)[1:],
            request.url_root + url_for('get_error_list')[1:])
        
        return err_sum + u'\n\n' + err_list
    
    def rec_query(self, full_query):
        timestamp = str(int(time.time()))
        self._page_content[self._query_route][timestamp] = full_query
        return request.url_root + url_for('full_query', timestamp=timestamp)[1:]
    
    def rec_info(self, full_info):
        timestamp = str(int(time.time()))
        self._page_content[self._info_route][timestamp] = full_info
        return request.url_root + url_for('full_info', timestamp=timestamp)[1:]
    
    def rec_text(self, textmsg_list):
        if not isinstance(textmsg_list, (list, tuple)):
            textmsg_list = [textmsg_list]
    
        timestamp = str(int(time.time()))
        self._page_content[self._text_route][timestamp] = u'\n===============================\n'.join([u'【Message {}】\n\n{}'.format(index, txt.text) for index, txt in enumerate(textmsg_list, start=1)])
        return request.url_root + url_for('full_content', timestamp=timestamp)[1:]

    def error_timestamp_list(self):
        sorted_list = sorted(self._page_content[self._error_route].keys(), key=self._page_content[self._error_route].get, reverse=True)
        return sorted_list

    def get_content(self, type, timestamp):
        timestamp = str(timestamp)
        content = None
        if type == content_type.Error:
            content = self._page_content[self._error_route].get(timestamp)
            type_chn = u'錯誤'
        elif type == content_type.Query:
            content = self._page_content[self._query_route].get(timestamp)
            type_chn = u'索引'
        elif type == content_type.Info:
            content = self._page_content[self._info_route].get(timestamp)
            type_chn = u'查詢詳細資料'
        elif type == content_type.Text:
            content = self._page_content[self._text_route].get(timestamp)
            type_chn = u'回傳文字'

        if content is None:
            return error.webpage.no_content_at_time(type_chn, float(timestamp))
        else:
            return content

    @staticmethod
    def html_render(content, title=None):
        return render_template('WebPage.html', Contents=content.replace(' ', '&nbsp;').split('\n'), Title=title)

    @staticmethod
    def html_render_error_list(boot_up, error_dict):
        """
        Error dict 
        key=timestamp
        value=URL
        """
        return render_template('ErrorList.html', boot_up=boot_up, ErrorDict=error_dict)

class content_type(Enum):
    Error = 0
    Query = 1
    Info = 2
    Text = 3


