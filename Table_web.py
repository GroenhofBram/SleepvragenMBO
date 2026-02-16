from PIL import Image, ImageDraw, ImageFont
import textwrap

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
        # store requested font names (we'll try variants)
        self.font_path = font_path
        self.bold_font_path = bold_font_path
        self.font_size = font_size
        self.cells = {}
        self.bold_cells = {}

    def _try_load_font(self, candidates):
        """Try a list of candidate filenames/paths and return first loadable truetype font or None."""
        for name in candidates:
            try:
                return ImageFont.truetype(name, self.font_size)
            except OSError:
                continue
        return None

    def set_text(self, row, col, text, bold=False):
        self.cells[(row, col)] = text
        self.bold_cells[(row, col)] = bold

    def draw(self):
        img = Image.new("RGB", (self.width, self.height), self.bg_color)
        draw = ImageDraw.Draw(img)

        # draw vertical lines
        for c in range(self.cols + 1):
            x = c * self.col_width
            draw.line([(x, 0), (x, self.height)], fill=self.line_color, width=self.line_width)

        # compute y positions for rows and draw horizontal lines
        y_positions = [0]
        for h in self.row_height:
            y_positions.append(y_positions[-1] + h)
        for y in y_positions:
            draw.line([(0, y), (self.width, y)], fill=self.line_color, width=self.line_width)

        # Try loading Verdana (several common names). If not found, fall back to default font.
        regular_candidates = [
            self.font_path,
            "Verdana.ttf",
            "verdana.ttf",
            "/usr/share/fonts/truetype/msttcorefonts/Verdana.ttf",
            "/usr/share/fonts/truetype/msttcorefonts/verdana.ttf"
        ]
        bold_candidates = [
            self.bold_font_path,
            "verdanab.ttf",
            "Verdana Bold.ttf",
            "Verdana-Bold.ttf",
            "/usr/share/fonts/truetype/msttcorefonts/Verdana_Bold.ttf",
            "/usr/share/fonts/truetype/msttcorefonts/verdanab.ttf"
        ]

        normal_font = self._try_load_font(regular_candidates)
        bold_font = self._try_load_font(bold_candidates)

        # If no truetype fonts found, fall back to PIL default (monospace) but still simulate bold if requested.
        if normal_font is None:
            normal_font = ImageFont.load_default()
        padding_left = 8

        for (r, c), text in self.cells.items():
            # support None or empty string gracefully
            if not text:
                continue
            x = c * self.col_width
            y = y_positions[r]
            bold = self.bold_cells.get((r, c), False)

            # pick font object to use for measurement/drawing
            font_obj = bold_font if (bold and bold_font is not None) else normal_font
            simulate_bold = bold and (bold_font is None)

            # wrap text into lines
            lines = textwrap.wrap(text, width=self.wrap_width) or [""]

            # measure line heights
            line_heights = []
            for line in lines:
                bbox = draw.textbbox((0, 0), line, font=font_obj)
                line_heights.append(bbox[3] - bbox[1])
            total_text_height = sum(line_heights)
            # vertical center within row
            current_y = y + (y_positions[r + 1] - y - total_text_height) / 2

            for i, line in enumerate(lines):
                pos = (x + padding_left, current_y)
                if simulate_bold:
                    # draw twice with a 1px offset to simulate bold
                    draw.text(pos, line, fill=(0, 0, 0), font=font_obj)
                    draw.text((pos[0] + 1, pos[1]), line, fill=(0, 0, 0), font=font_obj)
                else:
                    draw.text(pos, line, fill=(0, 0, 0), font=font_obj)
                current_y += line_heights[i]

        return img

    def save(self, filename):
        img = self.draw()
        img.save(filename, "JPEG")
