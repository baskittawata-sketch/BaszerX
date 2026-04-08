from flask import Flask, render_template, request, jsonify
import requests
from datetime import datetime, timedelta
import threading
import time
import uuid

app = Flask(__name__)

# --- CONFIGURATION ---
WEBHOOK_URL = 'https://discord.com/api/webhooks/1491383774423027854/nCvRzf5AC59qRiG7wQsel-Mxh7VX1uCIjuuDbgyKzcIDIgU_lHgNr1-COD3fXYqXlKkJ'

# ฐานข้อมูลในหน่วยความจำ {id: {data}}
boss_registry = {}

def send_to_discord(content):
    try:
        requests.post(WEBHOOK_URL, json={"content": content})
    except:
        pass

def monitor_logic():
    """ตรวจสอบเวลาเกิดและแจ้งเตือนเข้าสู่ Phase 1 อัตโนมัติ"""
    while True:
        now = datetime.now()
        for b_id in list(boss_registry.keys()):
            boss = boss_registry[b_id]
            if boss['status'] == 'COUNTING':
                spawn_dt = datetime.fromisoformat(boss['spawn_time'])
                if now >= spawn_dt:
                    # เปลี่ยนสถานะเป็นเริ่มเกิด (Phase 1)
                    boss['status'] = 'SPAWNING'
                    boss['current_phase'] = 1
                    send_to_discord(f"🔥 **[{boss['name']}] Ch.{boss['ch']} ถึงเวลาเกิดแล้ว!**\n⚠️ สถานะ: **PHASE 1 (เริ่มตีมอนสเตอร์)** @everyone")
        time.sleep(5)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/timers')
def get_timers():
    # ส่งข้อมูลบอสทั้งหมดและเรียงลำดับเวลา
    timers = list(boss_registry.values())
    timers.sort(key=lambda x: x['spawn_time'])
    return jsonify(timers)

@app.route('/set_timer', methods=['POST'])
def set_timer():
    b_id = request.form.get('id') or str(uuid.uuid4())
    name = request.form.get('name')
    ch = request.form.get('ch')
    cd_val = request.form.get('cd')
    
    now = datetime.now()
    # กฎเวลา: มีจุด = ชม. / ไม่มีจุด = นาที
    if '.' in cd_val:
        h, m = map(int, cd_val.split('.'))
        spawn_dt = now + timedelta(hours=h, minutes=m)
    else:
        spawn_dt = now + timedelta(minutes=int(cd_val))
    
    boss_registry[b_id] = {
        "id": b_id,
        "name": name,
        "ch": ch,
        "spawn_time": spawn_dt.isoformat(),
        "status": "COUNTING",
        "current_phase": 0
    }
    return jsonify({"status": "success"})

@app.route('/update_phase', methods=['POST'])
def update_phase():
    b_id = request.form.get('id')
    phase = int(request.form.get('phase'))
    
    if b_id in boss_registry:
        boss = boss_registry[b_id]
        boss['current_phase'] = phase
        boss['status'] = 'SPAWNING' # มั่นใจว่าเป็นสถานะกำลังเกิด
        
        # ส่งแจ้งเตือน Phase ใหม่เข้า Discord
        emoji = ["", "🟢", "🟡", "🟠", "🔴"]
        send_to_discord(f"{emoji[phase]} **อัปเดตสถานะ:** [{boss['name']}] (Ch.{boss['ch']}) เข้าสู่ **PHASE {phase}**")
        return jsonify({"status": "success"})
    return jsonify({"status": "error"})

@app.route('/delete_timer', methods=['POST'])
def delete_timer():
    b_id = request.form.get('id')
    if b_id in boss_registry:
        del boss_registry[b_id]
    return jsonify({"status": "success"})

if __name__ == '__main__':
    threading.Thread(target=monitor_logic, daemon=True).start()
    app.run(debug=True, port=5000)