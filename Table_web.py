import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import textwrap
import io

# --- TableImage class (same as yours) ---
class TableImage:
    def __init__(self, rows, cols, col_width, row_height,
                 font_path="verdana.ttf", bold_font_path="verdanab.ttf",
                 font_size=10, line_color=(0, 0, 0), bg_color=(255, 255, 255),
                 line_width=2, wrap_width=30):
        self.rows = rows
        self.cols = cols
        self.col_width = col_width
        self.line_color = line_color
        self.bg_color = bg_color
        self.line_width = line_width
        self.wrap_width = wrap_width

        if isinstance(row_height, list):
            self.row_height = row_height
        else:
            self.row_height = [row_height] * rows

        self.height = sum(self.row_height)
        self.width = cols * col_width

        self.font_path = font_path
        self.bold_font_path = bold_font_path
        self.font_size = font_size

        self.cells = {}
        self.bold_cells = {}

    def set_text(self, row, col, text, bold=False):
        self.cells[(row, col)] = text
        self.bold_cells[(row, col)] = bold

    def draw(self):
        img = Image.new("RGB", (self.width, self.height), self.bg_color)
        draw = ImageDraw.Draw(img)

        # Vertical lines
        for c in range(self.cols + 1):
            x = c * self.col_width
            draw.line([(x, 0), (x, self.height)], fill=self.line_color, width=self.line_width)

        y_positions = [0]
        for h in self.row_height:
            y_positions.append(y_positions[-1] + h)

        # Horizontal lines
        for y in y_positions:
            draw.line([(0, y), (self.width, y)], fill=self.line_color, width=self.line_width)

        padding_left = 8

        for (r, c), text in self.cells.items():
            x = c * self.col_width
            y = y_positions[r]

            bold = self.bold_cells.get((r, c), False)
            font_path = self.bold_font_path if bold else self.font_path
            try:
                font = ImageFont.truetype(font_path, self.font_size)
            except OSError:
                font = ImageFont.load_default()

            lines = textwrap.wrap(text, width=self.wrap_width)
            line_heights = [draw.textbbox((0, 0), line, font=font)[3] - draw.textbbox((0, 0), line, font=font)[1] for line in lines]
            total_text_height = sum(line_heights)

            current_y = y + (y_positions[r + 1] - y - total_text_height) / 2
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
    ("Type 1 (graphic gapmatch)", "Type 2 (graphic gapmatch categorize)")
)

if table_type.startswith("Type 1"):
    rows = st.number_input("Number of rows", min_value=1, value=2)
    cols = st.number_input("Number of columns", min_value=1, value=2)
    row_height = st.number_input("Row height (pixels)", min_value=10, value=50)
    col_width = st.number_input("Column width (pixels)", min_value=10, value=100)
    row_heights = row_height
else:
    rows = 2
    cols = 2
    col_width = 225
    row_heights = []
    for i in range(rows):
        h = st.number_input(f"Height of row {i+1} (pixels)", min_value=10, value=100)
        row_heights.append(h)
    bold_choice = st.checkbox("Make all text bold?")

# Create TableImage object
table = TableImage(
    rows=rows,
    cols=cols,
    row_height=row_heights,
    col_width=col_width,
    font_size=11,
    line_width=1,
    wrap_width=29
)

# Input for each cell
st.subheader("Enter cell text")
for r in range(rows):
    for c in range(cols):
        text = st.text_input(f"Cell ({r+1},{c+1})", key=f"text_{r}_{c}")
        if table_type.startswith("Type 1"):
            bold_cell = st.checkbox(f"Bold?", key=f"bold_{r}_{c}")
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
        mime="image/jpeg"
    )
