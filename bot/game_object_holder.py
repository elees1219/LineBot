# -*- coding: utf-8 -*-

import game
from collections import defaultdict

class game_objects(object):
    def __init__(self):
        self._rps = defaultdict(game.rps)

    @property
    def rps_instance_count(self):
        return len(self._rps)

    def set_rps(self, cid, rps):
        self._rps[cid] = rps

    def del_rps(self, cid):
        del self._rps[cid]

    def get_rps(self, cid):
        return self._rps.get(cid)
