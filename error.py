# -*- coding: utf-8 -*-

import time

class error(object):

    class webpage(object):

        @staticmethod
        def no_content_at_time(content_type, timestamp):
            return u'在指定的時間沒有{}的紀錄。 ({})'.format(content_type, time.strftime('%Y-%m-%d %H:%M:%S (%Z)', time.localtime(timestamp)))

        @staticmethod
        def no_content():
            return u'沒有內容。.'

    class main(object):
        
        @staticmethod
        def invalid_thing(name_of_thing, thing):
            return u'不合法的{}: {}。請查看使用說明。'.format(name_of_thing, thing)

        @staticmethod
        def lack_of_thing(name_of_thing):
            return u'缺少{nm}。請修正您所提供的{nm}成正確的格式。'.format(nm=name_of_thing)

        @staticmethod
        def no_result():
            return u'無結果。'

        @staticmethod
        def restricted(permission=None):
            return u'已限制的功能。{}'.format(
                '\n\n需求權限: {}+'.format(permission) if permission is not None else '')

        @staticmethod
        def incorrect_channel(available_in_1v1=True, available_in_room=False, available_in_group=False):
            return u'無法於此類型的頻道使用。請至下列頻道:\n{} {} {}'.format(
                '[ 私訊 ]' if available_in_1v1 else '[ - ]',
                '[ 群組 ]' if available_in_group else '[ - ]',
                '[ 房間 ]' if available_in_room else '[ - ]')

        @staticmethod
        def incorrect_param(param_name, correct):
            return u'無法辨認。如果要使用這個功能，{}必須為{}。'.format(param_name, correct)

        @staticmethod
        def unable_to_determine():
            return u'無法判斷指令，請檢閱使用說明書。'