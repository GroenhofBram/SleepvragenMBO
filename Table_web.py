import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import textwrap
import io
import os

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

            # Use font metrics for consistent line height
            try:
                ascent, descent = font.getmetrics()
                line_height = ascent + descent
            except Exception:
                # fallback: mmeasure fiirst line 
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
            # center vertically
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


# --- Streamlit app ---
st.title("Table Image Generator")

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
    row_heights = row_height_pixels  # single int; TableImage will replicate it
else:
    # Type 2 defaults (two rows, two columns)
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

# Create TableImage object
table = TableImage(
    rows=rows,
    cols=cols,
    row_height=row_heights,
    col_width=col_width,
    font_size=11,
    line_width=1,
    wrap_width=29,
)

# Input for each cell
st.subheader("Enter cell text")
for r in range(rows):
    for c in range(cols):
        text = st.text_input(f"Cell ({r+1},{c+1})", key=f"text_{r}_{c}")
        if table_type.startswith("Type 1"):
            bold_cell = st.checkbox(f"Bold? (Cell {r+1},{c+1})", key=f"bold_{r}_{c}")
        else:
            bold_cell = bold_choice
        table.set_text(r, c, text, bold=bold_cell)

# Generate and download image
if st.button("Generate Table Image"):
    img = table.draw()
    st.image(img, caption="Generated Table", use_column_width=True)
    # Convert to bytes for download (PNG for crisper text)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    byte_im = buf.getvalue()
    st.download_button(
        label="Download Table Image",
        data=byte_im,
        file_name="table.png",
        mime="image/png",
    )
