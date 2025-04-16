from fastapi import FastAPI, File, UploadFile, BackgroundTasks
from fastapi.responses import FileResponse
import pandas as pd
import os
import re
import requests
import shutil
import zipfile
import csv
from pathlib import Path
from datetime import datetime

app = FastAPI()
UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"
EIMAGES_DIR = "outputs/electronics-images"
MIMAGES_DIR = "outputs/medical-images"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(EIMAGES_DIR, exist_ok=True)
os.makedirs(MIMAGES_DIR, exist_ok=True)


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
    data.columns = data.columns.str.strip()  # Remove leading/trailing spaces

    # Ensure required columns exist and handle missing values
    required_columns = {
        "Major Category": "",
        "Minor Category": "",
        "Description": "",
        "Extended Description": "",
        "Item Net Weight": 0,
        "Available Quantity": 0,
        "List Price": 0,
        "UPC Code": "",
        "Standard Price": 0
    }

    for col, default in required_columns.items():
        if col not in data.columns:
            data[col] = default
        else:
            data[col] = data[col].fillna(default)

    # Ensure Major Category and Minor Category are strings
    data["Major Category"] = data["Major Category"].astype(str)
    data["Minor Category"] = data["Minor Category"].astype(str)

    # Create the final mapped data frame
    mapped_data = pd.DataFrame({
        "Handle": data["Description"].apply(generate_handle),
        "Title": data["Description"],
        "Body (HTML)": data["Extended Description"].apply(lambda x: f"<p>{x}</p>" if pd.notna(x) else ""),
        "Vendor": "My Store",
        "Product Category": data["Major Category"],
        "Type": data["Minor Category"],
        "Tags": "",
        "Published": True,
        "Major category": data["Major category"] + " > " + data["Minor Category"],
        "Option1 Name": "Title",
        "Option1 Value": "Default Title",
        "Option1 Linked To": "",
        "Option2 Name": "",
        "Option2 Value": "",
        "Option2 Linked To": "",
        "Option3 Name": "",
        "Option3 Value": "",
        "Option3 Linked To": "",
        "Variant SKU": "",
        "Variant Grams": data["Item Net Weight"],
        "Variant Inventory Tracker": "",
        "Variant Inventory Qty": data["Available Quantity"],
        "Variant Inventory Policy": "deny",
        "Variant Fulfillment Service": "manual",
        "Variant Price": data["List Price"],
        "Variant Compare At Price": "",
        "Variant Requires Shipping": True,
        "Variant Taxable": True,
        "Variant Barcode": data["UPC Code"],
        "Image Src": data.iloc[:, 15].apply(process_image) if data.shape[1] > 15 else "",
        "Image Position": data.iloc[:, 15].apply(calculate_image_position) if data.shape[1] > 15 else 0,
        "Image Alt Text": "",
        "Gift Card": False,
        "SEO Title": "",
        "SEO Description": "",
        "Google Shopping / Google Product Category": "",
        "Google Shopping / Gender": "",
        "Google Shopping / Age Group": "",
        "Google Shopping / MPN": "",
        "Google Shopping / Condition": "",
        "Google Shopping / Custom Product": "",
        "Google Shopping / Custom Label 0": "",
        "Google Shopping / Custom Label 1": "",
        "Google Shopping / Custom Label 2": "",
        "Google Shopping / Custom Label 3": "",
        "Google Shopping / Custom Label 4": "",
        "Variant Image": "",
        "Variant Weight Unit": "lb",
        "Variant Tax Code": "",
        "Cost per item": data["Standard Price"],
        "Included / United States": True,
        "Price / United States": "",
        "Compare At Price / United States": "",
        "Included / International": True,
        "Price / International": "",
        "Compare At Price / International": "",
        "Status": "active"
    })

    output_csv = os.path.join(OUTPUT_DIR, "cms-medical-product-list-{0}.csv".format(datetime.now().strftime("%Y-%m-%d %H-%M-%S")))
    mapped_data.to_csv(output_csv, index=False)

    download_images(data, MIMAGES_DIR)
    return output_csv


def process_image_csv(file_path):
    image_directory = EIMAGES_DIR
    output_csv = os.path.join(OUTPUT_DIR, "output.csv")
    # available_images = set(os.listdir(image_directory))
    with open(file_path, mode="r", newline="") as infile, open(output_csv, mode="w", newline="") as outfile:
        reader = csv.reader(infile)
        writer = csv.writer(outfile)
        header = next(reader)
        header.append("image")
        header.append("images-url")
        writer.writerow(header)
        for row in reader:
            image_name = row[0].strip()
            if not image_name:
                continue
            image_name = f'{image_name}.jpg'
            row.append(image_name if image_name else "")
            images_url = f'https://www.dandh.com/images/prod300/{image_name}'
            row.append(images_url if images_url else "")
            writer.writerow(row)
    return output_csv


def create_zip():
    zip_path = os.path.join(OUTPUT_DIR, "processed_data.zip")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for folder, _, files in os.walk(OUTPUT_DIR):
            for file in files:
                file_path = os.path.join(folder, file)
                zipf.write(file_path, os.path.relpath(file_path, OUTPUT_DIR))
    return zip_path


@app.post("/upload-cms-medical-csv/")
async def upload_file(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    process_csv(file_path)
    zip_path = create_zip()
    return FileResponse(zip_path, filename="processed_data.zip", media_type="application/zip")


@app.post("/upload-electronics-csv/")
async def upload_image_csv(file: UploadFile = File(...)):
    file_name = "dh-electronics-product-list-{0}.csv".format(datetime.now().strftime("%Y-%m-%d %H-%M-%S"))
    file_path = os.path.join(UPLOAD_DIR, file_name)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    output_csv = process_image_csv(file_path)
    return FileResponse(output_csv, filename=file_name, media_type="text/csv")
