from flask import Flask, jsonify, render_template, request, redirect, url_for, flash
import requests
from models import db, FoodEntry  # 資料庫模型

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///food_analysis.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#app.secret_key = 'your_secret_key'

db.init_app(app)

@app.route('/history')
def history():
    entries = FoodEntry.query.order_by(FoodEntry.created_at.desc()).all()
    return render_template('history.html', entries=entries)


# 首頁
@app.route('/')
def index():
    return render_template('index.html')

# 飲食分析
@app.route('/analysis', methods=['GET', 'POST'])
def analysis():
    if request.method == 'POST':
        # 接收用戶輸入
        ingredients = request.form.getlist('food[]')
        quantities = request.form.getlist('quantity[]')
        units = request.form.getlist('unit[]')
        
        # 組合輸入資料
        full_ingredients = [
            f"{quantities[i]} {units[i]} {ingredients[i]}".strip()
            for i in range(len(ingredients))
        ]
        
        # 呼叫 Edamam API
        api_response = analyze_food(full_ingredients)
        if api_response:
            # 解析回傳數據並存入資料庫
            for ingredient, detail in zip(full_ingredients, api_response['ingredients']):
                # 提取營養資訊
                parsed = detail['parsed'][0]
                nutrients = parsed.get('nutrients', {})
                
                # 建立資料庫記錄
                new_entry = FoodEntry(
                    name=ingredient,
                    calories=nutrients.get('ENERC_KCAL', {}).get('quantity', 0),
                    protein=nutrients.get('PROCNT', {}).get('quantity', 0),
                    fat=nutrients.get('FAT', {}).get('quantity', 0),
                    carbs=nutrients.get('CHOCDF', {}).get('quantity', 0)
                )
                db.session.add(new_entry)
            db.session.commit()

        return render_template('analysis.html', data=api_response)

    return render_template('analysis.html')


# 飲食建議
@app.route('/suggestion')
def suggestion():
    return render_template('suggestion.html')

def analyze_food(ingredients):
    url = "https://api.edamam.com/api/nutrition-details"
    app_id = "9faf6199"
    app_key = "ae2ce57278d0b9054f230a2ec77f464f	"

    payload = {
        "title": "User Food List",
        "ingr": ingredients
    }
    headers = {"Content-Type": "application/json"}

    response = requests.post(f"{url}?app_id={app_id}&app_key={app_key}", json=payload, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        flash(f"Error: {response.status_code}, {response.text}")
        return None
    
@app.route('/delete_entry/<int:entry_id>', methods=['POST'])
def delete_entry(entry_id):
    try:
        # 尋找要刪除的紀錄
        entry = FoodEntry.query.get(entry_id)
        
        if entry:
            # 刪除紀錄
            db.session.delete(entry)
            db.session.commit()
            return jsonify({'status': 'success', 'message': '删除成功'}), 200
        else:
            return jsonify({'status': 'error', 'message': '记录不存在'}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # 自動創建資料表
    app.run(debug=True)

