from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import fitz
import os
import uuid
import zipfile

app = FastAPI()

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.post("/extract-images/")
async def extract_images(file: UploadFile = File(...)):
    try:
        pdf_id = str(uuid.uuid4())
        pdf_path = os.path.join(UPLOAD_FOLDER, f"{pdf_id}.pdf")

        with open(pdf_path, "wb") as f:
            f.write(await file.read())

        doc = fitz.open(pdf_path)
        image_paths = []

        for page_index in range(len(doc)):
            page = doc[page_index]
            images = page.get_images(full=True)

            for img_index, img in enumerate(images):
                xref = img[0]
                base_image = doc.extract_image(xref)

                image_bytes = base_image["image"]
                image_ext = base_image["ext"]

                img_filename = f"{pdf_id}_page{page_index+1}_{img_index}.{image_ext}"
                img_path = os.path.join(OUTPUT_FOLDER, img_filename)

                with open(img_path, "wb") as img_file:
                    img_file.write(image_bytes)

                image_paths.append(img_filename)

        zip_filename = f"{pdf_id}.zip"
        zip_path = os.path.join(OUTPUT_FOLDER, zip_filename)

        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for img in image_paths:
                zipf.write(os.path.join(OUTPUT_FOLDER, img), img)

        return JSONResponse({
            "status": "success",
            "total_images": len(image_paths),
            "images": image_paths,
            "zip_download": f"/download/{zip_filename}"
        })

    except Exception as e:
        return JSONResponse({
            "status": "error",
            "message": str(e)
        })

@app.get("/download/{file_name}")
def download_file(file_name: str):
    file_path = os.path.join(OUTPUT_FOLDER, file_name)
    if os.path.exists(file_path):
        return JSONResponse({
            "download_link": file_name
        })
    return {"error": "File not found"}