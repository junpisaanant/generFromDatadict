"""
streamlit_app.py – ER Diagram Generator (Streamlit UI)
รันแบบ local:  streamlit run streamlit_app.py
Deploy:        Streamlit Community Cloud (share.streamlit.io)
"""

import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from er_core import parse_docx, generate_drawio, layout_tables, get_stats, DOCX_OK

# ── Page config ─────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ER Diagram Generator",
    page_icon="🗂️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

DEFAULT_FILENAME = "3_ER_จำหน่ายวัสดุเครื่องจักรกล (อะไหล่).drawio"

# ── Custom CSS ───────────────────────────────────────────────────────────
st.markdown("""
<style>
  .block-container { padding-top: 2rem; max-width: 900px; }
  .metric-box {
    background: #eff6ff; border: 1px solid #bfdbfe;
    border-radius: 10px; padding: 16px; text-align: center;
  }
  .metric-val { font-size: 2rem; font-weight: 700; color: #2563eb; }
  .metric-lbl { font-size: .8rem; color: #6b7280; margin-top: 4px; }
  .sheet-card {
    background: #fff; border: 1px solid #e5e7eb;
    border-radius: 8px; padding: 12px 14px; margin-bottom: 8px;
  }
  .sheet-title { font-weight: 700; color: #1e40af; margin-bottom: 6px; }
  code { background:#eff6ff; border-radius:4px; padding:1px 6px;
         color:#1d4ed8; font-size:.82rem; font-family:monospace; }
  .stDownloadButton > button {
    background: #16a34a !important; color: white !important;
    border-radius: 8px !important; font-weight: 600 !important;
    padding: 10px 24px !important; font-size: 1rem !important;
  }
  .stDownloadButton > button:hover { background: #15803d !important; }
</style>
""", unsafe_allow_html=True)

# ── Header ───────────────────────────────────────────────────────────────
st.markdown("""
<div style="background:linear-gradient(135deg,#1e3a5f,#2563eb);
            color:white;border-radius:12px;padding:20px 28px;margin-bottom:24px;">
  <div style="font-size:1.4rem;font-weight:700">🗂️ ER Diagram Generator</div>
  <div style="font-size:.88rem;opacity:.85;margin-top:4px">
    แปลง Data Dictionary (.docx) → ไฟล์ ER Diagram (.drawio) แบบอัตโนมัติ<br>
    รองรับ Crow's Foot Notation · FK-aware Pagination · Dynamic Width
  </div>
</div>
""", unsafe_allow_html=True)

if not DOCX_OK:
    st.error("❌ ไม่พบ python-docx — กรุณาติดตั้ง: `pip install python-docx`")
    st.stop()

# ── Step 1: Upload ───────────────────────────────────────────────────────
with st.container():
    st.subheader("📄 อัปโหลด Data Dictionary")
    uploaded = st.file_uploader(
        "เลือกไฟล์ .docx (Word Document)",
        type=["docx"],
        label_visibility="collapsed",
        help="ไฟล์ Data Dictionary รูปแบบ Word ที่มีหัวข้อ Heading 3 สำหรับแต่ละตาราง",
    )

# ── Step 2: Output filename ──────────────────────────────────────────────
    out_name = st.text_input(
        "📝 ชื่อไฟล์ Output (.drawio)",
        value=DEFAULT_FILENAME,
        help="ชื่อไฟล์ที่จะดาวน์โหลด เช่น 3_ER_MyDatabase.drawio",
    )
    if out_name and not out_name.lower().endswith(".drawio"):
        out_name += ".drawio"

# ── Step 3: Generate ─────────────────────────────────────────────────────
    generate_clicked = st.button(
        "▶  สร้าง ER Diagram",
        disabled=(uploaded is None),
        type="primary",
        use_container_width=True,
    )

st.divider()

# ── Processing ───────────────────────────────────────────────────────────
if generate_clicked and uploaded is not None:
    with st.spinner("กำลังอ่านและประมวลผล Data Dictionary…"):
        try:
            docx_bytes = uploaded.read()
            tables = parse_docx(docx_bytes)

            if not tables:
                st.error("❌ ไม่พบตารางข้อมูล — ตรวจสอบว่าหัวข้อแต่ละตารางใช้ Heading 3 และชื่อตารางอยู่ในวงเล็บ เช่น `(TABLE_NAME)`")
                st.stop()

            xml_content = generate_drawio(tables)
            pages       = layout_tables(tables)
            stats       = get_stats(tables, pages)

            st.session_state["xml"]      = xml_content
            st.session_state["stats"]    = stats
            st.session_state["filename"] = out_name or DEFAULT_FILENAME

        except Exception as e:
            st.error(f"❌ เกิดข้อผิดพลาด: {e}")
            st.stop()

# ── Show results (persist across reruns) ────────────────────────────────
if "xml" in st.session_state:
    stats    = st.session_state["stats"]
    xml      = st.session_state["xml"]
    filename = st.session_state["filename"]

    total_edges = sum(p["edge_count"] for p in stats["pages"])

    # Stats row
    st.subheader("📊 ผลลัพธ์")
    c1, c2, c3, c4 = st.columns(4)
    for col, icon, val, lbl in [
        (c1, "📋", stats["table_count"],  "ตาราง"),
        (c2, "🔢", stats["column_count"], "คอลัมน์"),
        (c3, "🔗", total_edges,           "FK Edges"),
        (c4, "📄", stats["page_count"],   "Sheets"),
    ]:
        col.markdown(f"""
        <div class="metric-box">
          <div class="metric-val">{icon} {val}</div>
          <div class="metric-lbl">{lbl}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Sheet breakdown
    with st.expander("🗂️ รายละเอียดแต่ละ Sheet", expanded=True):
        cols = st.columns(2)
        for i, page in enumerate(stats["pages"]):
            with cols[i % 2]:
                tags = " ".join(f"`{t}`" for t in page["tables"])
                st.markdown(f"""
                <div class="sheet-card">
                  <div class="sheet-title">
                    📄 Sheet {i+1}
                    <span style="color:#6b7280;font-weight:400;font-size:.85rem">
                      — {len(page['tables'])} ตาราง, {page['edge_count']} edges
                    </span>
                  </div>
                  <div style="line-height:1.8">{tags}</div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Download
    st.subheader("⬇️ ดาวน์โหลด")
    xml_bytes = xml.encode("utf-8")
    size_kb   = len(xml_bytes) / 1024

    col_dl, col_info = st.columns([1, 2])
    with col_dl:
        st.download_button(
            label="⬇️  ดาวน์โหลด .drawio",
            data=xml_bytes,
            file_name=filename,
            mime="application/xml",
            use_container_width=True,
        )
    with col_info:
        st.markdown(f"""
        <div style="padding:12px 0;color:#374151">
          <div>📁 <strong>{filename}</strong></div>
          <div style="color:#6b7280;font-size:.85rem;margin-top:4px">
            {size_kb:.1f} KB · XML · เปิดด้วย diagrams.net หรือ draw.io Desktop
          </div>
        </div>
        """, unsafe_allow_html=True)

# ── Empty state ──────────────────────────────────────────────────────────
elif "xml" not in st.session_state:
    st.markdown("""
    <div style="text-align:center;padding:40px;color:#9ca3af">
      <div style="font-size:3rem">📂</div>
      <div style="margin-top:8px">อัปโหลดไฟล์ .docx แล้วกดปุ่ม <strong>สร้าง ER Diagram</strong></div>
    </div>
    """, unsafe_allow_html=True)

# ── Footer ───────────────────────────────────────────────────────────────
st.markdown("""
<hr style="margin-top:2rem;border-color:#e5e7eb">
<div style="text-align:center;color:#9ca3af;font-size:.78rem;padding-bottom:1rem">
  ER Diagram Generator · python-docx · Draw.io XML · FK-aware A4 Pagination · Crow's Foot Notation
</div>
""", unsafe_allow_html=True)
