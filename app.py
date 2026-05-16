# app.py
import streamlit as st
from functions import (
    extract_from_pdf, extract_from_docx, polish_with_ai,
    generate_professional_summary, ats_scorecard, generate_pdf
)
import io

# Konfigurasi halaman
st.set_page_config(page_title="AI Resume Agent", layout="wide")
st.title("📄 AI Resume Agent - ATS Optimized")
st.sidebar.subheader("Pengaturan Bahasa")
language = st.sidebar.radio("Pilih bahasa CV:", ["Bahasa Indonesia", "English"])
target_lang = "id" if language == "Bahasa Indonesia" else "en"
st.session_state.target_lang = target_lang
st.markdown("Buat CV profesional yang ramah ATS dengan bantuan AI.")

# Inisialisasi session state
if 'resume_data' not in st.session_state:
    st.session_state.resume_data = {}
if 'polished_text' not in st.session_state:
    st.session_state.polished_text = ""
if 'step' not in st.session_state:
    st.session_state.step = "input"  # input, preview, score

# ==================== SIDEBAR: PILIH METODE INPUT ====================
with st.sidebar:
    st.subheader("Metode Input")
    input_method = st.radio("Pilih cara memasukkan data:", ["Upload CV Lama", "Isi Formulir Manual"])

# ==================== MAIN AREA ====================
if st.session_state.step == "input":
    if input_method == "Upload CV Lama":
        uploaded_file = st.file_uploader("Unggah CV (PDF atau DOCX)", type=["pdf", "docx"])
        if uploaded_file is not None:
            with st.spinner("Membaca file..."):
                if uploaded_file.name.endswith(".pdf"):
                    raw_text = extract_from_pdf(uploaded_file)
                else:
                    raw_text = extract_from_docx(uploaded_file)
            st.success("File berhasil dibaca!")
            st.text_area("Teks hasil ekstraksi (bisa diedit):", raw_text, height=200)
            if st.button("Proses dengan AI"):
                # Simpan data mentah ke session state
                st.session_state.raw_data = raw_text
                # Lakukan polishing sederhana (contoh: polish seluruh teks sebagai satu blok)
                polished = polish_with_ai(raw_text, target_lang="en")  # default inggris
                st.session_state.polished_text = polished
                st.session_state.step = "preview"
                st.rerun()

    else:  # Isi Formulir Manual
        st.subheader("Data Diri")
        name = st.text_input("Nama Lengkap")
        email = st.text_input("Email")
        phone = st.text_input("Nomor Telepon")
        
        status = st.radio("Status Saat Ini:", ["Mahasiswa/Fresh Graduate", "Profesional Berpengalaman"])
        
        if status == "Mahasiswa/Fresh Graduate":
            edu = st.text_area("Pendidikan (Jurusan, Universitas, Tahun Lulus)")
            thesis = st.text_input("Judul Skripsi/Tugas Akhir (opsional)")
            org = st.text_area("Pengalaman Organisasi / Proyek Akademik (pisahkan dengan koma atau baris baru)")
            skills = st.text_input("Keterampilan (misal: Python, Public Speaking)")
            work_exp = ""  # tidak wajib
        else:
            work_exp = st.text_area("Pengalaman Kerja (Posisi, Perusahaan, Tahun, Deskripsi tugas)")
            edu = st.text_area("Pendidikan Terakhir")
            skills = st.text_input("Keterampilan Teknis & Non-teknis")
            org = ""
            thesis = ""
        
        if st.button("Generate CV dengan AI"):
    # Validasi input sederhana
         if not name or not email:
            st.error("Nama dan email harus diisi!")
        else:
            # Definisikan user_data
            user_data = {
                "name": name,
                "contact": f"{email} | {phone}",
                "education": edu,
                "work_experience": work_exp,
                "skills": skills,
                "status": status,
                "thesis": thesis,
                "organization": org
            }
            # Hasilkan ringkasan profesional
        with st.spinner("AI sedang menulis ringkasan profesional..."):
            summary = generate_professional_summary(user_data, target_lang=st.session_state.get("target_lang", "id"))
            # Polish pengalaman kerja jika ada
            exp_bullets = []
            if work_exp:
                  lines = work_exp.split("\n")
                  for line in lines:
                      if line.strip():
                         polished = polish_with_ai(line, target_lang=st.session_state.get("target_lang", "id"))
                         exp_bullets.append(polished)
                # Pisahkan berdasarkan baris baru (asumsi satu paragraf)
                         lines = work_exp.split("\n")
                  for line in lines:
                            if line.strip():
                                polished = polish_with_ai(line, target_lang=st.session_state.target_lang)
                                exp_bullets.append(polished)
                    # Untuk fresh grad, Polish organisasi/proyek
                            if org and not work_exp:
                              org_lines = org.split("\n")
                              for line in org_lines:
                                if line.strip():
                                 polished = polish_with_ai(line, target_lang=st.session_state.target_lang)
                            exp_bullets.append(polished)
            # Simpan ke session state
            st.session_state.resume_data = {
                "name": name,
                "contact": f"{email} | {phone}",
                "summary": summary,
                "experience": exp_bullets if exp_bullets else ["Belum ada pengalaman formal, tapi memiliki potensi besar untuk dikembangkan."],
                "education": edu,
                "skills": skills
            }
            # Buat teks polos untuk pratinjau (gabungkan)
            preview_text = f"{summary}\n\nPendidikan:\n{edu}\n\nPengalaman:\n" + "\n".join(exp_bullets) + f"\n\nKeterampilan:\n{skills}"
            st.session_state.polished_text = preview_text
            st.session_state.step = "preview"
            st.rerun()

# ==================== TAMPILAN PRATINJAU & EDIT ====================
if st.session_state.step == "preview":
    st.subheader("✏️ Pratinjau & Edit Hasil AI")
    st.info("Anda dapat mengedit teks di bawah ini sebelum mengunduh PDF.")
    
    edited_text = st.text_area("Teks CV (bisa diedit langsung):", st.session_state.polished_text, height=400)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Regenerate dengan AI (ulang)"):
            # Contoh: polish ulang teks yang diedit
            regenerated = polish_with_ai(edited_text, target_lang=st.session_state.target_lang)
            st.session_state.polished_text = regenerated
            st.rerun()
    with col2:
        if st.button("✅ Lanjut ke Skor ATS & Download"):
            st.session_state.polished_text = edited_text
            st.session_state.step = "score"
            st.rerun()
    
    if st.button("← Kembali ke Input"):
        st.session_state.step = "input"
        st.rerun()

# ==================== SKOR ATS & DOWNLOAD ====================
if st.session_state.step == "score":
    st.subheader("📊 ATS Scorecard & Finalisasi")
    
    # Hitung skor ATS
    score_result = ats_scorecard(st.session_state.polished_text)
    st.metric("ATS Compatibility Score", f"{score_result['score']} / 100")
    if score_result['suggestions']:
        st.warning("Saran perbaikan:")
        for s in score_result['suggestions']:
            st.write(f"- {s}")
    
    st.markdown("---")
    st.subheader("📥 Unduh CV")
    
    # Konversi teks yang sudah diedit menjadi dictionary untuk PDF
    # (Parsing sederhana: asumsikan teks memiliki bagian SUMMARY, EDUCATION, EXPERIENCE, SKILLS)
    # Di sini kita buat resume_dict dari st.session_state.resume_data yang sudah ada, namun tetap gunakan teks editan untuk isi.
    # Untuk kepraktisan, kita buat ulang resume_dict dari data yang tersimpan di session state, bukan dari teks editan.
    # Tapi Anda bisa meningkatkan parsing nanti.
    if 'resume_data' in st.session_state and st.session_state.resume_data:
        final_dict = st.session_state.resume_data
        # Update summary dari teks editan (coba ambil paragraf pertama)
        lines = st.session_state.polished_text.split("\n")
        final_dict["summary"] = lines[0] if lines else ""
    else:
        # fallback
        final_dict = {
            "name": "Pengguna",
            "contact": "",
            "summary": st.session_state.polished_text[:200],
            "experience": [],
            "education": "",
            "skills": ""
        }
    
    pdf_bytes = generate_pdf(final_dict)
    st.download_button(
        label="⬇️ Download PDF",
        data=pdf_bytes,
        file_name="resume_ats_optimized.pdf",
        mime="application/pdf"
    )
    
    if st.button("🔄 Buat CV Baru"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()