# -*- coding: utf-8 -*-

import time

class error(object):
    user_manual_url = 'https://sites.google.com/view/jellybot'

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
            return u'不合法的{}: {}。請查看使用說明書( {} )。'.format(name_of_thing, thing, error.user_manual_url)
        
        @staticmethod
        def invalid_thing_with_correct_format(name_of_thing, correct_format, thing):
            return u'不合法的{nt}: {t}。{nt}應為{fmt}。詳情請查看使用說明書( {um} )。'.format(nt=name_of_thing, t=thing, fmt=correct_format, um=error.user_manual_url)

        @staticmethod
        def lack_of_thing(name_of_thing):
            return u'缺少{nm}。請修正您所提供的{nm}成正確的格式。詳細說明請參閱使用說明書( {um} )'.format(nm=name_of_thing, um=error.user_manual_url)

        @staticmethod
        def no_result():
            return u'無結果。'

        @staticmethod
        def restricted(permission=None):
            return u'已限制的功能。{}'.format(
                u'\n需求權限: {}+\n\n權限相關說明請參閱使用說明書( {} )'.format(permission, error.user_manual_url) if permission is not None else u'')

        @staticmethod
        def incorrect_channel(available_in_1v1=True, available_in_room=False, available_in_group=False):
            return u'無法於此類型的頻道使用。請至下列頻道:\n{} {} {}\n詳細使用說明請參閱使用說明書( {} )'.format(
                u'[ 私訊 ]' if available_in_1v1 else u'[ - ]',
                u'[ 群組 ]' if available_in_group else u'[ - ]',
                u'[ 房間 ]' if available_in_room else u'[ - ]',
                error.user_manual_url)

        @staticmethod
        def incorrect_param(param_name, correct):
            return u'無法辨認。如果要使用這個功能，{}必須為{}。詳細使用方法請參閱使用說明書( {} )。'.format(param_name, correct, error.user_manual_url)

        @staticmethod
        def unable_to_determine():
            return u'無法判斷指令，請檢閱使用說明書( {} )。'.format(error.user_manual_url)

        @staticmethod
        def pair_not_exist_or_insuffieicnt_permission():
            return u'回覆組不存在，或字組改變權限不足。權限相關說明請參閱使用說明書( {} )。'.format(error.user_manual_url)

        @staticmethod
        def invalid_length(thing, length):
            return u'長度不符。{}的長度應為{}。'.format(thing, length)

        @staticmethod
        def insufficient_space_for_command():
            return u'偵測到1個空格。\n要使用指令的話，指令和參數之間需要2個空格。詳細使用方法請參閱使用說明書( {} )。'.format(
                error.user_manual_url)

        @staticmethod
        def unable_to_receive_user_id():
            return u'因LINE政策問題，如果要使用這個功能的話，請先將LINE更新到v7.5.0以上，或是在私訊頻道中重試。\n\n詳細說明請點此查看: https://developers.line.me/messaging-api/obtaining-user-consent'

        @staticmethod
        def line_account_data_not_found():
            return u'找不到LINE帳號資料。'

        @staticmethod
        def text_length_too_long(url):
            return u'因文字內容長度超過LINE Messaging API的最大字數限制(2000字)，故無法顯示。請點下列網址查看完整內容。\n{}'.format(url)

        @staticmethod
        def miscellaneous(content):
            return u'{}\n\n小水母使用說明: {}'.format(content, error.user_manual_url)