from utils.ocr_utils import extract_ocr_blocks_with_positions, extract_title_from_ocr_blocks
import os

pdf_path = r"data/Samuel Eilon Elements Of PPC.pdf"

print("🔍 File Exists:", os.path.exists(pdf_path))

ocr_df = extract_ocr_blocks_with_positions(pdf_path)
df = ocr_df[(ocr_df['page'] == 1) & (ocr_df['text'].notnull())]
df = df[df['text'].str.strip() != ""]
df = df.sort_values(by=['top', 'left']).reset_index(drop=True)

heights = df['height'].tolist()

drop_index = None
for i in range(1, len(heights)):
    if heights[i] < 0.6 * heights[i - 1]:  # 40% drop : significant font drop
        drop_index = i
        break

title_block = df.iloc[:drop_index] if drop_index else df.iloc[:5]
title_words = title_block['text'].tolist()
title = " ".join(title_words)

print("📊 OCR DataFrame shape:", ocr_df.shape)

if not ocr_df.empty:
    print("🧾 Sample OCR Data:")
    print(ocr_df[['text', 'left', 'top', 'width', 'height', 'conf', 'page']].head(10))
else:
    print("⚠️ OCR returned an empty DataFrame.")

title = extract_title_from_ocr_blocks(ocr_df)
print("🧠 Detected Title:\n", title)
