import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import textwrap
import io
import os
import math
import zipfile
import re
from datetime import date

# Try to write dark theme config (harmless if fails)
try:
    cfg_dir = os.path.join(os.getcwd(), ".streamlit")
    os.makedirs(cfg_dir, exist_ok=True)
    cfg_path = os.path.join(cfg_dir, "config.toml")
    with open(cfg_path, "w", encoding="utf-8") as f:
        f.write('[theme]\nbase = "dark"\n')
except Exception:
    pass

# ---------- Shared helpers ----------
def safe_filename(s):
    if s is None:
        return ""
    s = str(s).strip()
    s = s.replace(" ", "_")
    return re.sub(r"[^A-Za-z0-9._-]", "", s)


def wrap_text(text, width):
    if text is None or str(text).strip() == "":
        return {"wrapped_text": "", "line_count": 0}
    words = str(text).split(" ")
    wrapped_lines = []
    current_line = ""
    lines_for_curr_text = 0
    for word in words:
        if current_line == "":
            projected_len = len(word)
        else:
            projected_len = len(current_line) + 1 + len(word)
        if projected_len > width:
            wrapped_lines.append(current_line)
            current_line = word
            lines_for_curr_text += 1
        else:
            current_line = word if current_line == "" else current_line + " " + word
    if current_line != "":
        wrapped_lines.append(current_line)
        lines_for_curr_text += 1
    return {"wrapped_text": "\n".join(wrapped_lines), "line_count": lines_for_curr_text}


# ---------- TableImage (for the "Tabel Maken" preview) ----------
class TableImage:
    def __init__(
        self,
        rows,
        cols,
        row_height,
        col_width,
        font_path="verdana.ttf",
        bold_font_path="verdanab.ttf",
        font_size=10,
        line_color=(0, 0, 0),
        bg_color=(255, 255, 255),
        line_width=2,
        wrap_width=30,
        padding_left=8,
    ):
        self.rows = int(rows)
        self.cols = int(cols)
        self.col_width = int(col_width)
        self.line_color = line_color
        self.bg_color = bg_color
        self.line_width = int(line_width)
        self.wrap_width = wrap_width
        self.padding_left = int(padding_left)
        if isinstance(row_height, list):
            if len(row_height) != self.rows:
                if len(row_height) < self.rows:
                    row_height = row_height + [row_height[-1]] * (self.rows - len(row_height))
                else:
                    row_height = row_height[: self.rows]
            self.row_height = [int(h) for h in row_height]
        else:
            self.row_height = [int(row_height)] * self.rows
        self.height = sum(self.row_height)
        self.width = int(self.cols * self.col_width)
        try:
            BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        except Exception:
            BASE_DIR = os.getcwd()
        self.font_path = os.path.join(BASE_DIR, font_path)
        self.bold_font_path = os.path.join(BASE_DIR, bold_font_path)
        self.font_size = int(font_size)
        self.cells = {}
        self.bold_cells = {}

    def set_text(self, row, col, text, bold=False):
        self.cells[(int(row), int(col))] = "" if text is None else str(text)
        self.bold_cells[(int(row), int(col))] = bool(bold)

    def draw(self):
        img = Image.new("RGB", (self.width, self.height), self.bg_color)
        draw = ImageDraw.Draw(img)
        y_positions = [0]
        for h in self.row_height:
            y_positions.append(y_positions[-1] + int(h))
        inset = max(0, self.line_width // 2)
        for r in range(self.rows):
            y0 = y_positions[r]
            y1 = y_positions[r + 1] - 1
            for c in range(self.cols):
                x0 = int(c * self.col_width)
                x1 = int(x0 + self.col_width) - 1
                draw.rectangle(
                    [x0 + inset, y0 + inset, x1 - inset, y1 - inset],
                    outline=self.line_color,
                    width=self.line_width,
                )
        for (r, c), text in self.cells.items():
            x = int(c * self.col_width)
            y = y_positions[r]
            bold = self.bold_cells.get((r, c), False)
            font_path = self.bold_font_path if bold else self.font_path
            try:
                font = ImageFont.truetype(font_path, self.font_size)
            except Exception:
                font = ImageFont.load_default()
            lines = []
            if text:
                paragraphs = str(text).split("\n")
                for p in paragraphs:
                    if p.strip() == "":
                        lines.append("")
                    else:
                        wrapped = textwrap.wrap(p, width=self.wrap_width) or [p]
                        lines.extend(wrapped)
            try:
                ascent, descent = font.getmetrics()
                line_height = ascent + descent
            except Exception:
                if lines:
                    try:
                        bbox = draw.textbbox((0, 0), lines[0], font=font)
                        line_height = bbox[3] - bbox[1]
                    except Exception:
                        _, h = font.getsize(lines[0])
                        line_height = h
                else:
                    line_height = getattr(font, "size", 12)
            cell_height = y_positions[r + 1] - y_positions[r]
            total_text_height = len(lines) * line_height
            block_top = y + (cell_height - total_text_height) / 2
            current_y = block_top
            for line in lines:
                draw.text((x + self.padding_left, current_y), line, fill=(0, 0, 0), font=font)
                current_y += line_height
        return img


# ---------- Sleepoptie image helper ----------
def create_sleepoptie_single_image(
    text,
    tekst_titel="title",
    tekst_itemnummer="1",
    canvas_height=None,
    max_chars_per_line=33,
    font_size=11,
    base_dir=None,
    num_columns=2,
):
    if not text or str(text).strip() == "":
        return None, None
    wrap_result = wrap_text(text.strip(), max_chars_per_line)
    wrapped_text = wrap_result["wrapped_text"]
    line_count = wrap_result["line_count"]
    if line_count == 1:
        calculated_height = 18
    else:
        calculated_height = max(10, (line_count * 15) + 5)
    if canvas_height is not None:
        height = max(calculated_height, canvas_height)
    else:
        height = calculated_height
    try:
        num_cols = int(num_columns) if num_columns and int(num_columns) > 0 else 2
    except Exception:
        num_cols = 2
    out_width = max(50, math.floor((450.0 / num_cols) - 15))
    if base_dir is None:
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        except Exception:
            base_dir = os.getcwd()
    template_path = os.path.join(base_dir, "500x500_template.png")
    if os.path.exists(template_path):
        try:
            tpl = Image.open(template_path).convert("RGB")
            tpl = tpl.resize((out_width, height), resample=Image.LANCZOS)
            img = tpl
        except Exception:
            img = Image.new("RGB", (out_width, height), "white")
    else:
        img = Image.new("RGB", (out_width, height), "white")
    draw = ImageDraw.Draw(img)
    verdana_path = os.path.join(base_dir, "verdana.ttf")
    try:
        font = ImageFont.truetype(verdana_path, font_size)
    except Exception:
        font = ImageFont.load_default()
    margin_x = 5
    margin_y = 3
    draw.multiline_text((margin_x, margin_y), wrapped_text, fill="black", font=font, spacing=4)
    filename = f"{tekst_titel}_{tekst_itemnummer}.png"
    return img, filename


# ---------- Streamlit UI & CSS ----------
st.set_page_config(page_title="Sleepoptie en Tabel Generator", layout="wide")
st.markdown(
    """
    <style>
      html, body, [data-testid="stAppViewContainer"] { background:#000; color:#fff; }
      .block-container { background: rgba(0,0,0,0.85); color: #fff; }
      footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)
st.info("Laatste Update: 2026-05-27 - Grootte van sleepopties bij 1 regel gefixt")

manual_filename = "Nieuwe Itemtypes Handleiding Invoer TOM.docx"
base_dir = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
manual_path = os.path.join(base_dir, manual_filename)
try:
    with open(manual_path, "rb") as f:
        manual_bytes = f.read()
    st.download_button(
        label="Klik hier om de handleiding voor invoer te downloaden!",
        data=manual_bytes,
        file_name=manual_filename,
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        key="download_manual",
    )
except FileNotFoundError:
    st.warning(f"Handleiding niet gevonden: {manual_filename}. Zet het bestand in de app-map ({base_dir}).")
except Exception as e:
    st.error(f"Kon handleiding niet laden: {e}")

st.caption("Links vul je informatie in, rechts zie je de plaatjes.")

mode = st.selectbox("Kies functie:", ["Tabel Maken", "Sleepopties Maken", "Forms Feedbacktool"], index=0)
left, right = st.columns([1, 1.2])

# ----------------- TABEL MAKEN (full functionality) -----------------
if mode == "Tabel Maken":
    with left:
        vakcode = st.text_input("Vakcode (optioneel)", value="", key="table_vakcode")
        tekst_titel = st.text_input("Titel van de tekst", value="title", key="table_titel")
        tekst_itemnummer = st.text_input("Item nummer (in selectie)", value="1", key="table_itemnr")
        table_type = st.selectbox(
            "Selecteer het Type sleepvraag",
            ("Type 1 (graphic gapmatch)", "Type 2 (graphic gapmatch categorize)"),
        )
        max_chars_per_line = st.number_input(
            "Kies het aantal karakters per regel",
            min_value=5,
            max_value=200,
            value=33,
            step=1,
            key="table_wrap_width",
        )
        with st.expander("Instellingen voor de afmetingen van de tabel", expanded=True):
            if table_type.startswith("Type 1"):
                rows = int(st.number_input("Hoeveel rijen heeft de tabel?", min_value=1, value=2, step=1, key="t1_rows"))
                cols = int(st.number_input("Hoeveel kolommen heeft de tabel?", min_value=1, value=2, step=1, key="t1_cols"))
                col_width = int(450 // cols)
                st.write(f"Met deze instellingen wordt de kolombreedte {col_width} pixels (450 // {cols})")
                heading_lines = 0
                has_heading_label = st.checkbox("Heeft de kop van de tabel een label?", value=False, key="t1_heading_has_label")
                if has_heading_label:
                    heading_lines = int(
                        st.number_input(
                            "Hoeveel regels zijn nodig voor het langste label in de kop?",
                            min_value=1,
                            value=1,
                            step=1,
                            key="heading_lines_type1",
                        )
                    )
                    st.write(f"De eerste rij van de tabel (de kop van de tabel) wordt {heading_lines * 18} pixels")
                longest_rows = int(
                    st.number_input(
                        "Hoeveel regels zijn nodig voor het langste antwoord?",
                        min_value=1,
                        value=1,
                        step=1,
                        key="t1_longest_rows",
                    )
                )
                if longest_rows == 1:
                    answer_row_height = 22
                else:
                    answer_row_height = int(longest_rows * 20)
                if heading_lines > 0:
                    first_row_height = heading_lines * 18
                    if rows == 1:
                        row_heights = [first_row_height]
                    else:
                        row_heights = [first_row_height] + [answer_row_height] * (rows - 1)
                else:
                    row_heights = [answer_row_height] * rows
            else:
                rows = 2
                cols = 2
                col_width = 225
                st.write(f"De kolombreedte voor Type 2 is altijd hetzelfde: {col_width} pixels")
                heading_lines = int(st.number_input("Hoeveel regels zijn nodig voor de kop van de tabel?", min_value=1, value=1, step=1, key="heading_rows_type2"))
                longest_rows = int(st.number_input("Hoeveel regels zijn nodig voor het langste antwoord?", min_value=1, value=1, step=1, key="longest_rows_type2"))
                answers_per_box = int(st.number_input("Hoeveel sleepopties moeten er in 1 sleepvak kunnen?", min_value=1, value=1, step=1, key="answers_per_box"))
                row1_height = int(heading_lines * 18)
                row2_height = int(longest_rows * 20 * answers_per_box)
                row_heights = [row1_height, row2_height]

        table = TableImage(rows=rows, cols=cols, row_height=row_heights, col_width=col_width, font_size=11, line_width=1, wrap_width=max_chars_per_line)
        st.subheader("Vul de benodigde tekst per cel van de tabel in")
        if table_type.startswith("Type 2"):
            bold_choice = st.checkbox("Vink dit aan als de tekst dikgedrukt moet zijn", key="table_bold_all")
        else:
            bold_choice = False

        for r in range(rows):
            cols_inputs = st.columns(cols)
            for c in range(cols):
                text_key = f"text_{r}_{c}"
                with cols_inputs[c]:
                    text = st.text_input(f"Cell {r+1},{c+1}", key=text_key)
                    if table_type.startswith("Type 1"):
                        bold_cell = st.checkbox(f"maak tekst dikgedrukt", key=f"bold_{r}_{c}")
                    else:
                        bold_cell = bold_choice
                table.set_text(r, c, text, bold=bold_cell)

    with right:
        st.subheader("Preview & Downloaden (Tabel)")
        try:
            img = table.draw()
            prefix = (safe_filename(vakcode) + "_") if (vakcode and str(vakcode).strip()) else ""
            fname_safe = prefix + (safe_filename(f"{tekst_titel}_{tekst_itemnummer}_tabel.png") or "table.png")
            st.image(img, caption=f"Gegenereerde Tabel — {fname_safe}", use_column_width=True)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            byte_im = buf.getvalue()
            st.download_button(label="Download het plaatje", data=byte_im, file_name=fname_safe, mime="image/png", key="download_table")
        except Exception as e:
            st.error(f"Kon tabel niet genereren: {e}")


# ----------------- SLEEPOPTIES MAKEN (full functionality) -----------------
elif mode == "Sleepopties Maken":
    with left:
        vakcode = st.text_input("Vakcode (optioneel)", value="", key="sleep_vakcode")
        st.header("Sleepopties genereren")
        tekst_titel = st.text_input("Titel van de tekst", value="title", key="sleep_titel")
        tekst_itemnummer = st.text_input("Item nummer (in selectie)", value="1", key="sleep_itemnr")
        num_columns = st.number_input("Hoeveel kolommen heeft de tabel?", min_value=1, value=2, step=1, key="sleep_num_columns")
        max_chars_per_line_sleep = st.number_input("Kies het aantal karakters per regel", min_value=10, value=33, key="sleep_wrap")
        st.subheader("Sleepopties (antwoordopties)")
        st.write("Laat sleepopties die je niet nodig hebt leeg.")
        letters = ["A", "B", "C", "D", "E", "F", "G", "H"]
        options = [""] * 8
        opt_cols = st.columns(2)
        for idx, L in enumerate(letters):
            with opt_cols[idx % 2]:
                options[idx] = st.text_area(f"Sleepoptie {L}", value="", height=80, key=f"opt_{L}")

    with right:
        st.subheader("Gegenereerde plaatjes")
        base_dir = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
        heights = []
        line_counts = []
        for text in options:
            if text and text.strip() != "":
                wr = wrap_text(text.strip(), max_chars_per_line_sleep)
                lc = wr["line_count"]
                if lc == 1:
                    h = 18
                else:
                    h = max(10, (lc * 15) + 5)
                heights.append(h)
                line_counts.append(lc)
        if not heights:
            st.warning("Vul op z'n minst 1 sleepoptie in.")
        else:
            max_height = max(heights)
            max_lines = max(line_counts) if line_counts else 0
            extra_pixels = max(0, max_lines - 1)
            canvas_height = max_height + extra_pixels
            generated_images = []
            prefix = (safe_filename(vakcode) + "_") if (vakcode and str(vakcode).strip()) else ""
            for idx, text in enumerate(options, start=1):
                if not text or text.strip() == "":
                    continue
                letter = chr(64 + idx)
                img, _ = create_sleepoptie_single_image(
                    text,
                    tekst_titel=tekst_titel,
                    tekst_itemnummer=f"{tekst_itemnummer}_{letter}",
                    canvas_height=canvas_height,
                    max_chars_per_line=max_chars_per_line_sleep,
                    font_size=11,
                    base_dir=base_dir,
                    num_columns=num_columns,
                )
                if img is not None:
                    filename = prefix + f"{safe_filename(tekst_titel)}_{tekst_itemnummer}_{letter}.png"
                    generated_images.append((filename, img))
            if generated_images:
                st.success(f"Gegenereerde {len(generated_images)} plaatjes:")
                for i, (filename, img) in enumerate(generated_images, start=1):
                    st.image(img, caption=filename, use_column_width=False)
                    buf = io.BytesIO()
                    img.save(buf, format="PNG")
                    buf.seek(0)
                    st.download_button(label=f"Download {filename}", data=buf.getvalue(), file_name=safe_filename(filename) or filename, mime="image/png", key=f"download_{filename}_{i}")
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w", compression=zipfile.ZIP_DEFLATED) as zip_file:
                    for filename, img in generated_images:
                        img_bytes = io.BytesIO()
                        img.save(img_bytes, format="PNG")
                        img_bytes.seek(0)
                        zip_file.writestr(safe_filename(filename) or filename, img_bytes.getvalue())
                zip_buffer.seek(0)
                zip_name = prefix + f"{safe_filename(tekst_titel)}_{tekst_itemnummer}_alle_sleepopties.zip"
                st.download_button(label="Download alle plaatjes in 1 keer (.zip)", data=zip_buffer.getvalue(), file_name=safe_filename(zip_name) or "sleepopties.zip", mime="application/zip", key="download_all_zip")


# ----------------- FORMS FEEDBACKTOOL (simplified, no preview) -----------------
elif mode == "Forms Feedbacktool":
    # heavy imports only here
    try:
        import pandas as pd
        from docx import Document
        from docx.shared import Pt
        from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
        from docx.oxml import OxmlElement
        from docx.oxml.ns import qn
    except Exception:
        st.error("Deze feature vereist extra packages: pandas en python-docx. Installeer met: pip install pandas python-docx openpyxl")
        st.stop()

    # helpers for Forms tool
    def reformat_data(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        if "Geef uw naam" in df.columns:
            df = df.rename(columns={"Geef uw naam": "VC lid"})
        if "VC lid" not in df.columns:
            df["VC lid"] = ""
        for c in df.select_dtypes(include=["object", "string"]).columns:
            df[c] = df[c].fillna("geen opmerkingen").astype(str)
        df = df.fillna("geen opmerkingen")
        return df

    def sanitize_filename(name: str) -> str:
        if name is None:
            return ""
        return re.sub(r"[^0-9A-Za-z._-]", "_", str(name))

    def extract_column_name(col_name: str) -> str:
        if not isinstance(col_name, str):
            col_name = str(col_name)
        parts = col_name.split()
        for i in range(len(parts) - 1, -1, -1):
            if re.search(r"[A-Z]", parts[i]):
                return " ".join(parts[i:])
        return col_name

    # ensure table has gridlines (set tblBorders)
    def ensure_table_grid(table):
        tbl = table._tbl
        tblPr = tbl.get_or_add_tblPr()
        borders = OxmlElement("w:tblBorders")
        for border_name in ("top", "left", "bottom", "right", "insideH", "insideV"):
            node = OxmlElement(f"w:{border_name}")
            node.set(qn("w:val"), "single")
            node.set(qn("w:sz"), "4")
            node.set(qn("w:space"), "0")
            node.set(qn("w:color"), "000000")
            borders.append(node)
        # remove existing and append
        try:
            existing = tblPr.xpath("w:tblBorders")
            for e in existing:
                tblPr.remove(e)
        except Exception:
            pass
        tblPr.append(borders)

    st.header("Forms Feedbacktool — Word export")
    st.write("Upload een Excel (.xlsx). Kies alleen lettertype en lettergrootte. De preview is verwijderd; Word-bestanden krijgen gridlines, kop en datum zijn vetgedrukt.")

    # minimal user input
    font_family = st.selectbox("Lettertype voor Word", ["Calibri", "Times New Roman", "Arial"], index=0)
    font_size_pt = st.number_input("Lettergrootte (pt) voor Word", min_value=8, max_value=18, value=11, step=1)

    uploaded = st.file_uploader("Upload Excel file (.xlsx)", type=["xlsx"], accept_multiple_files=False)
    process = st.button("Generate Word Documents")
    status = st.empty()

    if process:
        if uploaded is None:
            st.warning("Upload eerst een .xlsx bestand.")
        else:
            try:
                df_raw = pd.read_excel(uploaded, engine="openpyxl")
                df = reformat_data(df_raw)
                cg_columns = [c for c in df.columns if re.match(r"^CG\d+", str(c))]
                if not cg_columns:
                    status.error("Geen CG-columns gevonden (kolommen die beginnen met 'CG' + cijfers).")
                else:
                    prefixes = sorted({re.match(r"^(CG\d+)", str(c)).group(1) for c in cg_columns})
                    generated = []
                    today_str = date.today().isoformat()

                    for prefix in prefixes:
                        doc = Document()
                        cols_for_prefix = [c for c in cg_columns if str(c).startswith(prefix)]
                        for cg_col in cols_for_prefix:
                            if cg_col not in df.columns:
                                continue
                            current_df = df[["VC lid", cg_col]].copy()
                            simple_name = extract_column_name(str(cg_col))
                            current_df.columns = ["VC lid", simple_name]

                            # Heading bold
                            p_head = doc.add_paragraph()
                            run_h = p_head.add_run(str(cg_col))
                            run_h.font.bold = True
                            run_h.font.size = Pt(font_size_pt + 1)
                            try:
                                run_h.font.name = font_family
                                run_h._element.rPr.rFonts.set(qn("w:eastAsia"), font_family)
                            except Exception:
                                pass

                            # Date bold
                            p_date = doc.add_paragraph()
                            run_d = p_date.add_run(f"VC {today_str}")
                            run_d.font.bold = True
                            run_d.font.size = Pt(font_size_pt)
                            try:
                                run_d.font.name = font_family
                                run_d._element.rPr.rFonts.set(qn("w:eastAsia"), font_family)
                            except Exception:
                                pass

                            # Create table with gridlines
                            table = doc.add_table(rows=1, cols=2)
                            ensure_table_grid(table)

                            # Header cells: set text, then clear and set formatted run
                            hdr_cells = table.rows[0].cells
                            hdr_cells[0].text = "VC lid"
                            hdr_cells[1].text = simple_name
                            for cell in hdr_cells:
                                # clear paragraph text and add formatted run
                                para = cell.paragraphs[0]
                                para.text = ""
                                run = para.add_run(cell.text if cell.text else "")
                                run.font.bold = True
                                run.font.size = Pt(font_size_pt)
                                try:
                                    run.font.name = font_family
                                    run._element.rPr.rFonts.set(qn("w:eastAsia"), font_family)
                                except Exception:
                                    pass

                            # Fill rows
                            for _, row in current_df.iterrows():
                                r_cells = table.add_row().cells
                                # left
                                left_para = r_cells[0].paragraphs[0]
                                left_para.text = ""
                                left_run = left_para.add_run(str(row["VC lid"]))
                                left_run.font.size = Pt(font_size_pt)
                                try:
                                    left_run.font.name = font_family
                                    left_run._element.rPr.rFonts.set(qn("w:eastAsia"), font_family)
                                except Exception:
                                    pass
                                # right
                                right_para = r_cells[1].paragraphs[0]
                                right_para.text = ""
                                right_run = right_para.add_run(str(row[simple_name]))
                                right_run.font.size = Pt(font_size_pt)
                                try:
                                    right_run.font.name = font_family
                                    right_run._element.rPr.rFonts.set(qn("w:eastAsia"), font_family)
                                except Exception:
                                    pass

                            doc.add_page_break()

                        sanitized_prefix = safe_filename(prefix)
                        filename = f"{today_str}_FB_Gebundeld_{sanitized_prefix}.docx"
                        bio = io.BytesIO()
                        doc.save(bio)
                        bio.seek(0)
                        generated.append((filename, bio.read()))

                    if not generated:
                        status.warning("Geen documenten gegenereerd.")
                    else:
                        status.success(f"✅ {len(generated)} Word-document(en) gegenereerd.")
                        for idx, (fname, data_bytes) in enumerate(generated, start=1):
                            st.download_button(label=fname, data=data_bytes, file_name=safe_filename(fname) or fname, mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", key=f"fb_download_{idx}")
                        # ZIP all
                        zip_buf = io.BytesIO()
                        with zipfile.ZipFile(zip_buf, "w", compression=zipfile.ZIP_DEFLATED) as z:
                            for fname, data_bytes in generated:
                                z.writestr(safe_filename(fname) or fname, data_bytes)
                        zip_buf.seek(0)
                        st.download_button(label="Download alle documenten als ZIP", data=zip_buf.getvalue(), file_name=f"FB_Gebundeld_{today_str}.zip", mime="application/zip", key="fb_zip_all")
            except Exception as e:
                status.error(f"Fout bij verwerken: {e}")
