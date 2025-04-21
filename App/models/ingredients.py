from App.database import db

class Ingredient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Float, default=1)
    unit = db.Column(db.String(50), nullable=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)