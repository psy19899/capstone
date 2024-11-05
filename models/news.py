from extensions import db

class Post(db.Model):
    __tablename__ = 'post'
    __table_args__ = {
        'mysql_charset': 'utf8mb4',
        'mysql_collate': 'utf8mb4_unicode_ci' 
    }
    id = db.Column(db.Integer, primary_key = True)
    headline = db.Column(db.Text, nullable=True)
    contents = db.Column(db.Text, nullable=True)
    url = db.Column(db.Text, nullable=False)
    author = db.Column(db.Text, nullable=True)
    written_date = db.Column(db.DateTime, nullable=True)
    team = db.Column(db.String(20), nullable=True)
    category = db.Column(db.String(20), nullable=True)

    block_id = db.Column(db.Integer, db.ForeignKey('block.id'))
    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns if column.name != 'block_id' and column.name != "team" and column.name != "category"}



class Block(db.Model):
    __tablename__ = 'block'
    __table_args__ = {
        'mysql_charset': 'utf8mb4',
        'mysql_collate': 'utf8mb4_unicode_ci' 
    }

    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(20), nullable=False)
    team_name = db.Column(db.String(20), nullable=False)

    posts = db.relationship('Post', backref='block', lazy=True)
    comments = db.relationship('Comment', backref='block', lazy=True)  

class Comment(db.Model):
    __tablename__ = 'comment'
    __table_args__ = {
        'mysql_charset': 'utf8mb4',
        'mysql_collate': 'utf8mb4_unicode_ci' 
    }

    id = db.Column(db.Integer, primary_key=True)

    contents = db.Column(db.String(512), nullable=False)
    userid = db.Column(db.Integer, nullable=False)

    block_id = db.Column(db.Integer, db.ForeignKey('block.id'), nullable=False)