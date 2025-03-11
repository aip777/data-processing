from fastapi import FastAPI, File, UploadFile, BackgroundTasks
from fastapi.responses import FileResponse
import pandas as pd
import os
import re
import requests
import shutil
import zipfile
from pathlib import Path

app = FastAPI()
UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"
IMAGES_DIR = "outputs/images"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)


def generate_handle(description):
    description = re.sub(r'\s+', '-', description)
    description = re.sub(r'[/.]', '-', description)
    description = re.sub(r'-+', '-', description)
    description = re.sub(r'[^a-zA-Z0-9-]', '', description)
    description = description.strip('-')
    return description.lower()


def process_image(image_column):
    return f"https://cdn.shopify.com/s/files/1/0673/7775/8363/files/{image_column.strip()}" if pd.notna(
        image_column) and image_column.strip() else ""


def calculate_image_position(image_column):
    return 1 if pd.notna(image_column) and image_column.strip() else 0


def download_images(data, output_folder):
    for col in range(33, 36):
        for image_url in data.iloc[:, col]:
            if pd.notna(image_url) and image_url.strip():
                image_url = image_url.strip()
                image_name = os.path.basename(image_url)
                save_path = os.path.join(output_folder, image_name)
                try:
                    response = requests.get(image_url, stream=True, timeout=30)
                    if response.status_code == 200:
                        with open(save_path, 'wb') as f:
                            for chunk in response.iter_content(1024):
                                f.write(chunk)
                except Exception as e:
                    print(f"Error downloading {image_url}: {e}")


def process_csv(file_path):
    data = pd.read_csv(file_path, encoding='latin1')
    mapped_data = pd.DataFrame({
        "Handle": data["Description"].apply(generate_handle),
        "Title": data["Description"],
        "Body (HTML)": data["Extended Description"].apply(lambda x: f"<p>{x}</p>" if pd.notna(x) else ""),
        "Vendor": "My Store",
        "Type": data["Minor Category"],
        "Variant Grams": data["Item Net Weight"],
        "Variant Inventory Qty": data["Available Quantity"],
        "Variant Price": data["List Price"],
        "Variant Barcode": data["UPC Code"],
        "Image Src": data.iloc[:, 15].apply(process_image),
        "Image Position": data.iloc[:, 15].apply(calculate_image_position),
        "Cost per item": data["Standard Price"],
        "Status": "active"
    })
    output_csv = os.path.join(OUTPUT_DIR, "formatted.csv")
    mapped_data.to_csv(output_csv, index=False)
    download_images(data, IMAGES_DIR)
    return output_csv


def create_zip():
    zip_path = os.path.join(OUTPUT_DIR, "processed_data.zip")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for folder, _, files in os.walk(OUTPUT_DIR):
            for file in files:
                file_path = os.path.join(folder, file)
                zipf.write(file_path, os.path.relpath(file_path, OUTPUT_DIR))
    return zip_path


@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    process_csv(file_path)
    zip_path = create_zip()
    return FileResponse(zip_path, filename="processed_data.zip", media_type="application/zip")
