r"""
# Preprocessing of the image ; however insignificant result

def preprocess_image(img: Image.Image) -> Image.Image:
    # Convert PIL image to OpenCV grayscale
    open_cv_img = np.array(img.convert('L'))
    
    # Apply bilateral filter to reduce noise while preserving edges
    open_cv_img = cv2.bilateralFilter(open_cv_img, 9, 75, 75)
    
    # Adaptive thresholding (binarization)
    thresh = cv2.adaptiveThreshold(open_cv_img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY, 31, 15)

    # Deskew image
    coords = np.column_stack(np.where(thresh < 255))
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    (h, w) = thresh.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    deskewed = cv2.warpAffine(thresh, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

    # Convert back to PIL
    final_img = Image.fromarray(deskewed)
    return final_img


        
        """


import pytesseract
import cv2
import numpy as np
from pdf2image import convert_from_path
from PIL import Image
import pandas as pd
import re
from pdf2image import convert_from_path
import pytesseract
import pandas as pd

def extract_text_from_scanned_pdf(pdf_path):
    try:
        images = convert_from_path(pdf_path, dpi=300)  # high-resolution render
        full_text = ""
        for i, img in enumerate(images):
            processed_img = preprocess_image(img)
            page_text = pytesseract.image_to_string(processed_img, lang='eng')
            page_text = re.sub(r'\s+', ' ', page_text)
            full_text += f"\n\n--- Page {i+1} ---\n\n" + page_text
        return full_text.strip()
    except Exception as e:
        print(f"OCR failed: {e}")
        return 

def preprocess_image(img: Image.Image) -> Image.Image:
    # Convert to OpenCV grayscale
    open_cv_img = np.array(img.convert('L'))

    # Reduce noise while preserving edges
    open_cv_img = cv2.bilateralFilter(open_cv_img, 9, 75, 75)

    # Apply adaptive thresholding
    thresh = cv2.adaptiveThreshold(
        open_cv_img, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 31, 15
    )

    # Deskew the image
    coords = np.column_stack(np.where(thresh < 255))
    if coords.size == 0:
        return Image.fromarray(thresh)  # fallback (blank page etc.)

    angle = cv2.minAreaRect(coords)[-1]
    angle = -(90 + angle) if angle < -45 else -angle

    (h, w) = thresh.shape[:2]
    M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
    deskewed = cv2.warpAffine(thresh, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

    return Image.fromarray(deskewed)



def extract_ocr_blocks_with_positions(pdf_path):
    try:
        images = convert_from_path(pdf_path, dpi=300)
        all_blocks = []

        for page_num, img in enumerate(images):
            processed_img = preprocess_image(img)

            ocr_data = pytesseract.image_to_data(
                processed_img,
                lang='eng',
                output_type=pytesseract.Output.DATAFRAME
            )

            ocr_data = ocr_data[ocr_data['text'].notnull()]  # remove blanks
            ocr_data['page'] = page_num + 1
            all_blocks.append(ocr_data)

        full_df = pd.concat(all_blocks, ignore_index=True)
        return full_df

    except Exception as e:
        print(f"OCR layout extraction failed: {e}")
        return pd.DataFrame()
    
 
def extract_title_from_ocr_blocks(ocr_df):
    if ocr_df.empty:
        return "N/A"

    # Filter: high confidence, non-empty text, top page only
    df = ocr_df[(ocr_df['conf'] > 95) & (ocr_df['page'] == 1)]

    # Group by line (using top position)
    grouped = df.groupby('top')

    title_candidates = []

    for top_pos in sorted(grouped.groups.keys()):
        line_df = grouped.get_group(top_pos).sort_values('left')
        line_text = " ".join(line_df['text'].tolist()).strip()

        # Skip short or noisy lines
        if len(line_text) < 10:
            continue
        if any(keyword in line_text.lower() for keyword in ["doi", "journal", "volume", "access", "license", "email"]):
            continue

        title_candidates.append((top_pos, line_text))

        # Optionally stop after 2 stacked lines
        if len(title_candidates) == 2:
            break

    # Combine best 1-2 lines
    title = " ".join([text for _, text in title_candidates])
    return title.strip() if title else "N/A"
