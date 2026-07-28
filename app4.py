from flask import Flask, render_template_string, request, redirect, session, jsonify
import subprocess
import random
import string
import requests
import time
import os

# 1. ประกาศตัวแปร app เป็นอันดับแรกสุด (ห้ามย้าย)
app = Flask(__name__)
app.secret_key = 'zp_cloud_secure_production_2026'

RECEIVER_PHONE = "0624792643"

def get_package_duration(pkg_value):
    if pkg_value == 'trial':
        return 1200    # 20 นาที
    elif pkg_value == '32':
        return 86400   # 1 วัน
    elif pkg_value == '70':
        return 604800  # 7 วัน
    elif pkg_value == '299':
        return 2592000 # 30 วัน
    return 86400

# 1. หน้าเลือกแพ็กเกจ + Modal ฟอร์มทดลองใช้ (UI ใหม่: ดาวตก + พื้นหลังอนิเมะสวยๆ)
packages_template = '''
<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <title>เลือกแพ็กเกจ VPS - ZP Cloud</title>
    <style>
        body { 
            background: url('https://4kwallpapers.com/images/wallpapers/castorice-butterfly-25920.jpg') no-repeat center center fixed; 
            background-size: cover; 
            color: #f8fafc; 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            display: flex; 
            justify-content: center; 
            align-items: center; 
            min-height: 100vh; 
            margin: 0; 
            box-sizing: border-box; 
            padding: 20px; 
            overflow: hidden;
            position: relative;
        }
        
        /* เอฟเฟกต์ดาวตก */
        .night { position: absolute; width: 100%; height: 100%; top: 0; left: 0; z-index: 1; pointer-events: none; }
        .shooting-star { position: absolute; height: 2px; background: linear-gradient(-45deg, #5df, rgba(0, 0, 255, 0)); border-radius: 999px; filter: drop-shadow(0 0 6px #38bdf8); animation: tail 3s ease-in-out infinite, falling 3s ease-in-out infinite; }
        .shooting-star::before, .shooting-star::after { content: ''; position: absolute; top: calc(50% - 1px); right: 0; height: 2px; background: linear-gradient(-45deg, rgba(0, 0, 255, 0), #38bdf8, rgba(0, 0, 255, 0)); transform: translateX(50%) rotateZ(45deg); border-radius: 100%; animation: shining 3s ease-in-out infinite; }
        .shooting-star::after { transform: translateX(50%) rotateZ(-45deg); }
        
        @keyframes tail { 0% { width: 0; } 30% { width: 100px; } 100% { width: 0; } }
        @keyframes falling { 0% { transform: translateX(0) translateY(0); } 100% { transform: translateX(300px) translateY(300px); } }
        @keyframes shining { 0% { width: 0; } 50% { width: 30px; } 100% { width: 0; } }

        .card { 
            background: rgba(18, 24, 38, 0.85); 
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            padding: 35px; 
            border-radius: 20px; 
            width: 440px; 
            border: 1px solid rgba(56, 189, 248, 0.3); 
            box-shadow: 0 20px 50px rgba(0,0,0,0.9), 0 0 20px rgba(56, 189, 248, 0.2); 
            box-sizing: border-box; 
            z-index: 2;
        }
        h2 { color: #38bdf8; text-align: center; margin-top: 0; font-size: 24px; text-shadow: 0 0 10px rgba(56,189,248,0.5); }
        
        .pkg-box { 
            background: rgba(11, 15, 25, 0.6); 
            padding: 14px 18px; 
            border-radius: 12px; 
            margin: 12px 0; 
            border: 1px solid rgba(255,255,255,0.08); 
            font-size: 15px; 
            cursor: pointer; 
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .pkg-box:hover {
            border-color: #38bdf8;
            box-shadow: 0 0 12px rgba(56, 189, 248, 0.4);
            transform: translateY(-2px);
        }
        .pkg-trial { border: 1px dashed #38bdf8; background: rgba(15, 23, 42, 0.7); }
        
        button { 
            width: 100%; 
            padding: 14px; 
            background: linear-gradient(135deg, #22c55e, #16a34a); 
            border: none; 
            color: #ffffff; 
            font-weight: bold; 
            border-radius: 10px; 
            cursor: pointer; 
            margin-top: 20px; 
            font-size: 16px; 
            box-shadow: 0 4px 15px rgba(34, 197, 94, 0.4);
            transition: all 0.3s ease;
        }
        button:hover { 
            filter: brightness(1.1); 
            box-shadow: 0 6px 20px rgba(34, 197, 94, 0.6);
            transform: translateY(-1px);
        }
        
        .modal { display: {{ 'flex' if show_trial_modal else 'none' }}; position: fixed; z-index: 10; left: 0; top: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.85); backdrop-filter: blur(8px); justify-content: center; align-items: center; }
        .modal-content { background: rgba(18, 24, 38, 0.95); padding: 30px; border-radius: 16px; width: 400px; border: 1px solid rgba(56,189,248,0.4); box-shadow: 0 15px 40px rgba(0,0,0,0.9); box-sizing: border-box; z-index: 11; }
        .modal-content h3 { color: #38bdf8; margin-top: 0; font-size: 20px; text-align: center; }
        .modal-content label { font-size: 13px; color: #94a3b8; display: block; margin-top: 12px; }
        .modal-content input, .modal-content textarea { width: 100%; padding: 12px; margin-top: 6px; background: rgba(11, 15, 25, 0.8); border: 1px solid rgba(255,255,255,0.1); color: white; border-radius: 8px; box-sizing: border-box; font-size: 14px; outline: none; transition: 0.3s; }
        .modal-content input:focus, .modal-content textarea:focus { border-color: #38bdf8; box-shadow: 0 0 8px rgba(56,189,248,0.3); }
        .modal-content textarea { resize: vertical; height: 90px; }
        .btn-group { display: flex; gap: 12px; margin-top: 20px; }
        .btn-close { flex: 1; padding: 12px; background: rgba(51, 65, 85, 0.8); border: none; color: white; border-radius: 8px; cursor: pointer; text-decoration: none; text-align: center; font-size: 14px; transition: 0.3s; }
        .btn-close:hover { background: #475569; }
        .btn-confirm { flex: 1; padding: 12px; background: linear-gradient(135deg, #38bdf8, #0284c7); border: none; color: #050505; font-weight: bold; border-radius: 8px; cursor: pointer; font-size: 14px; box-shadow: 0 4px 15px rgba(56,189,248,0.4); transition: 0.3s; }
        .btn-confirm:hover { filter: brightness(1.1); }
        .error-text { color: #ef4444; font-size: 13px; text-align: center; margin-top: 12px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="night">
        <div class="shooting-star" style="top: 10%; left: 20%; animation-delay: 0s;"></div>
        <div class="shooting-star" style="top: 40%; left: 70%; animation-delay: 1.2s;"></div>
        <div class="shooting-star" style="top: 70%; left: 40%; animation-delay: 2.5s;"></div>
    </div>

    <div class="card">
        <h2>💎 เลือกแพ็กเกจของคุณ</h2>
        <form method="POST" action="/select-package">
            <label class="pkg-box pkg-trial"><input type="radio" name="package" value="trial"> <b>🚀 ทดลองใช้งานฟรี 20 นาที</b></label>
            <label class="pkg-box"><input type="radio" name="package" value="32" checked> <b>32 บาท / วัน</b></label>
            <label class="pkg-box"><input type="radio" name="package" value="70"> <b>70 บาท / สัปดาห์</b></label>
            <label class="pkg-box"><input type="radio" name="package" value="299"> <b>299 บาท / เดือน</b></label>
            <button type="submit">ดำเนินการต่อ</button>
        </form>
    </div>

    <div class="modal">
        <div class="modal-content">
            <h3>📝 ฟอร์มขอทดลองใช้งานระบบ</h3>
            <form method="POST" action="/submit-trial">
                <label>เบอร์โทรศัพท์:</label>
                <input type="text" name="trial_phone" placeholder="062XXXXXXX" required>
                <label>อีเมล:</label>
                <input type="email" name="trial_email" placeholder="example@email.com" required>
                <label>สาเหตุที่ต้องการทดลองใช้:</label>
                <textarea name="trial_reason" placeholder="ระบุเหตุผล..." required></textarea>
                
                {% if trial_error %}
                    <div class="error-text">❌ {{ trial_error }}</div>
                {% endif %}

                <div class="btn-group">
                    <a href="/" class="btn-close">ยกเลิก</a>
                    <button type="submit" class="btn-confirm">ยืนยันขอทดลอง</button>
                </div>
            </form>
        </div>
    </div>
</body>
</html>
'''

# 2. หน้าชำระเงิน (ระบบเดิมคงเดิม แต่ปรับ UI ให้ธีมเดียวกันพร้อมดาวตก)
payment_template = '''
<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <title>ชำระเงินผ่านซองอั่งเปา - ZP Cloud</title>
    <style>
        body { 
            background: url('https://4kwallpapers.com/images/wallpapers/castorice-butterfly-25920.jpg') no-repeat center center fixed; 
            background-size: cover; 
            color: #f8fafc; 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            display: flex; 
            justify-content: center; 
            align-items: center; 
            height: 100vh; 
            margin: 0; 
            overflow: hidden;
            position: relative;
        }

        .night { position: absolute; width: 100%; height: 100%; top: 0; left: 0; z-index: 1; pointer-events: none; }
        .shooting-star { position: absolute; height: 2px; background: linear-gradient(-45deg, #5df, rgba(0, 0, 255, 0)); border-radius: 999px; filter: drop-shadow(0 0 6px #38bdf8); animation: tail 3s ease-in-out infinite, falling 3s ease-in-out infinite; }
        .shooting-star::before, .shooting-star::after { content: ''; position: absolute; top: calc(50% - 1px); right: 0; height: 2px; background: linear-gradient(-45deg, rgba(0, 0, 255, 0), #38bdf8, rgba(0, 0, 255, 0)); transform: translateX(50%) rotateZ(45deg); border-radius: 100%; animation: shining 3s ease-in-out infinite; }
        .shooting-star::after { transform: translateX(50%) rotateZ(-45deg); }
        
        @keyframes tail { 0% { width: 0; } 30% { width: 100px; } 100% { width: 0; } }
        @keyframes falling { 0% { transform: translateX(0) translateY(0); } 100% { transform: translateX(300px) translateY(300px); } }
        @keyframes shining { 0% { width: 0; } 50% { width: 30px; } 100% { width: 0; } }

        .card { 
            background: rgba(18, 24, 38, 0.85); 
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            padding: 30px; 
            border-radius: 20px; 
            width: 440px; 
            border: 1px solid rgba(56, 189, 248, 0.3); 
            box-shadow: 0 20px 50px rgba(0,0,0,0.9), 0 0 20px rgba(56, 189, 248, 0.2); 
            box-sizing: border-box; 
            z-index: 2;
        }
        h2 { color: #38bdf8; text-align: center; margin-top: 0; font-size: 22px; text-shadow: 0 0 10px rgba(56,189,248,0.5); }
        p { font-size: 14px; color: #cbd5e1; line-height: 1.6; margin: 8px 0 20px 0; text-align: center; }
        
        input[type="text"] { 
            width: 100%; 
            padding: 14px; 
            margin: 10px 0; 
            background: rgba(11, 15, 25, 0.8); 
            border: 1px solid rgba(255,255,255,0.1); 
            color: white; 
            border-radius: 10px; 
            box-sizing: border-box; 
            font-size: 14px; 
            outline: none; 
            transition: 0.3s; 
        }
        input[type="text"]:focus { 
            border-color: #38bdf8; 
            box-shadow: 0 0 10px rgba(56, 189, 248, 0.4); 
        }

        .btn-group { display: flex; gap: 12px; margin-top: 20px; }
        .btn-cancel { flex: 1; padding: 12px; background: rgba(239, 68, 68, 0.8); border: none; color: white; font-weight: bold; border-radius: 10px; cursor: pointer; text-decoration: none; text-align: center; box-sizing: border-box; font-size: 14px; transition: 0.3s; box-shadow: 0 4px 15px rgba(239, 68, 68, 0.3); }
        .btn-cancel:hover { background: #dc2626; }
        
        .btn-submit { flex: 1; padding: 12px; background: linear-gradient(135deg, #22c55e, #16a34a); border: none; color: white; font-weight: bold; border-radius: 10px; cursor: pointer; font-size: 14px; box-shadow: 0 4px 15px rgba(34, 197, 94, 0.4); transition: 0.3s; }
        .btn-submit:hover { filter: brightness(1.1); box-shadow: 0 6px 20px rgba(34, 197, 94, 0.6); }
        
        .status-box { text-align: center; margin-top: 20px; font-weight: bold; font-size: 14px; }
    </style>
</head>
<body>
    <div class="night">
        <div class="shooting-star" style="top: 15%; left: 10%; animation-delay: 0.5s;"></div>
        <div class="shooting-star" style="top: 50%; left: 60%; animation-delay: 2s;"></div>
    </div>

    <div class="card">
        <h2>🧧 เติมเงินผ่านซองอั่งเปา TrueMoney</h2>
        <p>สร้างซองอั่งเปาไปยังเบอร์ <b style="color: #38bdf8;">{{ receiver_phone }}</b> แล้วนำลิงก์มาวางด้านล่าง:</p>
        
        <form method="POST" action="/payment">
            <input type="text" name="angpao_code" placeholder="วางลิงก์ซองอั่งเปาที่นี่..." required>
            
            {% if checked %}
                <div class="status-box" style="color: #38bdf8;" id="loading-text">🔄 กำลังตรวจสอบซองอั่งเปา (กรุณารอสักครู่)...</div>
                <script>
                    // หน่วงเวลา 12 วินาที (12000 มิลลิวินาที) ก่อนเด้งไปหน้า app3.py (พอร์ต 8081)
                    setTimeout(() => {
                        document.getElementById('loading-text').style.color = '#22c55e';
                        document.getElementById('loading-text').innerHTML = '✅ ตรวจสอบสำเร็จ! กำลังเข้าสู่ระบบ VPS...';
                        setTimeout(() => {
                            window.location.href = "http://localhost:8081";
                        }, 1000);
                    }, 12000);
                </script>
            {% elif error_message %}
                <div class="status-box" style="color: #ef4444;">❌ {{ error_message }}</div>
            {% endif %}

            <div class="btn-group" {% if checked %}style="display:none;"{% endif %}>
                <a href="/" class="btn-cancel">ยกเลิก</a>
                <button type="submit" class="btn-submit">ตรวจสอบซอง</button>
            </div>
        </form>
    </div>
</body>
</html>
'''

# 3. หน้า Dashboard (ตกแต่งธีมกระจกเรืองแสงสวยงาม)
dashboard_template = '''
<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <title>ZP Cloud - Dashboard</title>
    <style>
        body { 
            background: url('https://4kwallpapers.com/images/wallpapers/castorice-butterfly-25920.jpg') no-repeat center center fixed; 
            background-size: cover; 
            color: #f8fafc; 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            display: flex; 
            justify-content: center; 
            align-items: center; 
            height: 100vh; 
            margin: 0; 
        }
        .card { 
            background: rgba(18, 24, 38, 0.85); 
            backdrop-filter: blur(16px);
            padding: 35px; 
            border-radius: 20px; 
            width: 420px; 
            border: 1px solid rgba(56, 189, 248, 0.3); 
            box-shadow: 0 20px 50px rgba(0,0,0,0.9), 0 0 20px rgba(56, 189, 248, 0.2); 
            text-align: center; 
        }
        h2 { color: #38bdf8; margin-top: 0; font-size: 24px; text-shadow: 0 0 10px rgba(56,189,248,0.5); }
        p { color: #cbd5e1; font-size: 14px; margin-bottom: 25px; }
        .btn { display: block; width: 100%; padding: 14px; background: linear-gradient(135deg, #38bdf8, #0284c7); border: none; color: #050505; font-weight: bold; border-radius: 10px; text-decoration: none; margin-top: 15px; box-sizing: border-box; box-shadow: 0 4px 15px rgba(56,189,248,0.4); transition: 0.3s; }
        .btn:hover { filter: brightness(1.1); }
        .btn-back { background: rgba(51, 65, 85, 0.8); color: white; box-shadow: none; }
        .btn-back:hover { background: #475569; }
    </style>
</head>
<body>
    <div class="card">
        <h2>🎉 ยินดีต้อนรับสู่ ZP Cloud</h2>
        <p>สถานะระบบ: เปิดใช้งานเรียบร้อยแล้ว</p>
        <a href="http://localhost:8081" target="_blank" class="btn">🖥️ เปิดหน้า VPS GUI (app3.py)</a>
        <a href="/" class="btn btn-back">🔄 กลับหน้าแรก</a>
    </div>
</body>
</html>
'''

# --- Flask Routes (ระบบหลังบ้านและ API จริง ทำงานเหมือนเดิม 100%) ---
@app.route('/')
def index():
    return render_template_string(packages_template, show_trial_modal=False)

@app.route('/select-package', methods=['POST'])
def select_package():
    pkg = request.form.get('package')
    session['selected_package'] = pkg
    if pkg == 'trial':
        return render_template_string(packages_template, show_trial_modal=True)
    return redirect('/payment')

@app.route('/submit-trial', methods=['POST'])
def submit_trial():
    phone = request.form.get('trial_phone')
    email = request.form.get('trial_email')
    reason = request.form.get('trial_reason')
    
    if not phone or not email or not reason:
        return render_template_string(packages_template, show_trial_modal=True, trial_error="กรุณากรอกข้อมูลให้ครบถ้วน")
    
    session['has_paid'] = True
    session['expire_time'] = time.time() + get_package_duration('trial')
    session['selected_package'] = 'trial'
    
    return redirect('/dashboard')

@app.route('/payment', methods=['GET', 'POST'])
def payment():
    checked = False
    error_message = None
    if request.method == 'POST':
        angpao_link = request.form.get('angpao_code', '').strip()
        
        voucher_code = angpao_link
        if "v=" in angpao_link:
            voucher_code = angpao_link.split("v=")[1].split("&")[0]
        elif "voucher.truemoney.com" in angpao_link:
            voucher_code = angpao_link.rstrip("/").split("/")[-1]

        try:
            api_url = f"https://gift.truemoney.com/campaign/vouchers/{voucher_code}/redeem"
            payload = {
                "mobile": RECEIVER_PHONE,
                "voucher_hash": voucher_code
            }
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json",
                "Accept-Language": "th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7"
            }
            
            response = requests.post(api_url, json=payload, headers=headers, timeout=10)
            data = response.json()
            
            if data.get("status", {}).get("code") == "SUCCESS":
                session['has_paid'] = True
                session['expire_time'] = time.time() + get_package_duration(session.get('selected_package', '32'))
                checked = True
            else:
                error_message = data.get("status", {}).get("message", "ซองอั่งเปานี้ไม่ถูกต้อง หรือถูกใช้งานไปแล้ว")
        except requests.exceptions.RequestException:
            error_message = "ไม่สามารถเชื่อมต่อกับเซิร์ฟเวอร์ TrueMoney ได้ในขณะนี้ (โปรดตรวจสอบการเชื่อมต่ออินเทอร์เน็ต)"
        except Exception:
            error_message = "เกิดข้อผิดพลาดในการประมวลผลซองอั่งเปา"

    return render_template_string(payment_template, receiver_phone=RECEIVER_PHONE, checked=checked, error_message=error_message)

@app.route('/dashboard')
def dashboard():
    if not session.get('has_paid'):
        return redirect('/payment')
    return render_template_string(dashboard_template)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
