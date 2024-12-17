from flask import Flask, render_template, request, flash, redirect, url_for
import requests
from models import db, FoodEntry  # 資料庫模型
from dotenv import load_dotenv
import os
from datetime import datetime

# 加載環境變數
load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///food_analysis.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.getenv("SECRET_KEY", "secret")

db.init_app(app)

@app.route('/history')
def history():
    # 查詢所有食材分析紀錄並按日期分組
    entries = FoodEntry.query.order_by(FoodEntry.created_at.desc()).all()

    # 根據日期分組
    grouped_entries = {}
    for entry in entries:
        date_str = entry.created_at.strftime('%Y-%m-%d')
        if date_str not in grouped_entries:
            grouped_entries[date_str] = []
        grouped_entries[date_str].append(entry)

    return render_template('history.html', grouped_entries=grouped_entries)

@app.route('/history/<date>')
def history_detail(date):
    # 轉換日期格式
    date_obj = datetime.strptime(date, "%Y-%m-%d")
    
    # 查詢這一天的所有紀錄
    entries = FoodEntry.query.filter(db.func.date(FoodEntry.created_at) == date_obj.date()).all()
    
    # 根據時間點分組
    grouped_by_time = {}
    for entry in entries:
        time_str = entry.created_at.strftime('%H:%M:%S')
        if time_str not in grouped_by_time:
            grouped_by_time[time_str] = []
        grouped_by_time[time_str].append(entry)
    
    return render_template('history_detail.html', grouped_by_time=grouped_by_time, date=date)


@app.route('/delete/<int:entry_id>', methods=['POST'])
def delete_entry(entry_id):
    entry = FoodEntry.query.get_or_404(entry_id)
    db.session.delete(entry)
    db.session.commit()
    flash('紀錄已刪除！', 'success')
    return redirect(request.referrer or url_for('history'))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analysis', methods=['GET', 'POST'])
def analysis():
    if request.method == 'POST':
        ingredients = request.form.getlist('food[]')
        quantities = request.form.getlist('quantity[]')
        units = request.form.getlist('unit[]')
        date_time = request.form.get('date_time')  # 接收日期與時間

        full_ingredients = [
            f"{quantities[i]} {units[i]} {ingredients[i]}".strip()
            for i in range(len(ingredients))
        ]

        api_response = analyze_food(full_ingredients)
        if api_response:
            for ingredient, detail in zip(full_ingredients, api_response['ingredients']):
                parsed = detail['parsed'][0]
                nutrients = parsed.get('nutrients', {})
                new_entry = FoodEntry(
                    name=ingredient,
                    calories=nutrients.get('ENERC_KCAL', {}).get('quantity', 0),
                    protein=nutrients.get('PROCNT', {}).get('quantity', 0),
                    fat=nutrients.get('FAT', {}).get('quantity', 0),
                    carbs=nutrients.get('CHOCDF', {}).get('quantity', 0),
                    fiber=nutrients.get('FIBTG', {}).get('quantity', 0),
                    created_at=datetime.strptime(date_time, '%Y-%m-%dT%H:%M')  # 使用傳入的日期時間
                )
                db.session.add(new_entry)
            db.session.commit()
            flash("分析結果已儲存！", "success")

        return render_template('analysis.html', data=api_response)

    return render_template('analysis.html')

@app.route('/suggestion')
def suggestion():
    return render_template('suggestion.html')

def analyze_food(ingredients):
    url = "https://api.edamam.com/api/nutrition-details"
    app_id = os.getenv("APP_ID")
    app_key = os.getenv("API_KEY")

    payload = {
        "title": "User Food List",
        "ingr": ingredients
    }
    headers = {"Content-Type": "application/json"}

    response = requests.post(f"{url}?app_id={app_id}&app_key={app_key}", json=payload, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        flash(f"錯誤: {response.status_code}, {response.text}", "danger")
        return None

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
