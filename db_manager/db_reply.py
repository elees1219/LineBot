class db_reply(db.model):
    """Manager of creating keyword dictionary"""

    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(30), unique=True)
    reply = db.Column(db.String(30))

    def __init__(self, keyword, reply):
        self.keyword = keyword
        self.reply = reply

    def __repr__(self):
        return '<Keyword %r>' % self.keyword % '<Reply %r>' % self.reply
