# -*- coding: utf-8 -*-

class text_calculator(object):
    @staticmethod
    def calc(text, debug=False):
        result = ''
        if text.startswith('0'):
            return
        try:
            if 'result=' not in text:
                exec('result={}'.format(text))
            else:
                exec(text)

            if result != '' and text != str(result) and isinstance(result, (float, int, long)):
                return result
            elif debug:
                print 'String math calculation failed:'
                print type(result)
                print 'Original Text:'
                print text
                print 'Result variant:'
                print result
        except:
            if debug:
                print 'String math calculation failed:'
                print type(result)
                print 'Original Text:'
                print text
                print 'Result variant:'
                print result
            return 
