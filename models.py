from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Suggestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)  # 用戶選擇的日期
    special_request = db.Column(db.Text, nullable=True)  # 用戶的特殊需求
    generated_text = db.Column(db.Text, nullable=False)  # 生成的建議
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # 建議生成的時間


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
