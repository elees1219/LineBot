# -*- coding: utf-8 -*-
import enum

class permission_verifier(object):
    def __init__(self, permission_key_list):
        self._permission_list = [None]
        self._permission_list.extend(permission_key_list)

    def permission_level(self, key):
        try:
            return permission(self._permission_list.index(key))
        except ValueError:
            return permission.user

class permission(enum.IntEnum):
    user = 0
    moderator = 1
    group_admin = 2
    bot_admin = 3

class line_api_proc(object):
    def __init__(self, line_api):
        self._line_api = line_api

    def profile(self, uid):
        try:
            return self._line_api.get_profile(uid)
        except exceptions.LineBotApiError as ex:
            if ex.status_code == 404:
                return None

    @staticmethod
    def source_channel_id(event_source):
        return event_source.sender_id
    
    @staticmethod
    def source_user_id(source_event):
        return event_source.user_id
    
    @staticmethod
    def is_valid_user_id(uid):
        return uid is not None and len(uid) == 33 and uid.startswith('U')
    
    @staticmethod
    def is_valid_room_group_id(uid):
        return uid is not None and len(uid) == 33 and (uid.startswith('C') or uid.startswith('R'))

def string_is_int(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False
    

