from flask_login import UserMixin

class User(UserMixin):
#    __tablename__ = 'users_table'
#    id =  db.Column(db.Integer, primary_key=True)
#    name =  db.Column(db.String,nullable=False,unique=False)
#    password = db.Column(db.String,primary_key=False, unique=False,nullable=False)

    def __init__(self, name, password):
         self.name = name
         self.password = password

    def get_id(self):
      return self.name