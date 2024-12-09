from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
class FoodEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    calories = db.Column(db.Float, nullable=True)
    protein = db.Column(db.Float, nullable=True)
    fat = db.Column(db.Float, nullable=True)
    carbs = db.Column(db.Float, nullable=True)  # 新增碳水化合物欄位
    created_at = db.Column(db.DateTime, default=db.func.now())  # 記錄時間
