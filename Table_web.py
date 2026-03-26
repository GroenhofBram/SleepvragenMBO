import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import textwrap
import io
import os
import math
import zipfile

# TableImage 
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


# sleepopties 
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


# ---------- UI (layout-only changes) ----------
st.set_page_config(page_title="Sleepoptie en Tabel Generator", layout="wide")
st.info("Laatste Update: 2026-03-26")
st.caption("Links vul je informatie in, rechts zie je de plaatjes.")

# Keep the same mode selection but place it more prominently
mode = st.selectbox(
    "Select mode",
    ["Tabel Maken", "Sleepopties Maken"],
    index=0,
)

# Two-column layout: left for inputs, right for preview/downloads
left, right = st.columns([1, 1.2])

# ---------- Tables mode ----------
if mode == "Tabel Maken":
    with left:
        # Table type and general options grouped
        st.subheader("Algemene instellingen")
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
                    st.number_input("Hoeveel regels heeft de tabel?", min_value=1, value=2, step=1, key="t1_rows")
                )
                cols = int(
                    st.number_input("Hoeveel kolommen heeft de tabel?", min_value=1, value=2, step=1, key="t1_cols")
                )
                col_width = int(450 // cols)
                st.write(f"Met deze instellingen wordt de kolombreedte {col_width} pixels (450 // {cols})")

                heading_lines = 0
                if cols >= 3:
                    heading_lines = int(
                        st.number_input(
                            "Hoeveel regels zijn nodig voor de kop van de tabel?",
                            min_value=1,
                            value=1,
                            step=1,
                            key="heading_lines_type1",
                            help="Deze optie is alleen relevant bij 3 of meer kolommen. Omdat er meer kolommen zijn, is er minder ruimte voor de tekst. Daarom kan het zijn dat je meerdere regels nodig hebt. Kijk even goed wat er gebeurt als je hier wat aanpast en wat er gebeurt als je de waarde van 'Kies het aantal karakters per regel' aanpast",
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
                answer_row_height = int(longest_rows * 18)
                st.write(f"De rijen waar de antwoorden in gesleept moeten worden worden {answer_row_height} pixels ( {longest_rows} × 18 )")

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
                # fixed the multiplication expression so it runs correctly
                row2_height = int(longest_rows * 18 * answers_per_box)
                row_heights = [row1_height, row2_height]
                st.write(f"De rij waar de antwoorden in gesleept moeten worden wordt {row2_height} pixels ( {longest_rows} × 18 × {answers_per_box} )")
                bold_choice = st.checkbox("Vink dit aan als de tekst dikgedrukt moet zijn", key="table_bold_all")



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

        # Arrange cell inputs in a grid using columns to reduce scrolling
        for r in range(rows):
            cols_inputs = st.columns(cols)
            for c in range(cols):
                text_key = f"text_{r}_{c}"
                with cols_inputs[c]:
                    text = st.text_input(f"Cell {r+1},{c+1}", key=text_key)
                    if table_type.startswith("Type 1"):
                        bold_cell = st.checkbox(f"Bold? (Cell {r+1},{c+1})", key=f"bold_{r}_{c}")
                    else:
                        bold_cell = bold_choice
                table.set_text(r, c, text, bold=bold_cell)

        # Generate button on the left to make it easy to tweak inputs and produce preview
        gen_table = st.button("Generate Table Image", key="gen_table")

    with right:
        st.subheader("Preview & Downloaden")
        preview_placeholder = st.empty()
        if gen_table:
            img = table.draw()
            preview_placeholder.image(img, caption="Generated Table", use_column_width=True)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            byte_im = buf.getvalue()
            st.download_button(
                label="Download het plaatje",
                data=byte_im,
                file_name="table.png",
                mime="image/png",
                key="download_table"
            )



# ---------- Sleepopties mode ----------
elif mode == "Sleepopties Maken":
    with left:
        st.header("Sleepopties genereren")

        # Main input block grouped
        with st.container():
            tekst_titel = st.text_input("Titel van de tekst", value="title", key="sleep_titel")
            tekst_itemnummer = st.text_input("Item nummer", value="1", key="sleep_itemnr")
            num_columns = st.number_input(
                "Hoeveel kolommen heeft de tabel?",
                min_value=1,
                value=2,
                step=1,
                key="sleep_num_columns",
                help="Dit is nodig om de grootte van de plaatjes goed te krijgen.",
            )
            max_chars_per_line_sleep = st.number_input("Kies het aantal karakters per regel", min_value=10, value=33, key="sleep_wrap")

        st.subheader("Sleepopties")
        st.write("Laat sleepopties die je niet nodig hebt leeg.")

        # Display the 8 text areas in two columns to save vertical space
        letters = ["A", "B", "C", "D", "E", "F", "G", "H"]
        options = [""] * 8
        # two-column layout for options
        opt_cols = st.columns(2)
        for idx, L in enumerate(letters):
            col_idx = 0 if idx < 4 else 1
            with opt_cols[col_idx]:
                options[idx] = st.text_area(f"Sleepoptie {L}", value="", height=80, key=f"opt_{L}")

        gen_sleep = st.button("Genereer sleepopties", key="gen_sleep")

    with right:
        st.subheader("Gegenereerde plaatjes")
        if gen_sleep:
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
                st.warning("Vul op z'n minst 1 sleepoptie in.")
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

                # Display individual images and provide per-image downloads
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
                            file_name=filename,
                            mime="image/png",
                            key=f"download_{i}"
                        )
                    # create ZIP in RAM and download
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, "w", compression=zipfile.ZIP_DEFLATED) as zip_file:
                        for filename, img in generated_images:
                            img_bytes = io.BytesIO()
                            img.save(img_bytes, format="PNG")
                            img_bytes.seek(0)
                            zip_file.writestr(filename, img_bytes.getvalue())
                    zip_buffer.seek(0)
                    zip_name = f"{tekst_titel}_{tekst_itemnummer}_alle_sleepopties.zip"
                    st.download_button(
                        label="Download All Images (ZIP)",
                        data=zip_buffer.getvalue(),
                        file_name=zip_name,
                        mime="application/zip",
                        key="download_all_zip"
                    )

