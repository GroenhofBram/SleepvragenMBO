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
    ):
        self.rows = rows
        self.cols = cols
        self.col_width = col_width
        self.line_color = line_color
        self.bg_color = bg_color
        self.line_width = line_width
        self.wrap_width = wrap_width

        # Normalize row_height to a list of heights (one per row)
        if isinstance(row_height, list):
            if len(row_height) != rows:
                # if lengths differ, try to pad or truncate
                if len(row_height) < rows:
                    row_height = row_height + [row_height[-1]] * (rows - len(row_height))
                else:
                    row_height = row_height[:rows]
            self.row_height = row_height
        else:
            # single value: replicate for all rows
            self.row_height = [int(row_height)] * rows

        self.height = sum(self.row_height)
        self.width = int(cols * col_width)

        try:
            BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        except NameError:
            BASE_DIR = os.getcwd()

        self.font_path = os.path.join(BASE_DIR, font_path)
        self.bold_font_path = os.path.join(BASE_DIR, bold_font_path)
        self.font_size = font_size
        self.cells = {}
        self.bold_cells = {}

    def set_text(self, row, col, text, bold=False):
        self.cells[(row, col)] = text
        self.bold_cells[(row, col)] = bool(bold)

    def draw(self):
        img = Image.new("RGB", (self.width, self.height), self.bg_color)
        draw = ImageDraw.Draw(img)

        # Pre-compute y positions
        y_positions = [0]
        for h in self.row_height:
            y_positions.append(y_positions[-1] + int(h))

        # Draw rectangles for every cell (including outer borders)
        for r in range(self.rows):
            y0 = y_positions[r]
            y1 = y_positions[r + 1] - 1  # keep inside image bounds
            for c in range(self.cols):
                x0 = int(c * self.col_width)
                x1 = int(x0 + self.col_width - 1)  # keep inside image bounds
                draw.rectangle([x0, y0, x1, y1], outline=self.line_color, width=self.line_width)

        padding_left = 8
        # Draw text for each cell
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
            # compute line heights using textbbox if available
            line_heights = []
            for line in lines:
                try:
                    bbox = draw.textbbox((0, 0), line, font=font)
                    line_h = bbox[3] - bbox[1]
                except Exception:
                    # fallback
                    _, line_h = font.getsize(line)
                line_heights.append(line_h)

            if not line_heights:
                line_heights = [0]

            total_text_height = sum(line_heights)
            cell_height = y_positions[r + 1] - y_positions[r]
            current_y = y + (cell_height - total_text_height) / 2

            for i, line in enumerate(lines):
                draw.text((x + padding_left, current_y), line, fill=(0, 0, 0), font=font)
                current_y += line_heights[i]

        return img

    def save(self, filename):
        img = self.draw()
        img.save(filename, "JPEG")


# --- Streamlit app ---
st.title("Table Image Generator")

table_type = st.selectbox(
    "Select table type",
    ("Type 1 (graphic gapmatch)", "Type 2 (graphic gapmatch categorize)"),
)

if table_type.startswith("Type 1"):
    rows = st.number_input("Number of rows", min_value=1, value=2, step=1)
    cols = st.number_input("Number of columns", min_value=1, value=2, step=1)
    longest_rows = st.number_input(
        "How many rows are required for the longest answer?",
        min_value=1,
        value=1,
        step=1,
    )
    row_height_pixels = int(longest_rows * 18)
    st.write(f"Row height (pixels) will be: {row_height_pixels} px ( {longest_rows} × 18 )")
    col_width = st.number_input("Column width (pixels)", min_value=10, value=100, step=1)
    row_heights = row_height_pixels  # single value replicated across rows
else:
    rows = 2
    cols = 2
    col_width = 225

    heading_rows = st.number_input(
        "How many rows are required for the headings?",
        min_value=1,
        value=1,
        step=1,
        key="heading_rows",
    )
    st.write(f"Height of row 1 (pixels) will be: {heading_rows * 18} px ( {heading_rows} × 18 )")

    longest_rows = st.number_input(
        "How many rows are required for the longest answer?",
        min_value=1,
        value=1,
        step=1,
        key="longest_rows_type2",
    )

    answers_per_box = st.number_input(
        "How many answers can fit in 1 box?",
        min_value=1,
        value=1,
        step=1,
        key="answers_per_box",
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

    # Convert to bytes for download
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    byte_im = buf.getvalue()
    st.download_button(
        label="Download Table Image",
        data=byte_im,
        file_name="table.jpg",
        mime="image/jpeg",
    )
