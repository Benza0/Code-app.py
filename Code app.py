import customtkinter as ctk
import math
import threading
import google.generativeai as genai

# --- 1. ตั้งค่าหน้าต่างโปรแกรม ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("RMUTL Mold & Die: Spring Predictor")
app.geometry("1100x750")

# --- 2. การตั้งค่าระบบ AI ---
API_KEY = "AQ.Ab8RN6K-Ir52L-zkTyLJpt38n_rLf58TKbGxMcW6YgXox80eVA"
if API_KEY.strip() != "":
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    api_ready = True
else:
    model = None
    api_ready = False

# --- 3. ฐานข้อมูลแคตตาล็อกสปริง CORE ---
CORE_SPRINGS = [
    {"color": "สีเขียวอ่อน (Light Green)", "model": "19SSY", "max_k": 5.0},
    {"color": "สีฟ้าอ่อน (Light Blue)", "model": "19SSU", "max_k": 10.0},
    {"color": "สีขาวงาช้าง (Ivory White)", "model": "19SSR", "max_k": 15.0},
    {"color": "สีส้ม (Orange)", "model": "19SSS", "max_k": 20.0},
    {"color": "สีเหลือง (Yellow)", "model": "19SF", "max_k": 30.0},
    {"color": "สีน้ำเงิน (Blue)", "model": "19SL", "max_k": 45.0},
    {"color": "สีแดง (Red)", "model": "19SM", "max_k": 65.0},
    {"color": "สีเขียวเข้ม (Dark Green)", "model": "19SH", "max_k": 90.0},
    {"color": "สีน้ำตาล (Brown)", "model": "19SB", "max_k": 120.0},
    {"color": "สีเทา (Gray)", "model": "19SG", "max_k": 999.0}
]

# --- 4. จัด Layout หน้าจอ ---
lbl_main_title = ctk.CTkLabel(app, text="ระบบวิเคราะห์แม่พิมพ์และทำนายอายุสปริง (Auto SPM & Life Cycle)", font=("Helvetica", 22, "bold"), text_color="white")
lbl_main_title.pack(pady=15)

main_frame = ctk.CTkFrame(app, fg_color="transparent")
main_frame.pack(fill="both", expand=True, padx=20, pady=10)

left_frame = ctk.CTkScrollableFrame(main_frame, width=400)
left_frame.pack(side="left", fill="y", padx=(0, 20))

right_frame = ctk.CTkFrame(main_frame)
right_frame.pack(side="right", fill="both", expand=True)

# ฟังก์ชันสร้างช่องกรอกข้อมูล
def create_input_group(parent, title, color, fields):
    lbl_title = ctk.CTkLabel(parent, text=title, font=("Helvetica", 15, "bold"), text_color=color)
    lbl_title.pack(anchor="w", padx=10, pady=(15, 5))
    frame = ctk.CTkFrame(parent, border_width=1, border_color="gray")
    frame.pack(fill="x", padx=10, pady=5)
    
    entries = {}
    for i, (label, default) in enumerate(fields.items()):
        row = i // 2
        col = i % 2
        inner_frame = ctk.CTkFrame(frame, fg_color="transparent")
        inner_frame.grid(row=row, column=col, padx=10, pady=10, sticky="ew")
        ctk.CTkLabel(inner_frame, text=label, font=("Helvetica", 12)).pack(anchor="w")
        entry = ctk.CTkEntry(inner_frame, width=120)
        entry.insert(0, default)
        entry.pack(anchor="w")
        entries[label] = entry
    return entries

part_entries = create_input_group(left_frame, "1. ข้อมูลแผ่นชิ้นงาน (Part Data)", "#FFD700", {"Thickness (mm):": "1.2", "Punch Radius:": "3.0"})
mold_entries = create_input_group(left_frame, "2. ข้อมูลแม่พิมพ์ (Mold Data)", "#00FFFF", {"Req. BHF (kN):": "18.0", "Plate Wt. (kg):": "50.0"})
spring_entries = create_input_group(left_frame, "3. ข้อมูลสปริง (Spring Data)", "#90EE90", {"Spring k (N/mm):": "60.0", "Free Length:": "75.0", "Preload (mm):": "5.0", "Stroke (mm):": "15.0", "Op. Temp (C):": "45.0"})

btn_calc = ctk.CTkButton(right_frame, text="ประมวลผลข้อมูลและคำนวณอายุการใช้งาน", font=("Helvetica", 15, "bold"), height=40)
btn_calc.pack(pady=(20, 20), padx=20, fill="x")

textbox_result = ctk.CTkTextbox(right_frame, font=("Helvetica", 15), height=280, wrap="word", text_color="#00FF00")
textbox_result.pack(pady=10, padx=20, fill="x")
textbox_result.insert("0.0", "ผลการคำนวณทางฟิสิกส์ ความเร็วรอบ และอายุการใช้งานจะแสดงที่นี่...")
textbox_result.configure(state="disabled")

btn_ai = ctk.CTkButton(right_frame, text="🤖 วิเคราะห์เชิงลึกด้วย AI (Fatigue & Optimization)", fg_color="#800080", hover_color="#5e008a", font=("Helvetica", 15, "bold"), height=40)
btn_ai.pack(pady=(10, 10), padx=20, fill="x")

textbox_ai = ctk.CTkTextbox(right_frame, font=("Helvetica", 14), wrap="word")
textbox_ai.pack(pady=(0, 20), padx=20, fill="both", expand=True)
textbox_ai.insert("0.0", "สถานะ: รอการเชื่อมต่อ AI...")
textbox_ai.configure(state="disabled")

# --- 5. ฟังก์ชันการคำนวณทางฟิสิกส์ ---
def analyze_data():
    try:
        thick = float(part_entries["Thickness (mm):"].get())
        req_bhf = float(mold_entries["Req. BHF (kN):"].get())
        plate_wt = float(mold_entries["Plate Wt. (kg):"].get())
        k = float(spring_entries["Spring k (N/mm):"].get())
        l_free = float(spring_entries["Free Length:"].get())
        preload = float(spring_entries["Preload (mm):"].get())
        stroke = float(spring_entries["Stroke (mm):"].get())
        temp = float(spring_entries["Op. Temp (C):"].get())
        
        selected_spring = next((s for s in CORE_SPRINGS if k <= s["max_k"]), CORE_SPRINGS[-1])
        app.selected_spring_model = selected_spring['model']
        
        total_deflection = preload + stroke
        deflection_ratio = (total_deflection / l_free) * 100 if l_free > 0 else 0
        force_f1 = k * preload
        force_f2 = k * total_deflection
        
        net_force = (req_bhf * 1000) + (plate_wt * 9.81)
        num_springs = math.ceil(net_force / force_f2) if force_f2 > 0 else 0
        pocket_depth = l_free * 0.25
        
        if total_deflection > 0:
            safe_spm = max(20, min(int(2000 / (total_deflection * (deflection_ratio / 10 + 1))), 150))
        else:
            safe_spm = 0

        if deflection_ratio <= 20: life_cycle = "1,000,000+ Shots (ยอดเยี่ยม)"
        elif deflection_ratio <= 25: life_cycle = "500,000 Shots (มาตรฐาน)"
        elif deflection_ratio <= 35: life_cycle = "300,000 Shots (ควรหมั่นตรวจสอบ)"
        else: life_cycle = "ต่ำกว่า 100,000 Shots (ความเสี่ยงสูง)"
        
        res = f"📊 ผลการวิเคราะห์ชิ้นงานหนา {thick} mm\n"
        res += f"• แนะนำสปริง CORE: {selected_spring['color']} (รุ่น {selected_spring['model']})\n\n"
        res += f"⚙️ พารามิเตอร์และการทำนายอายุการใช้งาน\n"
        res += f"• ระยะยุบตัวรวม: {total_deflection:.1f} mm ({deflection_ratio:.1f}% ของความยาว)\n"
        res += f"• แรง Preload (F1): {force_f1:,.1f} N/ตัว\n"
        res += f"• แรงทำงานสูงสุด (F2): {force_f2:,.1f} N/ตัว\n"
        res += f"• ความลึกเบ้าสปริง: อย่างน้อย {pocket_depth:.1f} mm\n"
        res += f"• จำนวนสปริงที่ต้องใช้: {num_springs} ตัว\n"
        res += f"• ⚠️ ทำนายอายุการใช้งาน: {life_cycle}\n"
        res += f"• ✅ ความเร็วเครื่องปั๊มที่แนะนำ: {safe_spm} SPM\n"
        
        if temp > 80: res += f"\n⚠️ ความร้อน {temp}°C อาจทำให้สปริงนิ่มลง"
            
        textbox_result.configure(state="normal")
        textbox_result.delete("0.0", "end")
        textbox_result.insert("0.0", res)
        textbox_result.configure(state="disabled")
    except ValueError:
        pass

btn_calc.configure(command=analyze_data)

# --- 6. ฟังก์ชัน AI ---
def fetch_ai():
    if not api_ready: return
    btn_ai.configure(state="disabled", text="กำลังประมวลผล...")
    try:
        prompt = f"ในฐานะวิศวกรแม่พิมพ์ ช่วยแนะนำการกระจายจุด Center of Force ของสปริงให้ตรงกับ CG แผ่นเพลท เพื่อป้องกันปัญหา Tilting Moment"
        response = model.generate_content(prompt)
        textbox_ai.configure(state="normal")
        textbox_ai.delete("0.0", "end")
        textbox_ai.insert("0.0", response.text)
        textbox_ai.configure(state="disabled")
    except Exception as e:
        pass
    finally:
        btn_ai.configure(state="normal", text="🤖 วิเคราะห์เชิงลึกด้วย AI")

btn_ai.configure(command=lambda: threading.Thread(target=fetch_ai).start())

app.mainloop()
