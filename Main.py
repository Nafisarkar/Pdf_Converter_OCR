import customtkinter as ctk
from customtkinter import filedialog
import pypdfium2 as pdfium
from PIL import Image, ImageDraw, ImageFont
from customtkinter import CTkImage
import os
import threading
import easyocr  # Import EasyOCR

# Global variables
global currentpath, current_image_path, selected_folder_path
image_label = None
progress_bar = None
loading_label = None  # Added for loading indication
selected_folder_path = None

def marge_text():
    global selected_folder_path
    if not selected_folder_path:
        print("No folder selected for merging text files.")
        return

    def marge_text_thread():
        # Collect all the .txt files from the folder
        text_files = [f for f in os.listdir(selected_folder_path) if f.endswith('.txt')]

        if not text_files:
            print("No text files found in the selected folder.")
            return
        # Sort the text files numerically or based on their order
        text_files.sort(key=lambda x: int(os.path.splitext(x)[0]) if os.path.splitext(x)[0].isdigit() else x)

        merged_text = ""
        for text_file in text_files:
            file_path = os.path.join(selected_folder_path, text_file)
            with open(file_path, 'r', encoding='utf-8') as file:
                merged_text += file.read() + "\n"  # Add a newline between contents of each file

        # Save the merged content to a new file
        folder_name = os.path.basename(selected_folder_path)
        merged_file_path = os.path.join(selected_folder_path, f"{folder_name}_merged.txt")
        with open(merged_file_path, 'w', encoding='utf-8') as merged_file:
            merged_file.write(merged_text)

        print(f"Merged text saved to: {merged_file_path}")

    # Run the merging process in a separate thread
    threading.Thread(target=marge_text_thread).start()
    
    
def count_images_in_folder(folder_path):
    image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff'}
    count = 0
    for file_name in os.listdir(folder_path):
        if os.path.splitext(file_name)[1].lower() in image_extensions:
            count += 1
    return count

def folderSelector():
    global selected_folder_path
    selected_folder_path = filedialog.askdirectory()
    if selected_folder_path:
        print(f"Folder selected: {selected_folder_path}")
        folder_path_label.configure(text=f"Selected Folder: {selected_folder_path}")
        image_count = count_images_in_folder(selected_folder_path)
        image_count_label.configure(text=f"Number of Images: {image_count}")
        ocr_button.grid(row=3, column=0, padx=10, pady=10, sticky="w")  # Show OCR button
        marge_text_files.grid(row=3, column=1, padx=10, pady=10, sticky="w")  # Show Merge Text button



def count_images_in_folder(folder_path):
    image_extensions = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff"}
    count = 0
    for file_name in os.listdir(folder_path):
        if os.path.splitext(file_name)[1].lower() in image_extensions:
            count += 1
    return count


def create_placeholder_image():
    placeholder = Image.new("RGB", (300, 500), (200, 200, 200))
    draw = ImageDraw.Draw(placeholder)
    text = "Image Preview"
    font = ImageFont.load_default()
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    text_position = ((300 - text_width) // 2, (500 - text_height) // 2)
    draw.text(text_position, text, fill=(0, 0, 0), font=font)
    return placeholder


def convertP2i():
    global current_image_path
    if currentpath:
        def convert_thread():
            pdf_name = os.path.splitext(os.path.basename(currentpath))[0]
            output_dir = os.path.join(os.getcwd(), pdf_name)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            dpi_scale = dpi_slider.get() / 100
            pdf = pdfium.PdfDocument(currentpath)
            print(f"Dpi upscaled to {dpi_scale}")
            n_pages = len(pdf)

            for page_number in range(n_pages):
                print(f" Page {page_number} Done !")
                page = pdf.get_page(page_number)
                pil_image = page.render(scale=dpi_scale).to_pil()
                image_path = os.path.join(output_dir, f"{pdf_name}_{page_number + 1}.jpg")
                pil_image.save(image_path)
                current_image_path = image_path
                display_image(image_path)

            print(f"Conversion completed, images saved in folder: {output_dir}")

        # Start conversion in a new thread
        threading.Thread(target=convert_thread).start()
    else:
        print("No file selected")


def start_conversion():
    threading.Thread(target=lambda: app.after(0, convertP2i)).start()


def selectfile():
    global currentpath
    filename = filedialog.askopenfilename()
    pathofpdf.configure(state="normal")
    pathofpdf.delete(0, "end")
    pathofpdf.insert(0, filename)
    pathofpdf.configure(state="disabled")
    currentpath = filename
    print(f"File selected: {filename}")


def display_image(image_path):
    global image_label
    img = Image.open(image_path)
    img.thumbnail((300, 500))
    ctk_image = CTkImage(img, size=(300, 500))

    if image_label is None:
        image_label = ctk.CTkLabel(image_frame, image=ctk_image, text="")
        image_label.image = ctk_image
        image_label.pack(pady=10)
        image_label.bind("<Button-1>", open_image_folder)
    else:
        image_label.configure(image=ctk_image)
        image_label.image = ctk_image
        image_label.bind("<Button-1>", open_image_folder)


def perform_ocr():
    global selected_folder_path
    if not selected_folder_path:
        print("No folder selected for OCR.")
        return

    def ocr_thread():
        ocr_language = ocr_language_entry.get().split(",")
        
        # Set GPU to True to enable GPU usage
        ocr_reader = easyocr.Reader(ocr_language, gpu=False)

        # Perform OCR on each image in the folder
        image_extensions = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff"}
        for file_name in os.listdir(selected_folder_path):
            file_path = os.path.join(selected_folder_path, file_name)
            if os.path.splitext(file_name)[1].lower() in image_extensions:
                result = ocr_reader.readtext(file_path)
                text_content = "\n".join([res[1] for res in result])
                text_file_path = os.path.join(
                    selected_folder_path, os.path.splitext(file_name)[0] + ".txt"
                )
                with open(text_file_path, "w", encoding="utf-8") as f:
                    f.write(text_content)
                print(f"OCR completed for {file_name}, text saved to {text_file_path}")

    # Run the OCR process in a new thread
    threading.Thread(target=ocr_thread).start()



def open_image_folder(event):
    global current_image_path
    if current_image_path:
        try:
            folder_path = os.path.dirname(current_image_path)
            os.startfile(folder_path)
        except Exception as e:
            print(f"Problem opening folder: {e}")
    else:
        print("No image to preview.")


def update_dpi_label(value):
    dpi_value_label.configure(text=f"{int(value)}%")


# Main window
app = ctk.CTk()
app.title("OCR and PDF Helper - SAKUNO")
app.geometry("1250x600")

left_frame = ctk.CTkFrame(app, width=100, height=100, corner_radius=0)
left_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

label = ctk.CTkLabel(left_frame, text="PDF Conversion", fg_color="transparent")
label.grid(row=0, column=0, padx=(10, 0), pady=(10, 0), sticky="w")

button = ctk.CTkButton(left_frame, text="File Selector", command=selectfile)
button.grid(row=1, column=0, padx=10, pady=10, sticky="w")

pathofpdf = ctk.CTkEntry(
    left_frame, placeholder_text="PDF path", width=500, state="disabled"
)
pathofpdf.grid(row=1, column=1, padx=20, pady=10, sticky="w")

ConvertP2i = ctk.CTkButton(left_frame, text="Convert", command=start_conversion)
ConvertP2i.grid(row=2, column=0, padx=10, pady=10, sticky="w")

dpi_label = ctk.CTkLabel(left_frame, text="Set DPI (Quality):")
dpi_label.grid(row=3, column=0, padx=10, pady=(10, 0), sticky="w")

dpi_slider = ctk.CTkSlider(
    left_frame, from_=10, to=500, number_of_steps=490, command=update_dpi_label
)
dpi_slider.set(100)
dpi_slider.grid(row=4, column=0, padx=10, pady=10, sticky="w")

dpi_value_label = ctk.CTkLabel(left_frame, text="100%")
dpi_value_label.grid(row=4, column=1, padx=10, pady=10, sticky="w")

right_frame = ctk.CTkFrame(app, width=350, height=350, corner_radius=0)
right_frame.grid(row=0, column=1, padx=20, pady=20, rowspan=6, sticky="nsew")

image_frame = ctk.CTkFrame(right_frame, width=400, height=400, corner_radius=0)
image_frame.pack(pady=10)

placeholder_image = create_placeholder_image()
ctk_placeholder_image = CTkImage(placeholder_image, size=(300, 500))

image_label = ctk.CTkLabel(image_frame, image=ctk_placeholder_image, text="")
image_label.pack(pady=10)
image_label.bind("<Button-1>", open_image_folder)

leftbottom_frame = ctk.CTkFrame(app, width=100, height=200, corner_radius=0)
leftbottom_frame.grid(row=1, column=0, padx=20, pady=20, sticky="nsew")

OcrRecognitionlabel = ctk.CTkLabel(
    leftbottom_frame, text="Text Recognition", fg_color="transparent"
)
OcrRecognitionlabel.grid(row=0, column=0, padx=(10, 0), pady=(10, 0), sticky="w")

folder_button = ctk.CTkButton(
    leftbottom_frame, text="Folder Selector", command=folderSelector
)
folder_button.grid(row=2, column=0, padx=10, pady=10, sticky="w")

folder_path_label = ctk.CTkLabel(
    leftbottom_frame, text="No folder selected", fg_color="transparent"
)
folder_path_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")

image_count_label = ctk.CTkLabel(
    leftbottom_frame, text="Image Count: 0", fg_color="transparent"
)
image_count_label.grid(row=1, column=1, padx=10, pady=10, sticky="w")

# OCR language selection
ocr_language_label = ctk.CTkLabel(
    leftbottom_frame, text="OCR Language (comma separated):"
)
ocr_language_label.grid(row=2, column=1, padx=10, pady=10, sticky="w")

ocr_language_entry = ctk.CTkEntry(
    leftbottom_frame, placeholder_text="e.g., eng,bn", width=150
)
ocr_language_entry.grid(row=2, column=2, padx=10, pady=10, sticky="w")

# OCR Button (Initially hidden)
ocr_button = ctk.CTkButton(leftbottom_frame, text="Perform OCR", command=perform_ocr)
ocr_button.grid_forget()

marge_text_files = ctk.CTkButton(leftbottom_frame, text="Marge All the text Files", command=marge_text)
marge_text_files.grid_forget()

app.mainloop()
