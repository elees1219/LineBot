# -*- coding: utf-8 -*-
import enum
from datetime import datetime, timedelta
from collections import defaultdict
from linebot import exceptions
import hashlib
import operator
import traceback
from math import *

class _command(object):
    def __init__(self, min_split=2, max_split=2, non_user_permission_required=False):
        self._split_max = max_split
        self._split_min = min_split
        self._count = 0
        self._non_user_permission_required = non_user_permission_required

    @property
    def split_max(self):
        """Maximum split count."""
        return self._split_max + (1 if self._non_user_permission_required else 0) 

    @property
    def split_min(self):
        """Minimum split count."""
        return self._split_min

    @property
    def count(self):
        """Called count."""
        return self._count

    @count.setter
    def count(self, value):
        """Called count."""
        self._count = value 

    @property
    def non_user_permission_required(self):
        """Required Permission"""
        return self._non_user_permission_required

_sys_cmd_dict = {'S': _command(1, 1, True), 
                'A': _command(2, 4, False), 
                'M': _command(2, 4, True), 
                'D': _command(1, 2, False), 
                'R': _command(1, 2, True), 
                'Q': _command(1, 2, False), 
                'C': _command(0, 0, True), 
                'I': _command(1, 2, False), 
                'K': _command(2, 2, False), 
                'P': _command(0, 1, False), 
                'G': _command(0, 1, False), 
                'GA': _command(1, 5, True), 
                'H': _command(0, 1, False), 
                'SHA': _command(1, 1, False), 
                'O': _command(1, 1, False), 
                'B': _command(0, 0, False), 
                'RD': _command(1, 2, False),
                'STK': _command(0, 0, False),
                'T': _command(1, 1, False)}

_game_cmd_dict = {'RPS': _command(0, 4, False)}

_helper_cmd_dict = {'MFF': _command(1, 8, False),
                    'CALC':  _command(0, 0, False)}

class system_data(object):
    def __init__(self):
        self._boot_up = datetime.now() + timedelta(hours=8)
        self._silence = False
        self._intercept = True
        self._string_calc_debug = False
        self._last_sticker = defaultdict(str)
        self._sys_cmd_dict = _sys_cmd_dict
        self._game_cmd_dict = _game_cmd_dict
        self._helper_cmd_dict = _helper_cmd_dict
        self._webpage_viewed = 0

    def set_last_sticker(self, cid, stk_id):
        self._last_sticker[cid] = str(stk_id)

    def get_last_sticker(self, cid):
        return self._last_sticker.get(cid)

    @property
    def silence(self):
        return self._silence

    @silence.setter
    def silence(self, value):
        self._silence = value
        
    @property
    def intercept(self):
        return self._intercept

    @intercept.setter
    def intercept(self, value):
        self._intercept = value
        
    @property
    def calc_debug(self):
        return self._string_calc_debug

    @calc_debug.setter
    def calc_debug(self, value):
        self._string_calc_debug = value

    @property
    def boot_up(self):
        return self._boot_up

    @property
    def sys_cmd_dict(self):
        return self._sys_cmd_dict

    @property
    def sys_cmd_called(self):
        return sum([x.count for x in self._sys_cmd_dict.itervalues()])

    @property
    def game_cmd_dict(self):
        return self._game_cmd_dict

    @property
    def sys_cmd_called(self):
        return sum([x.count for x in self._game_cmd_dict.itervalues()])

    @property
    def helper_cmd_dict(self):
        return self._helper_cmd_dict

    @property
    def sys_cmd_called(self):
        return sum([x.count for x in self._helper_cmd_dict.itervalues()])

    @property
    def webpage_viewed(self):
        return self._webpage_viewed

    def view_webpage(self):
        self._webpage_viewed += 1

class permission_verifier(object):
    def __init__(self, permission_key_list):
        self._permission_list = [None]
        self._permission_list.extend(permission_key_list)

    def permission_level(self, key):
        try:
            return permission(self._permission_list.index(hashlib.sha224(key).hexdigest()))
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
    def source_user_id(event_source):
        return event_source.user_id
    
    @staticmethod
    def is_valid_user_id(uid):
        return uid is not None and len(uid) == 33 and uid.startswith('U')
    
    @staticmethod
    def is_valid_room_group_id(uid):
        return uid is not None and len(uid) == 33 and (uid.startswith('C') or uid.startswith('R'))

def string_can_be_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

def string_can_be_float(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

    

