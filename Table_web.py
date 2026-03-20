import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import textwrap
import io
import os

# TableImage class remains unchanged from your code ...
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
        except NameError:
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
        # text
        for (r, c), text in self.cells.items():
            x = int(c * self.col_width)
            y = y_positions[r]
            bold = self.bold_cells.get((r, c), False)
            font_path = self.bold_font_path if bold else self.font_path
            try:
                font = ImageFont.truetype(font_path, self.font_size)
            except Exception:
                font = ImageFont.load_default()
            lines = textwrap.wrap(text, width=self.wrap_width) if text else []
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

# Wrap text function unchanged
def wrap_text(text, width):
    if text is None:
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

# Plaatje één sleepoptie
def create_sleepoptie_single_image(
    text,
    tekst_titel="title",
    tekst_itemnummer="1",
    max_chars_per_line=33,
    font_size=11,
    base_dir=None,
):
    if not text or str(text).strip() == "":
        return None, None

    # Wrap text
    wrap_result = wrap_text(text.strip(), max_chars_per_line)
    wrapped_text = wrap_result["wrapped_text"]
    line_count = wrap_result["line_count"]

    calculated_height = max(10, (line_count * 15) + 5)
    out_width = 210

    if base_dir is None:
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        except NameError:
            base_dir = os.getcwd()

    template_path = os.path.join(base_dir, "500x500_template.png")

    if os.path.exists(template_path):
        try:
            tpl = Image.open(template_path).convert("RGB")
            tpl = tpl.resize((out_width, calculated_height), resample=Image.LANCZOS)
            img = tpl
        except Exception:
            img = Image.new("RGB", (out_width, calculated_height), "white")
    else:
        img = Image.new("RGB", (out_width, calculated_height), "white")

    draw = ImageDraw.Draw(img)

    verdana_path = os.path.join(base_dir, "verdana.ttf")
    try:
        font = ImageFont.truetype(verdana_path, font_size)
    except Exception:
        font = ImageFont.load_default()

    margin_x = 5
    margin_y = 3
    draw.multiline_text((margin_x, margin_y), wrapped_text, fill="black", font=font, spacing=4)

    # Filename without var_name and without letter prefix, per your request
    filename = f"{tekst_titel}_{tekst_itemnummer}.png"

    return img, filename


# Streamlit app

st.title("Table & Sleepopties Generator (updated)")

mode = st.selectbox("Choose mode", ["Tables (original UI)", "Answer options (sleepopties)"])

if mode == "Tables (original UI)":
    # Keep your entire original Table UI code here unchanged
    st.header("Sleepvragen Maker - (2026-03-20 - Laatste Update)")
    table_type = st.selectbox(
        "Select table type",
        ("Type 1 (graphic gapmatch)", "Type 2 (graphic gapmatch categorize)"),
    )
    if table_type.startswith("Type 1"):
        rows = int(st.number_input("Number of rows", min_value=1, value=2, step=1))
        cols = int(st.number_input("Number of columns", min_value=1, value=2, step=1))
        longest_rows = int(
            st.number_input(
                "How many rows are required for the longest answer?",
                min_value=1,
                value=1,
                step=1,
            )
        )
        row_height_pixels = int(longest_rows * 18)
        st.write(f"Row height (pixels) will be: {row_height_pixels} px ( {longest_rows} × 18 )")
        col_width = int(st.number_input("Column width (pixels)", min_value=10, value=100, step=1))
        row_heights = row_height_pixels  
    else:
        rows = 2
        cols = 2
        col_width = int(st.number_input("Column width (pixels)", min_value=10, value=225, step=1))
        heading_rows = int(
            st.number_input(
                "How many rows are required for the headings?",
                min_value=1,
                value=1,
                step=1,
                key="heading_rows",
            )
        )
        st.write(f"Height of row 1 (pixels) will be: {heading_rows * 18} px ( {heading_rows} × 18 )")
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
        row1_height = int(heading_rows * 18)
        row2_height = int(longest_rows * 18 * answers_per_box)
        row_heights = [row1_height, row2_height]
        st.write(f"Height of row 2 (pixels) will be: {row2_height} px ( {longest_rows} × 18 × {answers_per_box} )")

    bold_choice = st.checkbox("Make all text bold?")

    table = TableImage(
        rows=rows,
        cols=cols,
        row_height=row_heights,
        col_width=col_width,
        font_size=11,
        line_width=1,
        wrap_width=29,
    )

    st.subheader("Enter cell text")
    for r in range(rows):
        for c in range(cols):
            text = st.text_input(f"Cell ({r+1},{c+1})", key=f"text_{r}_{c}")
            if table_type.startswith("Type 1"):
                bold_cell = st.checkbox(f"Bold? (Cell {r+1},{c+1})", key=f"bold_{r}_{c}")
            else:
                bold_cell = bold_choice
            table.set_text(r, c, text, bold=bold_cell)

    if st.button("Generate Table Image"):
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
        )

elif mode == "Answer options (sleepopties)":
    st.header("Generate Sleepoptie Images (A..H)")
    st.markdown("Enter text for sleepopties A through H. Leave empty entries blank to ignore them.")

    letters = ["A", "B", "C", "D", "E", "F", "G", "H"]
    options = []
    for L in letters:
        txt = st.text_area(f"Sleepoptie {L}", value="", height=80, key=f"opt_{L}")
        options.append(txt.strip())

    tekst_titel = st.text_input("Title (tekst_titel)", value="title")
    tekst_itemnummer = st.text_input("Item number (tekst_itemnummer)", value="1")

    max_chars_per_line = st.number_input("Max chars per line (wrap)", min_value=10, value=33)
    font_size = st.number_input("Font size (Verdana)", min_value=8, value=11)

    if st.button("Generate Sleepoptie Images"):
        base_dir = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
        generated_images = []
        for idx, text in enumerate(options, start=1):
            if not text:
                continue
            img, filename = create_sleepoptie_single_image(
                text,
                tekst_titel=tekst_titel,
                tekst_itemnummer=f"{tekst_itemnummer}_{idx}",
                max_chars_per_line=max_chars_per_line,
                font_size=font_size,
                base_dir=base_dir,
            )
            if img is not None:
                generated_images.append((filename, img))

        if not generated_images:
            st.warning("No non-empty sleepopties entered. Please enter at least one option.")
        else:
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
