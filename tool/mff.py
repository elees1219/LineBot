# coding: utf-8

import numpy as np

class mff_dmg_calc(object):

  @staticmethod
  def code_dict():
    return {
      'SKP': dmg_bonus(['SKP', 'SK', '技能威力', '威力'], '技能威力'),
      'ABL': dmg_bonus(['ABL', 'AB', '屬強', '屬性', '屬性強化'], '屬性強化'),
      'SKC': dmg_bonus(['SKC', 'SC', '連發', '連擊', '技能連擊'], '技能連擊傷害加成'),
      'ELC': dmg_bonus(['ELC', 'EC', '同屬連發', '同屬連擊'], '同屬技能連擊傷害加成'),
      'CRT': dmg_bonus(['CRT', 'CT', '爆擊', '爆擊加成'], '爆擊傷害加成', 1.5),
      'WKP': dmg_bonus(['WKP', 'WK', '弱點', '弱點加成'], '弱點屬性傷害加成', 2.0, 1.3),
      'BRK': dmg_bonus(['BRK', 'BK', '破防', '破防加成'], '破防傷害加成', 2.0),
      'MGC': dmg_bonus(['MGC', 'MG', '魔力'], '魔力', 1.0)
    }
  
  @staticmethod
  def _dmg_obj():
    return {'first': 0, 'continual': 0, 'list': list(), 'list_of_sum': list()}
  
  @staticmethod
  def _generate_dmg_list(dict):
    dict['list'] = [dict['first']]
    for i in range(4):
      dict['list'].append(dict['continual'])
    
    dict['list_of_sum'] = np.cumsum(dict['list']).tolist()
    return dict
  
  @staticmethod
  def dmg(job):
    """first, continual, list of sum"""
    ret = mff_dmg_calc._dmg_obj()
    
    ret['first'] = job.data['SKP'].value * (1.0 + job.data['ABL'].value) * job.data['WKP'].val(False) * job.data['MGC'].value / 2.0
    
    ret['continual'] = job.data['SKP'].value * (1.0 + job.data['ABL'].value + job.data['SKC'].value + job.data['ELC'].value) * job.data['WKP'].val(False) * job.data['MGC'].value / 2.0
    
    ret = mff_dmg_calc._generate_dmg_list(ret)
    return ret
  
  @staticmethod
  def dmg_crt(job):
    """first, continual, list of sum"""
    ret = mff_dmg_calc._dmg_obj()
    
    ret['first'] = job.data['SKP'].value * (1.0 + job.data['ABL'].value) * job.data['WKP'].val(False) * job.data['CRT'].value * job.data['MGC'].value / 2.0
    
    ret['continual'] = job.data['SKP'].value * (1.0 + job.data['ABL'].value + job.data['SKC'].value + job.data['ELC'].value) * job.data['CRT'].value * job.data['WKP'].val(False) * job.data['MGC'].value / 2.0
    
    ret = mff_dmg_calc._generate_dmg_list(ret)
    return ret
  
  @staticmethod
  def dmg_break(job):
    """first, continual, list of sum"""
    ret = mff_dmg_calc._dmg_obj()
    
    ret['first'] = job.data['SKP'].value * (1.0 + job.data['ABL'].value) * job.data['WKP'].value * job.data['BRK'].value * job.data['MGC'].value 
    
    ret['continual'] = job.data['SKP'].value * (1.0 + job.data['ABL'].value + job.data['SKC'].value + job.data['ELC'].value) * job.data['BRK'].value * job.data['WKP'].value * job.data['MGC'].value 
    
    ret = mff_dmg_calc._generate_dmg_list(ret)
    return ret
  
  @staticmethod
  def dmg_break_crt(job):
    """first, continual, list of sum"""
    ret = mff_dmg_calc._dmg_obj()
    
    ret['first'] = job.data['SKP'].value * (1.0 + job.data['ABL'].value) * job.data['WKP'].value * job.data['BRK'].value * job.data['CRT'].value * job.data['MGC'].value
    
    ret['continual'] = job.data['SKP'].value * (1.0 + job.data['ABL'].value + job.data['SKC'].value + job.data['ELC'].value) * job.data['BRK'].value * job.data['CRT'].value * job.data['WKP'].value * job.data['MGC'].value
    
    ret = mff_dmg_calc._generate_dmg_list(ret)
    return ret
    
  @staticmethod
  def help_code():
    txt = '代號說明:\n'
    txt += '\n'.join('{} (可用代號: {})'.format(value.description, 
                                               ', '.join(value.key)) for key, value in mff_dmg_calc.code_dict().items())
    return txt

  @staticmethod
  def help_sample():
      txt = '技能威力 {技能威力}\n屬性強化 {屬性強化}%\n技能連擊 {技能連擊}%\n同屬連擊 {同屬連擊}%\n爆擊加成 {爆擊加成}%\n弱點加成 {弱點加成}%\n破防 {破防加成}%\n魔力 {魔力}%'
      return txt
    
  @staticmethod
  def text_job_parser(input):
    dataobj = [x.split(' ') for x in input.split('\n')]
    
    ret_job = job()
    for key, value in ret_job.data.items():
      if not value.value_set:
        for pair in dataobj:
          if pair[0] in value.key:
            if '%' in pair[1]:
              pair[1] = pair[1].replace('%', '')
              value.value = float(pair[1]) / 100.0
            else:
              value.value = pair[1]
              
    return ret_job
    
class job(object):
  def __init__(self, **kwargs):
    self._data = mff.code_dict()
    for key, value in kwargs.items():
      self._data[key].value = value
      
  @property
  def data(self):
    return self._data
    
class dmg_bonus(object):
  """NOTICE: enter value without percentage."""
  def __init__(self, key, description, base=0.0, nonbreak_base=-1.0):
    self._key = [key] if not isinstance(key, list) else key
    self._description = description
    self._base = float(base)
    self._nbase = base if nonbreak_base == -1.0 else float(nonbreak_base)
    self._value = 0.0
    self._value_set = False
    
  def val(self, is_break=True):
    if is_break:
      return self._base + self._value
    else:
      return self._nbase + self._value
    
  @property
  def description(self):
    return self._description
    
  @property
  def key(self):
    return self._key
    
  @property
  def value(self):
    return self._base + self._value
    
  @property
  def value_set(self):
    return self._value_set
    
  @value.setter
  def value(self, value):
    self._value_set = True
    self._value = float(value)
    
  def __repr__(self):
    return 'Description: {}, Key: {}, Data Set: {}, Value: (B){} / (NB){}'.format(self._description, 
                                                                                  self._key, 
                                                                                  self._value_set, 
                                                                                  self.val(), 
                                                                                  self.val(False))