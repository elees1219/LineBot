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
            return u'Invalid {}: {}. Please recheck the user manual.'.format(name_of_thing, thing)

        @staticmethod
        def lack_of_thing(name_of_thing):
            return u'Lack of {nm}(s). Please amend the provided {nm}(s) to the valid form.'.format(nm=name_of_thing)

        @staticmethod
        def no_result():
            return 'No results.'

        @staticmethod
        def restricted(permission=None):
            return 'RESTRICTED.{}'.format(
                '\n\nRequired permission: {}'.format(permission) if permission is not None else '')

        @staticmethod
        def incorrect_channel(available_in_1v1=True, available_in_room=False, available_in_group=False):
            return 'This is not available in this channel. Valid channel to execute below:\n{} {} {}'.format(
                '[ CHAT ]' if available_in_1v1 else '[ - ]',
                '[ GROUP ]' if available_in_group else '[ - ]',
                '[ ROOM ]' if available_in_room else '[ - ]')