# -*- coding: utf-8 -*-

class text_calculator(object):
    @staticmethod
    def calc(text):
        if text.startswith('0'):
            return
        try:
            result = ''
            if 'result=' not in text:
                exec('result={}'.format(text))
            else:
                exec(text)

            if result != '' and text != str(result) and isinstance(result, (float, int, long)):
                return result
        except:
            return 
