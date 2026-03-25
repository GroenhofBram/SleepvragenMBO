import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import textwrap
import io
import os
import math
import zipfile
# TableImage
class TableImage:
    def **init**(
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
# sleepopties image creation
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
# Streamlit app
st.title("Table & Sleepopties Generator (aangepast)")
mode = st.selectbox("Choose mode", ["Tables (original UI)", "Answer options (sleepopties)"])
if mode == "Tables (original UI)":
    st.header("Sleepvragen Maker - (2026-03-20 - Laatste Update)")
    table_type = st.selectbox(
        "Select table type",
        ("Type 1 (graphic gapmatch)", "Type 2 (graphic gapmatch categorize)"),
    )
    max_chars_per_line = st.number_input(
        "Max chars per line (wrap) for table cells",
        min_value=5,
        max_value=200,
        value=33,
        step=1,
        help="How many characters before wrapping inside each table cell",
        key="table_wrap_width",
    )
    if table_type.startswith("Type 1"):
        rows = int(st.number_input("Number of rows", min_value=1, value=2, step=1, key="t1_rows"))
        cols = int(st.number_input("Number of columns", min_value=1, value=2, step=1, key="t1_cols"))
        col_width = int(450 // cols)
        st.write(f"Column width (pixels) is automatically set to: {col_width} px (450 // {cols})")
        heading_lines = 0
        if cols >= 3:
            heading_lines = int(
                st.number_input(
                    "How many rows are required for the headings?",
                    min_value=1,
                    value=1,
                    step=1,
                    key="heading_lines_type1",
                    help="Number of text lines (each ~18px) to reserve for the heading row",
                )
            )
            st.write(f"Heading row height will be: {heading_lines * 18} px ( {heading_lines} × 18 )")
        longest_rows = int(
            st.number_input(
                "How many rows are required for the longest answer?",
                min_value=1,
                value=1,
                step=1,
                key="t1_longest_rows",
            )
        )
        answer_row_height = int(longest_rows * 18)
        st.write(f"Answer row height (pixels) will be: {answer_row_height} px ( {longest_rows} × 18 )")
        if heading_lines > 0:
            first_row_height = heading_lines * 18
            if rows == 1:
                row_heights = [first_row_height]
            else:
                row_heights = [first_row_height] + [answer_row_height] * (rows - 1)
        else:
            row_heights = [answer_row_height] * rows
    else:
        # Type 2
        rows = 2
        cols = 2
        col_width = 225
        st.write(f"Column width (pixels) for Type 2 is fixed to: {col_width} px")
        heading_lines = int(
            st.number_input(
                "How many rows are required for the headings?",
                min_value=1,
                value=1,
                step=1,
                key="heading_rows_type2",
            )
        )
        st.write(f"Height of row 1 (pixels) will be: {heading_lines * 18} px ( {heading_lines} × 18 )")
        longest_rows = int(
            st.number_input(
                "How many rows are required for the longest answer?",
                min_value=1,
                value=1,
                step=1,
                key="longest_rows_type2",
            )
        )
        answers_per_box = int(
            st.number_input(
                "How many answers can fit in 1 box?",
                min_value=1,
                value=1,
                step=1,
                key="answers_per_box",
            )
        )
        row1_height = int(heading_lines * 18)
        row2_height = int(longest_rows _18_ answers_per_box)
        row_heights = [row1_height, row2_height]
        st.write(f"Height of row 2 (pixels) will be: {row2_height} px ( {longest_rows} × 18 × {answers_per_box} )")
    bold_choice = st.checkbox("Make all text bold?", key="table_bold_all")
    table = TableImage(
        rows=rows,
        cols=cols,
        row_height=row_heights,
        col_width=col_width,
        font_size=11,
        line_width=1,
        wrap_width=max_chars_per_line,
    )
    st.subheader("Enter cell text")
    for r in range(rows):
        for c in range(cols):
            text_key = f"text_{r}_{c}"
            text = st.text_input(f"Cell ({r+1},{c+1})", key=text_key)
            if table_type.startswith("Type 1"):
                bold_cell = st.checkbox(f"Bold? (Cell {r+1},{c+1})", key=f"bold_{r}_{c}")
            else:
                bold_cell = bold_choice
            table.set_text(r, c, text, bold=bold_cell)
    if st.button("Generate Table Image", key="gen_table"):
        img = table.draw()
        st.image(img, caption="Generated Table", use_column_width=True)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        byte_im = buf.getvalue()
        st.download_button(
            label="Download Table Image",
            data=byte_im,
            file_name="table.png",
            mime="image/png",
            key="download_table"
        )
elif mode == "Answer options (sleepopties)":
    st.header("Generate Sleepoptie Images (A..H)")
    st.markdown("Enter text for sleepopties A through H. Leave empty entries blank to ignore them.")
    tekst_titel = st.text_input("Title (tekst_titel)", value="title", key="sleep_titel")
    tekst_itemnummer = st.text_input("Item number (tekst_itemnummer)", value="1", key="sleep_itemnr")
    num_columns = st.number_input(
        "Number of columns",
        min_value=1,
        value=2,
        step=1,
        key="sleep_num_columns",
        help="Number of columns used to compute per-option image width",
    )
    max_chars_per_line_sleep = st.number_input("Max chars per line (wrap)", min_value=10, value=33, key="sleep_wrap")
    letters = ["A", "B", "C", "D", "E", "F", "G", "H"]
    options = []
    for L in letters:
        txt = st.text_area(f"Sleepoptie {L}", value="", height=80, key=f"opt_{L}")
        options.append(txt.strip())
    if st.button("Generate Sleepoptie Images", key="gen_sleep"):
        base_dir = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
        heights = []
        line_counts = []
        for text in options:
            if text and text.strip() != "":
                wr = wrap_text(text.strip(), max_chars_per_line_sleep)
                lc = wr["line_count"]
                h = max(10, (lc * 15) + 5)
                heights.append(h)
                line_counts.append(lc)
        if not heights:
            st.warning("No non-empty sleepopties entered. Please enter at least one option.")
        else:
            max_height = max(heights)
            max_lines = max(line_counts) if line_counts else 0
            extra_pixels = max(0, max_lines - 1)
            canvas_height = max_height + extra_pixels
            generated_images = []
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
                    filename = f"{tekst_titel}_{tekst_itemnummer}_{letter}.png"
                    generated_images.append((filename, img))
            st.success(f"Generated {len(generated_images)} images:")
            for i, (filename, img) in enumerate(generated_images, start=1):
                st.image(img, caption=filename, use_column_width=False)
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                buf.seek(0)
                st.download_button(
                    label=f"Download {filename}",
                    data=buf.getvalue(),
                    file_name=filename,
                    mime="image/png",
                    key=f"download_{i}"
                )

            # Create an in-memory ZIP of all generated images and offer a single download button
            if generated_images:
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
                    for filename, img in generated_images:
                        img_buf = io.BytesIO()
                        img.save(img_buf, format="PNG")
                        img_buf.seek(0)
                        zf.writestr(filename, img_buf.getvalue())
                zip_buffer.seek(0)
                zip_filename = f"{tekst_titel}_{tekst_itemnummer}_all.zip"
                st.download_button(
                    label="Download all as ZIP",
                    data=zip_buffer.getvalue(),
                    file_name=zip_filename,
                    mime="application/zip",
                    key="download_all_zip",
                )
