import streamlit as st
import pandas as pd
import altair as alt
import pyrebase
from datetime import datetime, time, date
import os 

# Impor Firebase Admin SDK
import firebase_admin
from firebase_admin import credentials, db

# --- KONFIGURASI DAN INISIALISASI ---

# Konfigurasi Firebase (Client Side)
firebase_config = {
    "apiKey": "AIzaSyAvARA5y4fWcyhsEE1jMdc6BpPIF-qcffg",
    "authDomain": "tubescd.firebaseapp.com",
    "databaseURL": "https://tubescd-default-rtdb.asia-southeast1.firebasedatabase.app",
    "projectId": "tubescd",
    "storageBucket": "tubescd.appspot.com",
    "messagingSenderId": "",
    "appId": ""
}

# Inisialisasi Firebase (Realtime DB & Auth)
try:
    if 'firebase_admin' in st.secrets:
        # Gunakan st.secrets untuk otorisasi Admin SDK
        cred = credentials.Certificate(dict(st.secrets["firebase_admin"]))
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred, {
                'databaseURL': 'https://tubescd-default-rtdb.asia-southeast1.firebasedatabase.app/'
            })
    else:
        if not firebase_admin._apps:
            st.warning("⚠️ Kunci Firebase Admin SDK tidak ditemukan di st.secrets. Fitur database Admin SDK mungkin terganggu.")
            pass
except Exception as e:
    st.error(f"❌ Gagal menginisialisasi Firebase Admin SDK dari secrets. Error: {e}")
    st.stop()


# --- FUNGSI TAMPILAN (UI) ---

def load_css():
    """Memuat CSS kustom untuk tampilan yang lebih menarik dan mendukung tema."""
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');
            
            html, body, [class*="st-"], .st-emotion-cache-10trblm {
                font-family: 'Poppins', sans-serif;
            }
            
            .stApp { background-color: var(--background-color); }
            .block-container { padding-top: 2rem; padding-bottom: 2rem; }

            /* Tombol umum */
            .stButton>button {
                border-radius: 12px; font-weight: 600; padding: 0.75rem 1.5rem;
                transition: all 0.3s ease-in-out; border: 2px solid var(--primary-color);
                background-color: var(--primary-color); color: white;
            }
            .stButton>button:hover {
                transform: translateY(-3px);
                box-shadow: 0 7px 14px rgba(46, 139, 87, 0.3);
                filter: brightness(1.1);
            }
            
            /* Kartu Metrik Kustom v2 */
            .metric-card-v2 {
                background-color: var(--secondary-background-color); border: 1px solid var(--secondary-background-color);
                padding: 1.5rem; border-radius: 1rem; text-align: center; transition: all 0.3s ease;
            }
            .metric-card-v2:hover { transform: scale(1.03); box-shadow: 0 8px 16px rgba(27, 46, 94, 0.1); }
            .metric-card-v2 .icon.moisture { color: #0072ff; }
            .metric-card-v2 .icon.light { color: #FFD700; }
            .metric-card-v2 .icon.water { color: #3b82f6; } 
            .metric-card-v2 .icon.tank { color: #800080; } 

            .metric-card-v2 .icon { font-size: 2.5rem; line-height: 1; color: var(--primary-color);}
            .metric-card-v2 .label { font-size: 0.9rem; color: var(--text-color); opacity: 0.7; margin-top: 0.5rem; }
            .metric-card-v2 .value { font-size: 1.75rem; font-weight: 700; color: var(--text-color); }

            /* Status Box */
            .status-box {
                display: flex; justify-content: center; align-items: center; gap: 0.75rem;
                padding: 1.5rem; border-radius: 1rem; color: white; font-weight: 600;
                box-shadow: 0 4px 10px rgba(0,0,0,0.1);
            }
            .status-box.lamp-on { background-color: #10B981; }
            .status-box.lamp-off { background-color: #EF4444; }
            .status-box.solenoid-on { background-color: #3B82F6; } 
            .status-box.solenoid-off { background-color: #EF4444; } 

            /* Card Hijau/Merah untuk status siram harian */
            .daily-status-card {
                padding: 1rem; border-radius: 0.75rem; text-align: center; font-weight: 600; margin-bottom: 0.5rem;
                box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            }
            .daily-status-card.done { background-color: #D1FAE5; color: #065F46; border: 1px solid #10B981; }
            .daily-status-card.pending { background-color: #FEE2E2; color: #991B1B; border: 1px solid #EF4444; }

            /* Menangani Tampilan Login/Register */
            @keyframes gradientBG {
                0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; }
            }
            @keyframes slideUpFadeIn { to { opacity: 1; transform: translateY(0); } }
            
            .login-title {
                text-align: center; color: white; font-size: 2.5rem; font-weight: 700;
                margin-bottom: 0.5rem; text-shadow: 2px 2px 8px rgba(0,0,0,0.4);
            }
            .login-subtitle { text-align: center; color: rgba(255, 255, 255, 0.9); margin-bottom: 2rem; }
            
            /* Input & Button Styling di dalam login-box */
            .login-box label { color: white !important; font-weight: 600; }
            .login-box input[type="text"], .login-box input[type="password"] {
                background-color: rgba(255, 255, 255, 0.8) !important;
                border: 1px solid rgba(255, 255, 255, 0.4) !important;
                color: #333 !important;
                border-radius: 8px !important;
            }
            .login-box .stButton>button { 
                background-color: white; color: #2E8B57; border-color: transparent; 
                width: 100%; margin-top: 1rem;
            }
            .login-box .stTabs [role="tab"] {
                color: white; border-bottom: 2px solid transparent; padding: 10px 0; margin: 0 15px;
            }
            .login-box .stTabs [aria-selected="true"] {
                color: white; border-bottom: 2px solid white;
            }
            
            /* SCRIPT PENTING UNTUK MENYEMBUNYIKAN TULISAN keyboard_double_arrow_right */
            
            /* Target berdasarkan konten teks (metode terakhir) */
            div:contains("keyboard_double_arrow_right") {
                display: none !important; 
            }
            
            /* Target div di area atas main content (berubah-ubah, tapi worth a try) */
            .st-emotion-cache-1yrk8w, 
            .st-emotion-cache-ocqkz6,
            .st-emotion-cache-18ni2g6:first-child,
            .st-emotion-cache-1ky8tcr { 
                display: none !important; 
            }

        </style>
    """, unsafe_allow_html=True)


# --- HALAMAN UTAMA APLIKASI ---

st.set_page_config(page_title="Smart Farming Buah Naga", layout="wide")
load_css()

# Inisialisasi Session State
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# --- Konfigurasi Referensi Firebase ---
sensor_ref = db.reference("sensor")
status_ref = db.reference("status")
kontrol_ref = db.reference("kontrol")
manual_ref = db.reference("manual")
irigasi_ref = db.reference("irigasi_log") 

# Halaman Login/Register
if not st.session_state.authenticated:
    
    st.markdown('<div class="login-page-container">', unsafe_allow_html=True)
    
    with st.container():
        # Menggunakan bobot numerik yang valid
        _, form_col, _ = st.columns([1, 3, 1]) 
        with form_col:
            st.markdown('<div class="login-box">', unsafe_allow_html=True)
            st.markdown('<div class="login-title">🐉 Smart Farming</div>', unsafe_allow_html=True)
            st.markdown('<p class="login-subtitle">Akses dasboard monitoring cerdas</p>', unsafe_allow_html=True)
        
            tab_login, tab_register = st.tabs(["🔑 Login", "📝 Buat Akun"])
            
            with tab_login:
                with st.form("login_form"):
                    email = st.text_input("Email", key="login_email", placeholder="anda@email.com")
                    password = st.text_input("Password", type="password", key="login_pass", placeholder="••••••••")
                    submitted = st.form_submit_button("🔓 Masuk")
                    if submitted:
                        try:
                            auth.sign_in_with_email_and_password(email, password)
                            st.session_state.authenticated = True
                            st.session_state.user_email = email
                            st.rerun()
                        except Exception:
                            st.error("❌ Email atau password salah.")
            
            with tab_register:
                with st.form("register_form"):
                    new_email = st.text_input("Email Baru", key="reg_email", placeholder="email.baru@email.com")
                    new_password = st.text_input("Password Baru", type="password", key="reg_pass", placeholder="Minimal 6 karakter")
                    submitted = st.form_submit_button("🆕 Daftarkan Akun")
                    if submitted:
                        try:
                            auth.create_user_with_email_and_password(new_email, new_password)
                            st.success("✅ Akun berhasil dibuat. Silakan login.")
                        except Exception:
                            st.error(f"❌ Gagal membuat akun: Pastikan format email benar dan password minimal 6 karakter.")
            
            st.markdown('</div>', unsafe_allow_html=True) 
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()


# --- DASBOR UTAMA (SETELAH LOGIN) ---

with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: var(--primary-color); font-family: Poppins, sans-serif;'>🐉 SmartFarm</h1>", unsafe_allow_html=True)
    st.markdown("---")
    st.write(f"Selamat datang, **{st.session_state.get('user_email', 'Petani')}**!")
    
    menu = st.radio("Navigasi", ["🌱 Sensor & Monitoring", "🛠️ Kontrol Sistem"], label_visibility="collapsed")
    
    st.markdown("---")
    st.info("Aplikasi ini memonitor kebun buah naga secara berkala menggunakan sensor IoT.")
    if st.button("🚪 Logout"):
        st.session_state.authenticated = False
        st.session_state.pop('user_email', None)
        st.rerun()
    if st.button("🔄 Refresh Data"):
        st.rerun()

# --------------------------------------------------------------------------------------
# MENU 1: SENSOR & MONITORING
# --------------------------------------------------------------------------------------
if menu == "🌱 Sensor & Monitoring":
    st.title("🌱 Dasbor Sensor & Monitoring")
    st.markdown("Pantau kondisi kebun buah naga Anda secara *real-time*.")
    st.markdown("---")

    sensor_data = sensor_ref.get() or {}
    status_data = status_ref.get() or {}
    irigasi_data = irigasi_ref.get() or {}

    ## 1. Kondisi Aktual
    with st.container(border=True):
        st.subheader("📊 Kondisi Aktual Kebun")
        # 5 Kolom: Kelembaban 1, Kelembaban 2, Cahaya, Volume Air Keluar, Volume Tandon
        cols = st.columns(5)
        
        # Kelembaban & Cahaya
        cols[0].markdown(f'<div class="metric-card-v2"><div class="icon moisture">💧</div><div class="value">{sensor_data.get("moisture1", 0)}%</div><div class="label">Kelembapan Tanah 1</div></div>', unsafe_allow_html=True)
        cols[1].markdown(f'<div class="metric-card-v2"><div class="icon moisture">💧</div><div class="value">{sensor_data.get("moisture2", 0)}%</div><div class="label">Kelembapan Tanah 2</div></div>', unsafe_allow_html=True)
        cols[2].markdown(f'<div class="metric-card-v2"><div class="icon light">☀️</div><div class="value">{sensor_data.get("lux", 0)} lx</div><div class="label">Intensitas Cahaya</div></div>', unsafe_allow_html=True)
        
        # Water Flow & Tandon Metrics
        cols[3].markdown(f'<div class="metric-card-v2"><div class="icon water">💧</div><div class="value">{sensor_data.get("total_volume", 0):.2f} L</div><div class="label">Volume Air Keluar</div></div>', unsafe_allow_html=True)
        cols[4].markdown(f'<div class="metric-card-v2"><div class="icon tank">🛢️</div><div class="value">{sensor_data.get("water_tank_level", 0)}%</div><div class="label">Volume Tandon Air</div></div>', unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Debit Air
        col_flow, _, _ = st.columns(3)
        col_flow.markdown(f'<div class="metric-card-v2"><div class="icon water">🌊</div><div class="value">{sensor_data.get("flow_rate", 0):.2f} L/min</div><div class="label">Debit Air Aktual</div></div>', unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.subheader("⚙️ Status Otomatisasi Sistem")
        status_lampu = status_data.get("lampu", "OFF")
        status_solenoid = status_data.get("solenoid", "OFF")
        col1, col2 = st.columns(2)
        lamp_class = "lamp-on" if status_lampu == "ON" else "lamp-off"
        solenoid_class = "solenoid-on" if status_solenoid == "ON" else "solenoid-off"
        
        col1.markdown(f'<div class="status-box {lamp_class}"><span>💡</span><span>Status Lampu: {status_lampu}</span></div>', unsafe_allow_html=True)
        col2.markdown(f'<div class="status-box {solenoid_class}"><span>💧</span><span>Status Solenoid: {status_solenoid}</span></div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)

    ## 2. Efektivitas Irigasi dan Status Harian
    with st.container(border=True):
        st.subheader("💧 Statistik Irigasi")
        
        last_moist_before = irigasi_data.get("last_moisture_before", 0)
        last_moist_after = irigasi_data.get("last_moisture_after", 0)
        kenaikan_moisture = last_moist_after - last_moist_before
        
        col_eff, col_morning, col_evening = st.columns(3)

        if kenaikan_moisture > 0:
            delta_str = f"+{kenaikan_moisture:.1f}%"
            delta_color = "inverse"
            message = "Penyiraman berhasil meningkatkan kelembaban tanah."
        elif last_moist_after > 0:
            delta_str = f"0%"
            delta_color = "off"
            message = "Kelembaban tidak berubah (tanah sudah cukup basah atau durasi kurang)."
        else:
            delta_str = f"N/A"
            delta_color = "off"
            message = "Belum ada log penyiraman selesai."

        col_eff.metric(
            label="Kenaikan Kelembaban Terakhir",
            value=f"{last_moist_before:.1f}% → {last_moist_after:.1f}%",
            delta=delta_str,
            delta_color=delta_color
        )
        col_eff.caption(message)

        # Status Siram Harian
        today_str = date.today().isoformat()
        
        last_morning = irigasi_data.get("irrigated_morning_today", "N/A")
        is_morning_done = (last_morning == today_str)
        morning_class = "done" if is_morning_done else "pending"
        morning_text = "✅ Sudah Siram Pagi" if is_morning_done else "❌ Belum Siram Pagi"
        
        col_morning.markdown(f'<div class="daily-status-card {morning_class}"><span>{morning_text}</span></div>', unsafe_allow_html=True)
        col_morning.caption("Status jadwal 08:00 WIB.")
        
        last_evening = irigasi_data.get("irrigated_evening_today", "N/A")
        is_evening_done = (last_evening == today_str)
        evening_class = "done" if is_evening_done else "pending"
        evening_text = "✅ Sudah Siram Sore" if is_evening_done else "❌ Belum Siram Sore"
        
        col_evening.markdown(f'<div class="daily-status-card {evening_class}"><span>{evening_text}</span></div>', unsafe_allow_html=True)
        col_evening.caption("Status jadwal 16:00 WIB.")
        
    st.markdown("<br>", unsafe_allow_html=True)

    ## 3. Grafik Historis
    with st.container(border=True):
        col_header, col_button = st.columns([3, 1])
        with col_header:
            st.subheader("📈 Grafik Historis Sensor")
        
        history_file = "history_log.csv"
        # Tambahkan kolom 'water_tank_level' ke DataFrame
        columns_list = ["timestamp", "moisture1", "moisture2", "lux", "flow_rate", "total_volume", "water_tank_level"]
        try:
            history_df = pd.read_csv(history_file)
            history_df["timestamp"] = pd.to_datetime(history_df["timestamp"])
        except (FileNotFoundError, pd.errors.EmptyDataError):
             history_df = pd.DataFrame(columns=columns_list)
        except Exception:
             history_df = pd.DataFrame(columns=columns_list)

        current_time = datetime.now()
        new_row = {
            "timestamp": current_time, 
            "moisture1": sensor_data.get("moisture1", 0), 
            "moisture2": sensor_data.get("moisture2", 0), 
            "lux": sensor_data.get("lux", 0),
            "flow_rate": sensor_data.get("flow_rate", 0),
            "total_volume": sensor_data.get("total_volume", 0),
            "water_tank_level": sensor_data.get("water_tank_level", 0)
        }

        should_update = True
        if not history_df.empty:
            last_entry_time = pd.to_datetime(history_df.iloc[-1]['timestamp'])
            if (last_entry_time.year == current_time.year and last_entry_time.month == current_time.month and 
                last_entry_time.day == current_time.day and last_entry_time.hour == current_time.hour and 
                last_entry_time.minute == current_time.minute):
                should_update = False

        if should_update:
            history_df = pd.concat([history_df, pd.DataFrame([new_row])], ignore_index=True).tail(200)
            try:
                history_df.to_csv(history_file, index=False)
            except Exception as e:
                st.warning(f"Gagal menyimpan ke history_log.csv: {e}")
        
        with col_button:
            st.download_button(
                label="📥 Unduh Riwayat",
                data=history_df.to_csv(index=False).encode('utf-8'),
                file_name='riwayat_sensor.csv',
                mime='text/csv'
            )

        chart_df = history_df.tail(100)

        # Chart Kelembaban
        moisture_chart = alt.Chart(chart_df, title="Tren Kelembapan Tanah").transform_fold(
            ["moisture1", "moisture2"], as_=["Sensor", "Nilai"]
        ).mark_line(size=3).encode(
            x=alt.X("timestamp:T", title="Waktu"), 
            y=alt.Y("Nilai:Q", title="Kelembaban (%)", scale=alt.Scale(domain=[0, 100])), 
            color=alt.Color("Sensor:N", title="Sensor", scale=alt.Scale(scheme='category10')), 
            tooltip=['timestamp:T', 'Sensor:N', 'Nilai:Q']
        ).properties(height=300).interactive()
        st.altair_chart(moisture_chart, use_container_width=True, theme="streamlit")

        # Chart Intensitas Cahaya
        lux_chart = alt.Chart(chart_df, title="Tren Intensitas Cahaya").mark_area(
            line={'color':'#F59E0B'}, 
            color=alt.Gradient(gradient='linear', stops=[alt.GradientStop(color='white', offset=0), alt.GradientStop(color='#FBBF24', offset=1)], x1=1, x2=1, y1=1, y2=0)
        ).encode(
            x=alt.X("timestamp:T", title="Waktu"), 
            y=alt.Y("lux:Q", title="Intensitas Cahaya (Lux)"), 
            tooltip=['timestamp:T', 'lux:Q']
        ).properties(height=300).interactive()
        st.altair_chart(lux_chart, use_container_width=True, theme="streamlit")
        
        # Chart Volume Tandon Air
        tank_chart = alt.Chart(chart_df, title="Tren Volume Tandon Air").mark_line(color='#800080').encode(
            x=alt.X("timestamp:T", title="Waktu"),
            y=alt.Y("water_tank_level:Q", title="Tandon (%)", scale=alt.Scale(domain=[0, 100])),
            tooltip=['timestamp:T', 'water_tank_level:Q']
        ).properties(height=300).interactive()
        st.altair_chart(tank_chart, use_container_width=True, theme="streamlit")
        
        # Chart Debit Air
        flow_chart = alt.Chart(chart_df, title="Tren Debit Air").mark_line(color='#3B82F6').encode(
            x=alt.X("timestamp:T", title="Waktu"),
            y=alt.Y("flow_rate:Q", title="Debit Air (L/min)"),
            tooltip=['timestamp:T', 'flow_rate:Q']
        ).properties(height=300).interactive()
        st.altair_chart(flow_chart, use_container_width=True, theme="streamlit")


# --------------------------------------------------------------------------------------
# MENU 2: KONTROL SISTEM
# --------------------------------------------------------------------------------------
elif menu == "🛠️ Kontrol Sistem":
    st.title("🛠️ Papan Kontrol Sistem")
    st.markdown("Ambil alih kontrol sistem atau serahkan pada otomatisasi cerdas.")
    st.markdown("---")
    
    kontrol_data = kontrol_ref.get() or {}
    status_data = status_ref.get() or {}
    
    st.subheader("💡 Status Aktual Sistem")
    status_lampu = status_data.get("lampu", "OFF")
    status_solenoid = status_data.get("solenoid", "OFF")
    col1, col2 = st.columns(2)
    
    lamp_class = "lamp-on" if status_lampu == "ON" else "lamp-off"
    solenoid_class = "solenoid-on" if status_solenoid == "ON" else "solenoid-off"
    
    col1.markdown(f'<div class="status-box {lamp_class}"><span>💡</span><span>Status Lampu: {status_lampu}</span></div>', unsafe_allow_html=True)
    col2.markdown(f'<div class="status-box {solenoid_class}"><span>💧</span><span>Status Solenoid Valve: {status_solenoid}</span></div>', unsafe_allow_html=True)
    st.markdown("---")

    with st.form("form_kontrol"):
        
        ## Mode Kontrol On/Off
        st.subheader("Mode Kontrol On/Off")
        col1, col2 = st.columns(2)
        
        # Kontrol Lampu
        with col1:
            with st.container(border=True):
                st.caption("Mode Otomatis menyalakan lampu saat gelap. Mode Manual memungkinkan Anda mengontrol penuh.")
                
                initial_lampu_index = 0 if kontrol_data.get("lampu", 2) == 1 else 1 
                mode_lampu = st.radio("Mode Lampu", ["Manual", "Otomatis"], index=initial_lampu_index, horizontal=True, key="mode_lampu")

                initial_manual_lampu = "ON" if status_lampu == "ON" else "OFF"
                manual_lampu_val = st.radio("Status Manual Lampu", ["OFF", "ON"], 
                                         index=1 if initial_manual_lampu == "ON" else 0,
                                         horizontal=True, 
                                         key="manual_lampu", 
                                         disabled=(mode_lampu == "Otomatis"))

        # Kontrol Solenoid Valve
        with col2:
            with st.container(border=True):
                st.caption("Mode Otomatis membuka valve saat tanah kering. Mode Manual untuk irigasi sesuai kebutuhan.")
                
                initial_solenoid_index = 0 if kontrol_data.get("solenoid", 2) == 1 else 1 
                mode_solenoid = st.radio("Mode Solenoid", ["Manual", "Otomatis"], index=initial_solenoid_index, horizontal=True, key="mode_solenoid")
                
                initial_manual_solenoid = "ON" if status_solenoid == "ON" else "OFF"
                manual_solenoid_val = st.radio("Status Manual Solenoid", ["OFF", "ON"], 
                                         index=1 if initial_manual_solenoid == "ON" else 0,
                                         horizontal=True, 
                                         key="manual_solenoid", 
                                         disabled=(mode_solenoid == "Otomatis"))
        
        st.markdown("---")

        ## Pengaturan Jadwal Penyiraman RTC
        st.subheader("⏰ Pengaturan Jadwal Penyiraman Otomatis (RTC)")
        st.caption("Atur waktu penyiraman rutin yang diinginkan pada mode Solenoid Otomatis.")

        try:
            db_morning_time = kontrol_data.get("water_morning_time", "08:00")
            default_morning = datetime.strptime(db_morning_time, "%H:%M").time()
        except ValueError:
            default_morning = time(8, 0)
            
        try:
            db_evening_time = kontrol_data.get("water_evening_time", "16:00")
            default_evening = datetime.strptime(db_evening_time, "%H:%M").time()
        except ValueError:
            default_evening = time(16, 0)
        
        col_morn, col_even = st.columns(2)
        
        morning_time = col_morn.time_input(
            "Waktu Penyiraman Pagi (00:00 - 11:59)", 
            value=default_morning, 
            key="morning_time",
            help="Penyiraman akan dipicu pada waktu ini jika kelembaban di bawah batas."
        )
        
        evening_time = col_even.time_input(
            "Waktu Penyiraman Sore (12:00 - 23:59)", 
            value=default_evening, 
            key="evening_time",
            help="Penyiraman akan dipicu pada waktu ini jika kelembaban di bawah batas."
        )

        st.markdown("---")
        
        ## Pengaturan Jadwal Lampu RTC BARU
        st.subheader("💡 Pengaturan Jadwal Lampu Otomatis")
        st.caption("Atur waktu kapan lampu harus menyala dan mati pada mode Lampu Otomatis.")

        try:
            db_lamp_on_time = kontrol_data.get("lamp_on_time", "18:00")
            default_lamp_on = datetime.strptime(db_lamp_on_time, "%H:%M").time()
        except ValueError:
            default_lamp_on = time(18, 0)
            
        try:
            db_lamp_off_time = kontrol_data.get("lamp_off_time", "06:00")
            default_lamp_off = datetime.strptime(db_lamp_off_time, "%H:%M").time()
        except ValueError:
            default_lamp_off = time(6, 0)
        
        col_on, col_off = st.columns(2)
        
        lamp_on_time = col_on.time_input(
            "Waktu Lampu Menyala (Malam)", 
            value=default_lamp_on, 
            key="lamp_on_time",
            help="Lampu akan menyala pada waktu ini (digunakan pada mode Otomatis)."
        )
        
        lamp_off_time = col_off.time_input(
            "Waktu Lampu Mati (Pagi)", 
            value=default_lamp_off, 
            key="lamp_off_time",
            help="Lampu akan mati pada waktu ini (digunakan pada mode Otomatis)."
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button("🚀 Terapkan Pengaturan")
        
        if submitted:
            # Update mode kontrol
            kontrol_ref.update({
                "lampu": 1 if mode_lampu == "Manual" else 2, 
                "solenoid": 1 if mode_solenoid == "Manual" else 2
            })
            
            # Update manual override
            if mode_lampu == "Manual":
                manual_ref.update({"lampu": 1 if manual_lampu_val == "ON" else 0})
                status_ref.update({"lampu": manual_lampu_val})
                
            if mode_solenoid == "Manual":
                manual_ref.update({"solenoid": 1 if manual_solenoid_val == "ON" else 0}) 
                status_ref.update({"solenoid": manual_solenoid_val})

            # Update Jadwal RTC
            kontrol_ref.update({
                "water_morning_time": morning_time.strftime("%H:%M"),
                "water_evening_time": evening_time.strftime("%H:%M"),
                "lamp_on_time": lamp_on_time.strftime("%H:%M"),  # BARU
                "lamp_off_time": lamp_off_time.strftime("%H:%M") # BARU
            })

            st.success("✅ Pengaturan sistem dan jadwal berhasil diperbarui!")
            st.rerun()
