import streamlit as st
import math
import google.generativeai as genai

# --- 1. ตั้งค่าหน้าเว็บ Streamlit ---
st.set_page_config(
    page_title="RMUTL Mold & Die: Spring Predictor",
    page_icon="⚙️",
    layout="wide"
)

st.title("⚙️ ระบบวิเคราะห์แม่พิมพ์และทำนายอายุสปริง (Auto SPM & Life Cycle)")
st.caption("RMUTL Mold & Die - Spring Life Cycle & Fatigue Analyzer")

# --- 2. การตั้งค่าระบบ AI ---
API_KEY = "AQ.Ab8RN6K-Ir52L-zkTyLJpt38n_rLf58TKbGxMcW6YgXox80eVA"
api_ready = False

if API_KEY.strip() != "":
    try:
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        api_ready = True
    except Exception:
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

# --- 4. จัด Layout หน้าจอ (แบ่งเป็น 2 คอลัมน์) ---
col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.subheader("📥 กรอกข้อมูลพารามิเตอร์")

    # 1. ข้อมูลแผ่นชิ้นงาน
    with st.expander("1. ข้อมูลแผ่นชิ้นงาน (Part Data)", expanded=True):
        col1, col2 = st.columns(2)
        thick = col1.number_input("Thickness (mm):", value=1.2, step=0.1)
        punch_r = col2.number_input("Punch Radius:", value=3.0, step=0.1)

    # 2. ข้อมูลแม่พิมพ์
    with st.expander("2. ข้อมูลแม่พิมพ์ (Mold Data)", expanded=True):
        col1, col2 = st.columns(2)
        req_bhf = col1.number_input("Req. BHF (kN):", value=18.0, step=0.5)
        plate_wt = col2.number_input("Plate Wt. (kg):", value=50.0, step=1.0)

    # 3. ข้อมูลสปริง
    with st.expander("3. ข้อมูลสปริง (Spring Data)", expanded=True):
        col1, col2 = st.columns(2)
        k = col1.number_input("Spring k (N/mm):", value=60.0, step=1.0)
        l_free = col2.number_input("Free Length (mm):", value=75.0, step=1.0)
        preload = col1.number_input("Preload (mm):", value=5.0, step=0.5)
        stroke = col2.number_input("Stroke (mm):", value=15.0, step=0.5)
        temp = col1.number_input("Op. Temp (°C):", value=45.0, step=1.0)

    btn_calc = st.button("📊 ประมวลผลข้อมูลและคำนวณอายุการใช้งาน", type="primary", use_container_width=True)

with col_right:
    st.subheader("📈 ผลการวิเคราะห์และคำนวณ")

    # ตัวแปรเก็บ Session state สำหรับผลลัพธ์
    if "res_text" not in st.session_state:
        st.session_state.res_text = None

    if btn_calc:
        selected_spring = next((s for s in CORE_SPRINGS if k <= s["max_k"]), CORE_SPRINGS[-1])
        
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

        # บันทึกผลลัพธ์ลง Session State
        st.session_state.res_text = {
            "thick": thick,
            "spring": selected_spring,
            "total_deflection": total_deflection,
            "deflection_ratio": deflection_ratio,
            "force_f1": force_f1,
            "force_f2": force_f2,
            "pocket_depth": pocket_depth,
            "num_springs": num_springs,
            "life_cycle": life_cycle,
            "safe_spm": safe_spm,
            "temp": temp
        }

    # แสดงผลลัพธ์ถ้ามีข้อมูล
    if st.session_state.res_text:
        data = st.session_state.res_text
        st.success(f"**ผลการวิเคราะห์ชิ้นงานหนา {data['thick']} mm**")
        
        col_a, col_b = st.columns(2)
        col_a.metric("สปริง CORE ที่แนะนำ", f"{data['spring']['model']}")
        col_b.metric("สีของสปริง", f"{data['spring']['color']}")
        
        st.markdown(f"""
        * **ระยะยุบตัวรวม:** `{data['total_deflection']:.1f} mm` ({data['deflection_ratio']:.1f}% ของความยาว)
        * **แรง Preload (F1):** `{data['force_f1']:,.1f} N/ตัว`
        * **แรงทำงานสูงสุด (F2):** `{data['force_f2']:,.1f} N/ตัว`
        * **ความลึกเบ้าสปริง:** อย่างน้อย `{data['pocket_depth']:.1f} mm`
        * **จำนวนสปริงที่ต้องใช้:** `{data['num_springs']} ตัว`
        * **⚠️ ทำนายอายุการใช้งาน:** **{data['life_cycle']}**
        * **✅ ความเร็วเครื่องปั๊มที่แนะนำ:** **{data['safe_spm']} SPM**
        """)
        
        if data['temp'] > 80:
            st.warning(f"⚠️ ความร้อน {data['temp']}°C อาจทำให้สปริงนิ่มลงและเสื่อมสภาพเร็วขึ้น")
    else:
        st.info("กดปุ่ม 'ประมวลผลข้อมูลและคำนวณอายุการใช้งาน' ทางด้านซ้ายเพื่อดูผลลัพธ์")

    st.divider()

    # --- 5. ปุ่ม AI วิเคราะห์เชิงลึก ---
    st.subheader("🤖 วิเคราะห์เชิงลึกด้วย AI (Fatigue & Optimization)")
    btn_ai = st.button("🤖 ขอคำแนะนำเชิงลึกจาก AI", use_container_width=True)

    if btn_ai:
        if not api_ready:
            st.error("ไม่สามารถเชื่อมต่อ Gemini AI ได้ โปรดตรวจสอบ API Key")
        else:
            with st.spinner("กำลังประมวลผลการวิเคราะห์ด้วย AI..."):
                try:
                    prompt = "ในฐานะวิศวกรแม่พิมพ์ ช่วยแนะนำการกระจายจุด Center of Force ของสปริงให้ตรงกับ CG แผ่นเพลท เพื่อป้องกันปัญหา Tilting Moment"
                    response = model.generate_content(prompt)
                    st.write(response.text)
                except Exception as e:
                    st.error(f"เกิดข้อผิดพลาดในการเรียกใช้ AI: {e}")
