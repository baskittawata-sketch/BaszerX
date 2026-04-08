from flask import Flask, render_template, request, jsonify
import requests
from datetime import datetime, timedelta

app = Flask(__name__)

# --- ตั้งค่าตรงนี้ ---
WEBHOOK_URL = 'https://discord.com/api/webhooks/1491383774423027854/nCvRzf5AC59qRiG7wQsel-Mxh7VX1uCIjuuDbgyKzcIDIgU_lHgNr1-COD3fXYqXlKkJ'
# ------------------

# เก็บข้อมูลบอสในหน่วยความจำ (RAM)
boss_registry = {}

def send_to_discord(content):
    if WEBHOOK_URL and WEBHOOK_URL != 'ใส่ลิงก์ WEBHOOK ของคุณที่นี่':
        try:
            requests.post(WEBHOOK_URL, json={"content": content}, timeout=5)
        except:
            print("Discord Webhook Error")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/set_timer', methods=['POST'])
def set_timer():
    boss_name = request.form.get('boss_name')
    channel = request.form.get('channel')
    minutes = float(request.form.get('minutes', 0))
    
    # คำนวณเวลาเกิด (UTC+7)
    spawn_time = datetime.now() + timedelta(minutes=minutes)
    boss_id = f"{boss_name}_{channel}_{int(spawn_time.timestamp())}"
    
    boss_registry[boss_id] = {
        "id": boss_id,
        "name": boss_name,
        "channel": channel,
        "spawn_time": spawn_time.isoformat(),
        "status": "waiting"
    }
    
    send_to_discord(f"📌 **จดบอส:** {boss_name} (Ch.{channel}) จะเกิดในอีก {minutes} นาที")
    return jsonify({"status": "success", "boss_id": boss_id})

@app.route('/get_timers')
def get_timers():
    # ส่งข้อมูลบอสทั้งหมดไปแสดงผลที่หน้าเว็บ
    return jsonify(list(boss_registry.values()))

@app.route('/delete_timer', methods=['POST'])
def delete_timer():
    boss_id = request.form.get('id')
    if boss_id in boss_registry:
        del boss_registry[boss_id]
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "ไม่พบข้อมูลบอส"})

@app.route('/notify_born', methods=['POST'])
def notify_born():
    boss_id = request.form.get('id')
    if boss_id in boss_registry:
        boss = boss_registry[boss_id]
        if boss['status'] == 'waiting':
            boss['status'] = 'born'
            send_to_discord(f"🚨 **BORN!!** {boss['name']} (Ch.{boss['channel']}) เกิดแล้ว!")
    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run(debug=True)
