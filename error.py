# -*- coding: utf-8 -*-

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
            return u'不合法的{}: {}. 請檢閱使用說明書。'.format(name_of_thing, thing)

        @staticmethod
        def lack_of_thing(name_of_thing):
            return u'不完整的{nm}。請修正您所提供的{nm}(s)。'.format(nm=name_of_thing)

        @staticmethod
        def no_result():
            return u'沒有結果。'

        @staticmethod
        def restricted(permission=None):
            return u'限制功能。{}'.format(
                '\n\n需求最低權限: {}'.format(permission) if permission is not None else '')

        @staticmethod
        def incorrect_channel(available_in_1v1=True, available_in_room=False, available_in_group=False):
            return u'無法在此類型的頻道使用。以下列出可使用的頻道:\n{} {} {}'.format(
                '[ 私訊 ]' if available_in_1v1 else '[ - ]',
                '[ 群組 ]' if available_in_group else '[ - ]',
                '[ 房間 ]' if available_in_room else '[ - ]')