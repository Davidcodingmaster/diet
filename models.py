from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class FoodEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    calories = db.Column(db.Float, nullable=True)
    protein = db.Column(db.Float, nullable=True)
    fat = db.Column(db.Float, nullable=True)
    carbs = db.Column(db.Float, nullable=True)
    fiber = db.Column(db.Float, nullable=True)  # 膳食纖維欄位
    tags = db.Column(db.String(255), nullable=True)  # 標籤欄位
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # 紀錄時間

    def __repr__(self):
        return f'<FoodEntry {self.name}>'
