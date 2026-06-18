import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import textwrap
import io
import os
import math
import zipfile
import re
from datetime import date

# Ensure dark theme config if possible
try:
    cfg_dir = os.path.join(os.getcwd(), ".streamlit")
    os.makedirs(cfg_dir, exist_ok=True)
    cfg_path = os.path.join(cfg_dir, "config.toml")
    cfg_content = '[theme]\nbase = "dark"\n'
    with open(cfg_path, "w", encoding="utf-8") as f:
        f.write(cfg_content)
except Exception:
    pass

# helper to create filenames
def safe_filename(s):
    if s is None:
        return ""
    s = str(s).strip()
    s = s.replace(" ", "_")
    s = re.sub(r"[^A-Za-z0-9._-]", "", s)
    return s

# TableImage class and helpers (unchanged from your original app)
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

    def save(self, filename):
        img = self.draw()
        ext = os.path.splitext(filename)[1].lower()
        fmt = "PNG" if ext == ".png" else "JPEG"
        img.save(filename, fmt)

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
    # Adjusted: if exactly 1 line, make height 18 px. Otherwise keep previous formula.
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

# Streamlit UI and CSS (same as before)
st.set_page_config(page_title="Sleepoptie en Tabel Generator", layout="wide")
manual_filename = "Nieuwe Itemtypes Handleiding Invoer TOM.docx"
base_dir = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()

css_force_dark = """
<script>
  // Force the data-theme attribute to dark for components that look at it
  try { document.documentElement.setAttribute('data-theme', 'dark'); } catch(e){}
</script>
<style>
  /* Page background & main text */
  html, body, [data-testid="stAppViewContainer"], .stApp, .reportview-container {
    background: #0b0b0b !important;
    color: #eaeaea !important;
  }
  /* Main content container */
  .block-container, .css-1outpf7, .css-1kyxreq {
    background: rgba(0,0,0,0.85) !important;
    color: #ffffff !important;
  }
  /* Headings and labels */
  h1, h2, h3, h4, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, label {
    color: #ff7ab6 !important;
  }
  /* Inputs / textareas / selectboxes / widgets */
  input, textarea, select, .stTextInput>div>input, .stTextArea>div>textarea,
  .stSelectbox>div, .stMultiSelect>div, .stRadio, .stSlider, .stCheckbox {
    background: rgba(255,255,255,0.03) !important;
    color: #ffffff !important;
    border: 1px solid rgba(255,122,182,0.12) !important;
  }
  /* Buttons */
  .stButton>button, .stDownloadButton>button, button {
    background: linear-gradient(90deg,#ff5fa6,#ff80c8) !important;
    color: #ffffff !important;
    border: none !important;
  }
  /* Tables / dataframes */
  table, thead, tbody, tr, td, th {
    background: transparent !important;
    color: #eaeaea !important;
    border-color: rgba(255,255,255,0.06) !important;
  }
  /* Overrule inline theming via data-theme attributes */
  html[data-theme="light"], [data-theme="light"] * {
    background: none !important;
    color: inherit !important;
  }
  /* Ensure scrollbar looks dark */
  ::-webkit-scrollbar { width: 10px; height: 10px; }
  ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.06); border-radius: 10px; }
</style>
"""
st.markdown(css_force_dark, unsafe_allow_html=True)
st.markdown(
    """
    <style>
      /* Page background */
      html, body, [data-testid="stAppViewContainer"] {
        background: #000000 !important;
        color: #ffffff !important;
      }
      /* Main content container */
      .block-container {
        border-radius: 16px;
        padding: 32px;
        background: rgba(0,0,0,0.85);
        box-shadow: 0 8px 30px rgba(0,0,0,0.6);
        color: #ffffff;
      }
      /* Headings and labels */
      h1, h2, h3, h4, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #ff7ab6;
        font-family: 'Pacifico', 'Poppins', sans-serif;
      }
      label, .css-1q8dd3e.egzxvld1 {
        color: #ff7ab6;
        font-family: 'Poppins', sans-serif;
      }
      /* Inputs / textareas */
      input[type="text"], textarea, .stTextInput>div>input, .stTextArea>div>textarea {
        border-radius: 10px;
        border: 1px solid rgba(255,122,182,0.18);
        background: rgba(255,255,255,0.03);
        color: #ffffff;
        padding: 8px;
        box-shadow: inset 0 2px 8px rgba(255,122,182,0.03);
        font-family: 'Poppins', sans-serif;
      }
      textarea { min-height: 80px; color: #fff; }
      /* Buttons / download buttons */
      .stButton>button, .stDownloadButton>button, button {
        background: linear-gradient(90deg,#ff5fa6,#ff80c8);
        color: #ffffff;
        border: none;
        padding: 8px 14px;
        border-radius: 12px;
        box-shadow: 0 6px 18px rgba(255,105,180,0.14);
        font-weight:600;
        font-family: 'Poppins', sans-serif;
      }
      .stButton>button:hover, .stDownloadButton>button:hover, button:hover {
        transform: translateY(-1px);
        opacity:0.95;
      }
      /* Alerts */
      .stInfo, .stWarning, .stSuccess, .stError {
        border-radius: 12px;
        padding: 12px;
        font-family: 'Poppins', sans-serif;
        color: #fff;
        background: rgba(255,255,255,0.03);
      }
      /* Small tweaks for contrast on widgets */
      .stSelectbox>div, .stMultiSelect>div { border-radius: 10px; }
      .stSlider, .stRadio, .stCheckbox { color: #fff; }
      .stMarkdown { color: #fff; }
      /* Hide default footer */
      footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)
st.info("Laatste Update: 2026-05-27 - Grootte van sleepopties bij 1 regel gefixt, dank Kirsten :-)")

# Manual download
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

mode = st.selectbox(
    "Kies functie:",
    ["Tabel Maken", "Sleepopties Maken", "Forms Feedbacktool"],
    index=0,
)

# Two-column layout: left for inputs, right for preview/downloads
left, right = st.columns([1, 1.2])

# ---------- Tables mode ----------
if mode == "Tabel Maken":
    with left:
        # Voeg hier Vakcode toe
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
            help="Na hoeveel karakters moet er een enter komen? Verlaag de waarde als je in het plaatje ziet dat er eerder een enter moet komen.",
            key="table_wrap_width",
        )
        with st.expander("Instellingen voor de afmetingen van de tabel", expanded=True):
            if table_type.startswith("Type 1"):
                rows = int(
                    st.number_input("Hoeveel rijen heeft de tabel?", min_value=1, value=2, step=1, key="t1_rows")
                )
                cols = int(
                    st.number_input("Hoeveel kolommen heeft de tabel?", min_value=1, value=2, step=1, key="t1_cols")
                )
                col_width = int(450 // cols)
                st.write(f"Met deze instellingen wordt de kolombreedte {col_width} pixels (450 // {cols})")
                heading_lines = 0
                has_heading_label = st.checkbox(
                    "Heeft de kop van de tabel een label?",
                    value=False,
                    key="t1_heading_has_label",
                )
                if has_heading_label:
                    heading_lines = int(
                        st.number_input(
                            "Hoeveel regels zijn nodig voor de kop van de tabel?",
                            min_value=1,
                            value=1,
                            step=1,
                            key="heading_lines_type1",
                            help="Deze optie is relevant als de kop een label heeft. Omdat er meer kolommen kunnen zijn, is er minder ruimte voor de tekst. Daarom kan het zijn dat je meerdere regels nodig hebt. Kijk even goed wat er gebeurt als je hier wat aanpast en wat er gebeurt als je de waarde van 'Kies het aantal karakters per regel' aanpast",
                        )
                    )
                    st.write(f"De eerste rij van de tabel (de kop van de tabel) wordt {heading_lines * 18} pixels ( {heading_lines} × 18 )")
                longest_rows = int(
                    st.number_input(
                        "Hoeveel regels zijn nodig voor het langste antwoord?",
                        min_value=1,
                        value=1,
                        step=1,
                        key="t1_longest_rows",
                        help="Kijk bij de afbeeldingen die je gemaakt hebt voor de sleepopties hoeveel regels tekst het langste antwoord heeft.",
                    )
                )
                # Als het langste antwoord 1 regel is, wil je een iets grotere rij: 22 px.
                if longest_rows == 1:
                    answer_row_height = 22
                else:
                    answer_row_height = int(longest_rows * 20)
                multiplier = 22 if longest_rows == 1 else 20
                st.write(f"De rijen waar de antwoorden in gesleept moeten worden worden {answer_row_height} pixels ( {longest_rows} × {multiplier} )")
                if heading_lines > 0:
                    first_row_height = heading_lines * 18
                    if rows == 1:
                        row_heights = [first_row_height]
                    else:
                        row_heights = [first_row_height] + [answer_row_height] * (rows - 1)
                else:
                    row_heights = [answer_row_height] * rows
            else:
                # Type 2 defaults
                rows = 2
                cols = 2
                col_width = 225
                st.write(f"De kolombreedte voor Type 2 is altijd hetzelfde: {col_width} pixels")
                heading_lines = int(
                    st.number_input(
                        "Hoeveel regels zijn nodig voor de kop van de tabel?",
                        min_value=1,
                        value=1,
                        step=1,
                        key="heading_rows_type2",
                        help="Kijk even goed wat er gebeurt als je hier wat aanpast en wat er gebeurt als je de waarde van 'Kies het aantal karakters per regel' aanpast",
                    )
                )
                st.write(f"De eerste rij van de tabel (de kop van de tabel) wordt {heading_lines * 18} pixels ( {heading_lines} × 18 )")
                longest_rows = int(
                    st.number_input(
                        "Hoeveel regels zijn nodig voor het langste antwoord?",
                        min_value=1,
                        value=1,
                        step=1,
                        key="longest_rows_type2",
                        help="Kijk bij de afbeeldingen die je gemaakt hebt voor de sleepopties hoeveel regels tekst het langste antwoord heeft.",
                    )
                )
                answers_per_box = int(
                    st.number_input(
                        "Hoeveel sleepopties moeten er in 1 sleepvak kunnen?",
                        min_value=1,
                        value=1,
                        step=1,
                        key="answers_per_box",
                        help="Dit is meestal het aantal sleepopties - 1, tenzij er specifiek in de vraag wordt aangegeven dat er X aantal in moet.",
                    )
                )
                row1_height = int(heading_lines * 18)
                # Use real multiplication for the second row
                row2_height = int(longest_rows * 20 * answers_per_box)
                row_heights = [row1_height, row2_height]
                st.write(f"De rij waar de antwoorden in gesleept moeten worden wordt {row2_height} pixels ( {longest_rows} × 20 × {answers_per_box} )")
        # Create TableImage instance
        table = TableImage(
            rows=rows,
            cols=cols,
            row_height=row_heights,
            col_width=col_width,
            font_size=11,
            line_width=1,
            wrap_width=max_chars_per_line,
        )
        st.subheader("Vul de benodigde tekst per cel van de tabel in, de cellen staan op dezelfde volgorde als de tabel (cel 1.1 is linksboven etc.).")
        if table_type.startswith("Type 2"):
            bold_choice = st.checkbox("Vink dit aan als de tekst dikgedrukt moet zijn", key="table_bold_all")
        else:
            bold_choice = False
        # Arrange cell inputs in a grid using columns to reduce scrolling
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
        st.subheader("Preview & Downloaden")
        preview_placeholder = st.empty()
        try:
            img = table.draw()
            prefix = (safe_filename(vakcode) + "_") if (vakcode and str(vakcode).strip()) else ""
            fname_safe = prefix + (safe_filename(f"{tekst_titel}_{tekst_itemnummer}_tabel.png") or "table.png")
            preview_placeholder.image(img, caption=f"Gegenereerde Tabel — {fname_safe}", use_column_width=True)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            byte_im = buf.getvalue()
            st.download_button(
                label="Download het plaatje",
                data=byte_im,
                file_name=fname_safe,
                mime="image/png",
                key="download_table"
            )
        except Exception as e:
            st.error(f"Kon tabel niet genereren: {e}")

# ---------- Sleepopties mode ----------
elif mode == "Sleepopties Maken":
    with left:
        vakcode = st.text_input("Vakcode (optioneel)", value="", key="sleep_vakcode")
        st.header("Sleepopties genereren")
        with st.container():
            tekst_titel = st.text_input("Titel van de tekst", value="title", key="sleep_titel")
            tekst_itemnummer = st.text_input("Item nummer (in selectie)", value="1", key="sleep_itemnr")
            num_columns = st.number_input(
                "Hoeveel kolommen heeft de tabel?",
                min_value=1,
                value=2,
                step=1,
                key="sleep_num_columns",
                help="Dit is nodig om de grootte van de plaatjes goed te krijgen.",
            )
            max_chars_per_line_sleep = st.number_input("Kies het aantal karakters per regel", min_value=10, value=33, key="sleep_wrap")
        st.subheader("Sleepopties (antwoordopties)")
        st.write("Laat sleepopties die je niet nodig hebt leeg.")
        # Display the 8 text areas in two columns to save vertical space
        letters = ["A", "B", "C", "D", "E", "F", "G", "H"]
        options = [""] * 8
        # two-column layout for options
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
                # Adjusted: if exactly 1 line, use 18 px, else keep previous formula
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
                img, _= create_sleepoptie_single_image(
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
                    st.download_button(
                        label=f"Download {filename}",
                        data=buf.getvalue(),
                        file_name=safe_filename(filename) or filename,
                        mime="image/png",
                        key=f"download_{filename}_{i}"
                    )
                # create ZIP in RAM and download
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w", compression=zipfile.ZIP_DEFLATED) as zip_file:
                    for filename, img in generated_images:
                        img_bytes = io.BytesIO()
                        img.save(img_bytes, format="PNG")
                        img_bytes.seek(0)
                        zip_file.writestr(safe_filename(filename) or filename, img_bytes.getvalue())
                zip_buffer.seek(0)
                zip_name = prefix + f"{safe_filename(tekst_titel)}_{tekst_itemnummer}_alle_sleepopties.zip"
                st.download_button(
                    label="Download alle plaatjes in 1 keer (.zip)",
                    data=zip_buffer.getvalue(),
                    file_name=safe_filename(zip_name) or "sleepopties.zip",
                    mime="application/zip",
                    key="download_all_zip"
                )

# ---------- Forms Feedbacktool mode (nieuw met preview instellingen) ----------
elif mode == "Forms Feedbacktool":
    # Import heavy deps only when needed
    try:
        import pandas as pd  # reading excel and dataframe ops
        from docx import Document  # create Word docs
        from docx.shared import Inches, Pt
        from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
        from docx.oxml import OxmlElement
        from docx.oxml.ns import qn
    except Exception:
        st.error("Deze feature vereist extra packages: pandas en python-docx. Installeer met: pip install pandas python-docx openpyxl")
        st.stop()

    # Helpers (translated from your R functions + extras)
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

    # set background color for a cell (docx XML)
    def set_cell_bg(cell, color_hex: str):
        # color_hex like "#F2F2F2" or "F2F2F2"
        c = color_hex.lstrip("#")
        tc = cell._tc
        tcPr = tc.get_or_add_tcPr()
        shd = OxmlElement("w:shd")
        shd.set(qn("w:fill"), c)
        tcPr.append(shd)

    st.header("Forms Feedbacktool — Word export van Forms-feedback")
    st.write("Upload een Excel-bestand (.xlsx) uit Forms. Kies hieronder hoe de tabellen eruit moeten zien (preview) en klik daarna op 'Generate Word Documents'.")

    # Appearance controls
    with st.expander("Tabel uiterlijk (preview & toepassen op Word)", expanded=True):
        font_family = st.selectbox("Lettertype", ["Times New Roman", "Arial", "Calibri"], index=0)
        font_size = st.number_input("Lettergrootte (pt)", min_value=8, max_value=20, value=11, step=1)
        header_bold = st.checkbox("Kop vetgedrukt", value=True)
        header_bg = st.color_picker("Kleur kop achtergrond (hex)", value="#F2F2F2")
        table_style_choice = st.selectbox(
            "Tabelstijl (Word, als beschikbaar)",
            ["Table Grid", "Light Shading", "Light List Accent 1", "None"],
            index=0,
            help="Als de geselecteerde stijl in python-docx document.styles beschikbaar is, wordt die gebruikt; anders default."
        )
        col_width_mode = st.selectbox("Kolombreedte", ["Auto", "Custom percentage"], index=0)
        if col_width_mode == "Custom percentage":
            first_col_pct = st.slider("Breedte eerste kolom (VC lid) (%)", min_value=10, max_value=90, value=30)
        else:
            first_col_pct = None
        second_col_align = st.selectbox("Uitlijning tweede kolom (inhoud)", ["Left", "Center", "Right"], index=0)

    uploaded = st.file_uploader("Upload Excel file (.xlsx)", type=["xlsx"], accept_multiple_files=False)
    # Allow user to preview a specific CG-column before generating all docs
    preview_section = st.expander("Preview een specifieke CG-tabel (HTML preview)", expanded=True)
    with preview_section:
        st.write("Na upload kies je een CG-kolom hieronder en klik op 'Toon preview' om te zien hoe de tabel in de Word-docs eruit zal zien.")
        cg_choice = st.selectbox("Kies CG-kolom voor preview (na upload)", options=["(upload eerst een bestand)"])
        show_preview = st.button("Toon preview")

    process = st.button("Generate Word Documents")

    download_area = st.container()
    status = st.empty()

    # Handle dynamic list of CG columns for preview dropdown
    if uploaded is not None:
        try:
            df_uploaded = pd.read_excel(uploaded, engine="openpyxl")
            df_uploaded = reformat_data(df_uploaded)
            cg_columns_all = [c for c in df_uploaded.columns if re.match(r"^CG\d+", str(c))]
            cg_options = ["(kies)"] + cg_columns_all
        except Exception:
            cg_options = ["(geen)"]
    else:
        cg_options = ["(upload eerst een bestand)"]
    # update cg_choice selectbox (workaround to replace previously created widget)
    # Note: We can't directly reassign the original selectbox; so we just display another selectbox if uploaded.
    if uploaded is not None:
        with preview_section:
            cg_choice = st.selectbox("Kies CG-kolom voor preview (na upload)", options=cg_options, index=0, key="cg_preview_select")

    # Show HTML preview when requested
    if uploaded is not None and show_preview:
        if cg_choice in (None, "(kies)", "(geen)", "(upload eerst een bestand)"):
            st.warning("Kies eerst een geldige CG-kolom voor preview.")
        else:
            try:
                df = df_uploaded.copy()
                if cg_choice not in df.columns:
                    st.error("Gekozen kolom niet gevonden.")
                else:
                    # Build a small dataframe for preview (first N rows)
                    current_df = df[["VC lid", cg_choice]].copy()
                    simple_name = extract_column_name(str(cg_choice))
                    current_df.columns = ["VC lid", simple_name]
                    preview_df = current_df.head(20).fillna("geen opmerkingen")

                    # Build CSS according to user choices
                    css = f"""
                        <style>
                        table.custom {{ border-collapse: collapse; width: 100%; font-family: '{font_family}', serif; font-size: {font_size}pt; }}
                        table.custom th, table.custom td {{ padding: 8px 12px; vertical-align: top; }}
                        table.custom th {{ font-weight: {'bold' if header_bold else 'normal'}; background: {header_bg}; text-align: left; }}
                        table.custom td {{ text-align: {'left' if second_col_align=='Left' else 'center' if second_col_align=='Center' else 'right'}; }}
                        </style>
                    """
                    # Build HTML table from preview_df with optional custom column width
                    if first_col_pct:
                        first_w = first_col_pct
                        second_w = 100 - first_col_pct
                        col_style = f"<colgroup><col style='width:{first_w}%' /><col style='width:{second_w}%' /></colgroup>"
                    else:
                        col_style = ""
                    html_table = preview_df.to_html(index=False, classes="custom", table_id="preview_table", escape=False)
                    # Inject colgroup and CSS (replace <table ...> with <table> containing colgroup)
                    html_table = html_table.replace("<table border=\"1\" class=\"dataframe custom\" id=\"preview_table\">",
                                                    f"<table class=\"custom\" id=\"preview_table\">")
                    # Insert colgroup after opening table tag
                    html_table = html_table.replace("<table class=\"custom\" id=\"preview_table\">", f"<table class=\"custom\" id=\"preview_table\">{col_style}")
                    st.markdown(css + html_table, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Fout bij preview genereren: {e}")

    # When process pressed -> create Word docs using appearance settings
    if process:
        if uploaded is None:
            st.warning("Upload eerst een .xlsx bestand.")
        else:
            try:
                df = pd.read_excel(uploaded, engine="openpyxl")
                df = reformat_data(df)
                cg_columns = [c for c in df.columns if re.match(r"^CG\d+", str(c))]
                if not cg_columns:
                    status.error("Geen CG-columns gevonden (kolommen die beginnen met 'CG' + cijfers).")
                else:
                    prefixes = sorted({re.match(r"^(CG\d+)", str(c)).group(1) for c in cg_columns})
                    generated = []  # list of tuples (filename, bytes)
                    today_str = date.today().isoformat()

                    # total width to use for custom widths (in inches)
                    total_width_inch = 6.0

                    for prefix in prefixes:
                        doc = Document()
                        cols_for_prefix = [c for c in cg_columns if str(c).startswith(prefix)]
                        for cg_col in cols_for_prefix:
                            if cg_col not in df.columns:
                                continue
                            current_df = df[["VC lid", cg_col]].copy()
                            simple_name = extract_column_name(str(cg_col))
                            current_df.columns = ["VC lid", simple_name]
                            # Add heading & date
                            doc.add_paragraph(str(cg_col))
                            doc.add_paragraph(f"VC {today_str}")

                            # Create table
                            table = doc.add_table(rows=1, cols=2)
                            # Apply chosen table style if available
                            if table_style_choice and table_style_choice != "None":
                                try:
                                    # Only set if exists
                                    if table_style_choice in [s.name for s in doc.styles]:
                                        table.style = table_style_choice
                                    else:
                                        # try common fallback names: "Table Grid"
                                        if "Table Grid" in [s.name for s in doc.styles]:
                                            table.style = "Table Grid"
                                except Exception:
                                    pass

                            hdr_cells = table.rows[0].cells
                            hdr_cells[0].text = "VC lid"
                            hdr_cells[1].text = simple_name

                            # Header formatting
                            for i, cell in enumerate(hdr_cells):
                                # set background
                                try:
                                    set_cell_bg(cell, header_bg)
                                except Exception:
                                    pass
                                # format runs in header
                                for para in cell.paragraphs:
                                    for run in para.runs:
                                        run.font.name = font_family
                                        try:
                                            run._element.rPr.rFonts.set(qn('w:eastAsia'), font_family)
                                        except Exception:
                                            pass
                                        run.font.size = Pt(font_size)
                                        run.font.bold = True if header_bold else False
                                    # header alignment
                                    if second_col_align == "Left":
                                        para.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT
                                    elif second_col_align == "Center":
                                        para.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
                                    else:
                                        para.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT

                            # Fill rows
                            for _, row in current_df.iterrows():
                                r_cells = table.add_row().cells
                                # Left cell (VC lid)
                                left_para = r_cells[0].paragraphs[0]
                                left_para.text = str(row["VC lid"])
                                left_para.runs[0].font.name = font_family
                                try:
                                    left_para.runs[0]._element.rPr.rFonts.set(qn('w:eastAsia'), font_family)
                                except Exception:
                                    pass
                                left_para.runs[0].font.size = Pt(font_size)
                                # alignment default left
                                left_para.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT

                                # Right cell (answer)
                                right_para = r_cells[1].paragraphs[0]
                                right_para.text = str(row[simple_name])
                                right_para.runs[0].font.name = font_family
                                try:
                                    right_para.runs[0]._element.rPr.rFonts.set(qn('w:eastAsia'), font_family)
                                except Exception:
                                    pass
                                right_para.runs[0].font.size = Pt(font_size)
                                # alignment based on user setting
                                if second_col_align == "Left":
                                    right_para.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT
                                elif second_col_align == "Center":
                                    right_para.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
                                else:
                                    right_para.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT

                            # Apply custom column widths if requested
                            if first_col_pct:
                                try:
                                    first_inch = (first_col_pct / 100.0) * total_width_inch
                                    second_inch = total_width_inch - first_inch
                                    # set widths for columns
                                    for idx_col, w in enumerate([first_inch, second_inch]):
                                        for cell in table.columns[idx_col].cells:
                                            tcPr = cell._tc.get_or_add_tcPr()
                                            tcW = OxmlElement('w:tcW')
                                            tcW.set(qn('w:w'), str(int(w * 914400)))  # EMU units per inch
                                            tcW.set(qn('w:type'), 'dxa')
                                            # remove existing tcW if present
                                            try:
                                                existing = tcPr.xpath('w:tcW')
                                                for e in existing:
                                                    tcPr.remove(e)
                                            except Exception:
                                                pass
                                            tcPr.append(tcW)
                                except Exception:
                                    pass

                            doc.add_page_break()

                        sanitized_prefix = sanitize_filename(prefix)
                        filename = f"{today_str}_FB_Gebundeld_{sanitized_prefix}.docx"

                        # save doc to bytes
                        bio = io.BytesIO()
                        doc.save(bio)
                        bio.seek(0)
                        generated.append((filename, bio.read()))

                    if not generated:
                        status.warning("Geen documenten gegenereerd.")
                    else:
                        status.success(f"✅ {len(generated)} Word-document(en) gegenereerd.")
                        with download_area:
                            st.write("Downloads:")
                            for idx, (fname, data_bytes) in enumerate(generated, start=1):
                                st.download_button(
                                    label=fname,
                                    data=data_bytes,
                                    file_name=sanitize_filename(fname) or fname,
                                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                    key=f"fb_download_{idx}",
                                )

                            # ZIP all
                            zip_buf = io.BytesIO()
                            with zipfile.ZipFile(zip_buf, "w", compression=zipfile.ZIP_DEFLATED) as z:
                                for fname, data_bytes in generated:
                                    z.writestr(sanitize_filename(fname) or fname, data_bytes)
                            zip_buf.seek(0)
                            st.download_button(
                                label="Download alle documenten als ZIP",
                                data=zip_buf.getvalue(),
                                file_name=f"FB_Gebundeld_{today_str}.zip",
                                mime="application/zip",
                                key="fb_zip_all",
                            )
            except Exception as e:
                status.error(f"Fout bij verwerken: {e}")
