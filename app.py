from flask import Flask, render_template, request, flash, redirect, url_for
import requests
from models import db, FoodEntry, Suggestion  # 資料庫模型
from dotenv import load_dotenv
import os
from datetime import datetime
import openai

# 加載環境變數
load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///food_analysis.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.getenv("SECRET_KEY", "secret")

db.init_app(app)

openai.api_key = os.getenv("OPENAI_API_KEY")
@app.route('/suggestion', methods=['GET', 'POST'])
def suggestion():
    if request.method == 'POST':
        # 從表單接收日期和特殊需求
        selected_date = request.form.get('date')
        special_request = request.form.get('special_request', '')

        # 確認用戶是否選擇了日期
        if not selected_date:
            flash("請選擇日期！", "danger")
            return redirect(url_for('suggestion'))

        # 查詢資料庫中選定日期的分析內容
        date_obj = datetime.strptime(selected_date, '%Y-%m-%d')
        entries = FoodEntry.query.filter(db.func.date(FoodEntry.created_at) == date_obj.date()).all()

        if not entries:
            flash("該日期沒有任何分析紀錄！", "danger")
            return redirect(url_for('suggestion'))

        # 整理 prompt 的內容
        food_analysis_summary = "\n".join([
            f"{entry.name}: 熱量 {entry.calories} kcal, 蛋白質 {entry.protein} g, 脂肪 {entry.fat} g, 碳水化合物 {entry.carbs} g, 纖維 {entry.fiber} g"
            for entry in entries
        ])
        prompt = (
            f"日期: {selected_date}\n"
            f"飲食內容:\n{food_analysis_summary}\n"
            f"特殊需求: {special_request}\n"
        )
        sample="""
        根據您的飲食狀況，以下是針對您今日飲食的建議：
        1.今日飲食中的需減少食物：餐中多次出現的蘋果，雖然是健康的水果，但過量會增加糖分攝入。可考慮減少到每天1-2個，而不是多次攝入。起司的脂肪含量較高，建議控制食用量，尤其是面對減脂需求的情況下。 
        2.缺少的營養成分： 碳水化合物和纖維相對充足，但蛋白質攝入量偏低，特別是在減脂的情況下，應增加優質蛋白質的攝入。維生素和礦物質方面，水果的攝入較多，但其他來源的蔬菜和全穀物攝入較少，可能導致營養不均衡。 
        3. 建議的飲食內容及餐數：建議一天進食三餐，每餐可包含以下食物：
        早餐：1個水煮蛋, 1片全麥吐司（可加少許鱈魚或雞胸肉）, 1個小蘋果 
        午餐：150克瘦肉（如雞肉、魚類）, 大量蔬菜沙拉，搭配橄欖油或醋, 半杯糙米或全穀物 
        晚餐：1個水煮蛋或100克豆腐, 1片全麥吐司, 番茄或其他低卡蔬菜（如菠菜、青豆等） 
        結合以上建議，您的日常飲食應更加均衡，多攝取蛋白質，並控制攝入量，尤其是高脂肪食物，助於減脂目標的達成。
        """

        # 呼叫 OpenAI API
        try:
            response = openai.chat.completions.create(
                model="gpt-4o-mini",  # 使用 4omini 模型
                messages=[
        {
            "role": "system",
            "content": "以下是某用戶當日的飲食狀況，請根據輸入內容生成當日的飲食建議，同時也要考慮到附加的特殊需求。給出的建議請著重在以下幾點:1.今日的飲食有那些東西應該少吃, 2.缺少了那些營養成分, 3.建議的飲食有那些東西應該少吃, ，生成結果的1,2,3項要換行並且不要出現多餘的字符，例如# *，這邊附上一個生成範例"+sample
        },
        {
            "role": "user",
            "content": prompt,
        },
    ],
                
            )
            suggestion_text = response.choices[0].message.content
            
            # 儲存建議到資料庫
            new_suggestion = Suggestion(
                date=date_obj.date(),
                special_request=special_request,
                generated_text=suggestion_text
            )
            db.session.add(new_suggestion)
            db.session.commit()
            return render_template('suggestion.html', suggestion=suggestion_text)

        except Exception as e:
            flash(f"生成建議時發生錯誤: {str(e)}", "danger")
            return redirect(url_for('suggestion'))

    # GET 方法時僅渲染空白的表單
    return render_template('suggestion.html')

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
