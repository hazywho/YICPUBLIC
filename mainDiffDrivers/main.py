import gradio as gr
import cv2
import numpy as np
import AutoFocus  # Your hardware control module
import tempfile
import os

# --------- Helper Functions ---------

def encode_image(img):
    """Encode OpenCV image as PNG byte array for downloading."""
    _, buffer = cv2.imencode('.png', img)
    return buffer.tobytes()


def start_driver(slide_area, pH, Do, BOD, COD, TDS, ammonia):
    """Initialize the AutoFocus driver."""
    waterData = {
        "pH": pH,
        "Dissolved Oxygen": Do,
        "Biochemical Oxygen Demand": int(BOD),
        "Chemical Oxygen Demand": int(COD),
        "Nitrogen (ammonia)": int(ammonia)
    }
    driver = AutoFocus.main(slideArea=slide_area, waterData=waterData)
    return driver, None, None, None, 0, 0  # driver, imgs, annos, response, index, n_images


def reset_driver(driver):
    """Call the driver reset method."""
    if driver:
        driver._clearCalibration()
        return "Reset done!"
    return "Driver not initialized."


def capture_images(driver):
    """Capture and process images."""
    if driver is None:
        return "Driver not available", None, None, 0, 0

    status = True
    if status:
        response, origImageList, annotatedImageList = driver.moveAroundAndProcess()
        n_images = len(annotatedImageList)
        return response, origImageList, annotatedImageList, 0, n_images
    else:
        return "Calibration error :(", None, None, 0, 0


def get_current_image(annotatedImgs, imgs, image_index):
    """Get annotated image and original image (as file path) by index."""
    if annotatedImgs is None or imgs is None:
        return None, None, "No images yet."
    if image_index < 0 or image_index >= len(annotatedImgs):
        return None, None, "Index out of bounds."

    annotated = annotatedImgs[image_index]

    # Encode and write image to a temporary file
    raw_bytes = encode_image(imgs[image_index])
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    tmp_file.write(raw_bytes)
    tmp_file.close()

    return annotated, tmp_file.name, f"AI analysis: Image {image_index + 1} of {len(annotatedImgs)}"


def update_index(current_index, direction, n_images):
    """Move image index forward or backward."""
    if n_images == 0:
        return 0
    if direction == "next":
        return (current_index + 1) % n_images
    else:
        return (current_index - 1) % n_images


def clear_all():
    """Clear everything."""
    return None, None, None, None, 0, 0, "", None, None, ""  # ⬅️ Added empty string for ai_report


# --------- Gradio Interface ---------

with gr.Blocks(title="OceanWatchers") as demo:
    # Persistent state
    driver = gr.State()
    imgs = gr.State()
    annotatedImgs = gr.State()
    response = gr.State()
    image_index = gr.State(0)
    n_images = gr.State(0)

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### Water Quality Data Input")
            slide_area = gr.Textbox(label="Measured Slide Area (cm^2)", value="3.24")
            pH = gr.Slider(label="pH", minimum=0.0, maximum=14.0, value=7.0, step=0.1)
            Do = gr.Slider(label="Dissolved Oxygen (mg/L)", minimum=0.0, maximum=20.0, value=6.0, step=0.1)
            BOD = gr.Textbox(label="Biochemical Oxygen Demand (mg/L)", value="7")
            COD = gr.Textbox(label="Chemical Oxygen Demand (mg/L)", value="7")
            TDS = gr.Textbox(label="Total Dissolved Solids (mg/L)", value="7")
            ammonia = gr.Textbox(label="Nitrogen (Ammonia) (mg/L)", value="7")

            submit_btn = gr.Button("Submit Data and Begin")
            reset_btn = gr.Button("Reset Calibration")
            start_btn = gr.Button("Start Taking Photo")
            clear_btn = gr.Button("Finish & Clear")

            reset_status = gr.Textbox(label="Reset Status", interactive=False)

        with gr.Column(scale=2):
            gr.Markdown("### Image Results")
            image_display = gr.Image(label="Annotated Image", type="numpy")
            download_image = gr.File(label="Download Image")
            analysis_text = gr.Textbox(label="AI Analysis", interactive=False)

            ai_report = gr.Markdown(label="Ecological Summary Report")  # ⬅️ ADDED

            with gr.Row():
                prev_btn = gr.Button("Prev")
                next_btn = gr.Button("Next")

    # Submit data and init driver
    submit_btn.click(
        start_driver,
        inputs=[slide_area, pH, Do, BOD, COD, TDS, ammonia],
        outputs=[driver, imgs, annotatedImgs, response, image_index, n_images]
    )

    # Reset calibration
    reset_btn.click(
        reset_driver,
        inputs=[driver],
        outputs=[reset_status]
    )

    # Start photo taking
    start_btn.click(
        capture_images,
        inputs=[driver],
        outputs=[response, imgs, annotatedImgs, image_index, n_images]
    ).then(
        get_current_image,
        inputs=[annotatedImgs, imgs, image_index],
        outputs=[image_display, download_image, analysis_text]
    ).then(
        lambda r: r,  # ⬅️ Display response in Markdown
        inputs=[response],
        outputs=[ai_report]
    )

    # Prev image
    prev_btn.click(
        update_index,
        inputs=[image_index, gr.Textbox(value="prev", visible=False), n_images],
        outputs=[image_index]
    ).then(
        get_current_image,
        inputs=[annotatedImgs, imgs, image_index],
        outputs=[image_display, download_image, analysis_text]
    )

    # Next image
    next_btn.click(
        update_index,
        inputs=[image_index, gr.Textbox(value="next", visible=False), n_images],
        outputs=[image_index]
    ).then(
        get_current_image,
        inputs=[annotatedImgs, imgs, image_index],
        outputs=[image_display, download_image, analysis_text]
    )

    # Clear all
    clear_btn.click(
        clear_all,
        outputs=[annotatedImgs, imgs, response, driver, image_index, n_images, analysis_text, image_display, download_image, ai_report]  # ⬅️ Added ai_report
    )

# Run the app
demo.launch()
