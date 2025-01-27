import pandas as pd
import os
import re
import requests

supplier_csv_path = "data/supplier_data.csv"
output_csv_path = "data/new-formated.csv"
output_folder = "images"
data = pd.read_csv(supplier_csv_path, encoding='latin1')
os.makedirs(output_folder, exist_ok=True)

def download_image(save_path):
    try:
        for _row in range(33,36):
            for i, image_url in enumerate(data.iloc[:, _row]):
                if pd.notna(image_url) and image_url.strip():
                    image_url = image_url.strip()
                    image_name = os.path.basename(image_url)
                    save_path = os.path.join(output_folder, image_name)
                response = requests.get(image_url, stream=True, timeout=10)
                if response.status_code == 200:
                    with open(save_path, 'wb') as f:
                        for chunk in response.iter_content(1024):
                            f.write(chunk)
                    print(f"Downloaded: {save_path}")
                else:
                    print(f"Failed to download {image_url} - Status code: {response.status_code}")
    except Exception as e:
        print(f"Error downloading {e}")
download_image(output_folder)
def generate_handle(description):
    description = re.sub(r'\s+', '-', description)
    description = re.sub(r'[/.]', '-', description)
    description = re.sub(r'-+', '-', description)
    description = re.sub(r'[^a-zA-Z0-9-]', '', description)
    description = description.strip('-')
    return description.lower()

def process_image(image_column):
    if pd.notna(image_column) and image_column.strip() != "":
        save_path = os.path.join(output_folder, image_column.strip())
        download_image('image_url', save_path)
        return f"https://cdn.shopify.com/s/files/1/0673/7775/8363/files/{image_column.strip()}"
    return ""

def calculate_image_position(image_column):
    if pd.notna(image_column) and image_column.strip() != "":
        return 1
    return 0

mapped_data = pd.DataFrame({
    "Handle": data["Description"].apply(generate_handle),
    "Title": data["Description"],
    "Body (HTML)": data["Extended Description"].apply(
        lambda x: f"<p>{x}</p>" if pd.notna(x) else ""),
    "Vendor": "My Store",
    "Product Category": "",
    "Type": data["Minor Category"],
    "Tags": "",
    "Published": True,
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
    "Image Src": data.iloc[:, 15].apply(process_image),
    "Image Position": data.iloc[:, 15].apply(calculate_image_position),
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
mapped_data.to_csv(output_csv_path, index=False)

print(f"Data has been successfully transformed and saved to {os.path.abspath(output_csv_path)}")
