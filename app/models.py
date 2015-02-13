from app import db

class JobHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32))
    ck_ref = db.Column(db.String(64))
    timestamp = db.Column(db.DateTime)
    amount = db.Column(db.String(20))
    currency = db.Column(db.String(5)) 
    address = db.Column(db.String())
    
    def __repr__(self):
        return '<Job %r>' % (self.job_ref)


class AddressBook(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32))
    address = db.Column(db.String(40))
    
    def __repr__(self):
        return '<Address %r>' % (self.name)
