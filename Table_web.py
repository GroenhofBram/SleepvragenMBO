def create_sleepoptie_single_image(
    text,
    tekst_titel="title",
    tekst_itemnummer="1",
    canvas_height=None,    # new param for fixed canvas height
    max_chars_per_line=33,
    font_size=11,
    base_dir=None,
):
    if not text or str(text).strip() == "":
        return None, None

    wrap_result = wrap_text(text.strip(), max_chars_per_line)
    wrapped_text = wrap_result["wrapped_text"]
    line_count = wrap_result["line_count"]

    # Use calculated height from line count or the forced fixed height if provided
    calculated_height = max(10, (line_count * 15) + 5)
    if canvas_height is not None:
        calculated_height = max(calculated_height, canvas_height)  # ensure not smaller than fixed height

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
        font = ImageFont.truetype(verdana_path, font_size)  # font_size fixed to 11
    except Exception:
        font = ImageFont.load_default()

    margin_x = 5
    margin_y = 3
    draw.multiline_text((margin_x, margin_y), wrapped_text, fill="black", font=font, spacing=4)

    filename = f"{tekst_titel}_{tekst_itemnummer}.png"

    return img, filename


# Inside your Streamlit app button click event for generating images:
if st.button("Generate Sleepoptie Images"):
    base_dir = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
    heights = []
    non_empty_texts = [t for t in options if t and t.strip() != ""]
    # First get heights for each sleepoptie
    for text in non_empty_texts:
        wrap_result = wrap_text(text.strip(), max_chars_per_line)
        line_count = wrap_result["line_count"]
        height = max(10, (line_count * 15) + 5)
        heights.append(height)

    max_height = max(heights) if heights else None

    generated_images = []
    for idx, text in enumerate(options, start=1):
        if not text or text.strip() == "":
            continue
        img, filename = create_sleepoptie_single_image(
            text,
            tekst_titel=tekst_titel,
            tekst_itemnummer=f"{tekst_itemnummer}_{idx}",
            canvas_height=max_height,   
            max_chars_per_line=max_chars_per_line,
            font_size=11,               # fixed font size 11
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
