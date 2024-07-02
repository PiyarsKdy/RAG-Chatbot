import asyncio
import csv
import io
import requests
from bs4 import BeautifulSoup
import re
import xml.etree.ElementTree as ET
import os
from urllib.parse import urlparse

async def extract_text_from_csv(csv_file):
    try:
        text = ""
        csv_file.seek(0)
        csv_data = csv_file.read().decode('utf-8')
        csv_data_io = io.StringIO(csv_data)
        reader = csv.reader(csv_data_io)
        
        for row in reader:
            non_empty_cells = [cell.strip() for cell in row if cell.strip()]
            if non_empty_cells:
                text += ','.join(non_empty_cells) + '\n'
        
        return text
    except Exception as e:
        print(f"Error extracting text from CSV: {e}")
        return None
    
def extract_and_clean_text(url):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        text = ' '.join(soup.stripped_strings)
        return text
    else:
        print(f"Failed to retrieve content from {url}")
        return None
    
async def parse_xml(xml_url):
    # Fetch the XML content from the URL
    xml_response = await asyncio.to_thread(requests.get, xml_url)
    xml_content = xml_response.content

    # Parse the XML content
    root = ET.fromstring(xml_content)

    # Get the namespace from the root element
    namespace = root.tag.split('}')[0].strip('{')

    for sitemap in root.findall(f"{{{namespace}}}sitemap"):
        sitemap_loc = sitemap.find(f"{{{namespace}}}loc").text
        print(f"Found sitemap: {sitemap_loc}")

        # Download the sitemap content
        sitemap_response = await asyncio.to_thread(requests.get, sitemap_loc)
        sitemap_content = sitemap_response.content

        # Parse the sitemap content
        sitemap_root = ET.fromstring(sitemap_content)

        for url in sitemap_root.findall(f"{{{namespace}}}url"):
            loc = url.find(f"{{{namespace}}}loc").text
            print(f" Found URL: {loc}")
            await save_url_text(loc, "temp_files")


async def save_url_text(url, output_dir):
    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Download the web page content
    response = await asyncio.to_thread(requests.get, url)
    soup = BeautifulSoup(response.content, "html.parser")

    # Extract text from the web page
    text = soup.get_text()

    # Use the full URL as the filename
    parsed_url = urlparse(url)
    file_name = f"{parsed_url.netloc}{parsed_url.path.replace('/', '_')}.txt"
    file_path = os.path.join(output_dir, file_name)

    if not text.strip():
        return {"error": "Unable to extract text from website"}

    cleaned_text = re.sub('[^A-Za-z0-9]+', ' ', text)
    
    # Save the extracted text to a separate text file for each URL
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(cleaned_text)

async def handle_url(url):
    # Detect if the URL is an XML sitemap or a regular URL
    if url.endswith(".xml"):
        await parse_xml(url)
    else:
        await save_url_text(url, "temp_files")