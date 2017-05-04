# -*- coding: utf-8 -*-

import time

class error(object):

    class webpage(object):

        @staticmethod
        def no_content_at_time(content_type, timestamp):
            return 'No {type} recorded at the specified time. ({time})'.format(time=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp)),
                                                                               type=content_type)

        @staticmethod
        def no_content():
            return 'No content.'

    class main(object):
        
        @staticmethod
        def invalid_thing(name_of_thing, thing):
            return u'不合法的{}: {}。請查看使用說明。'.format(name_of_thing, thing)

        @staticmethod
        def lack_of_thing(name_of_thing):
            return u'缺少{nm}。請修正您所提供的{nm}成正確的格式。'.format(nm=name_of_thing)

        @staticmethod
        def no_result():
            return '無結果。'

        @staticmethod
        def restricted(permission=None):
            return '已限制的功能。{}'.format(
                '\n\n需求權限: {}+'.format(permission) if permission is not None else '')

        @staticmethod
        def incorrect_channel(available_in_1v1=True, available_in_room=False, available_in_group=False):
            return 'This is not available in this channel. Valid channel to execute below:\n{} {} {}'.format(
                '[ 私訊 ]' if available_in_1v1 else '[ - ]',
                '[ 群組 ]' if available_in_group else '[ - ]',
                '[ 房間 ]' if available_in_room else '[ - ]')