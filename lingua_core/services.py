# import re

# from functools import lru_cache

# from django.conf import settings
# from PIL import Image
# import pytesseract
# import spacy

# pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD


# @lru_cache(maxsize=1)
# def _load_spacy_model():
#     return spacy.load(settings.SPACY_MODEL)

# def split_sentences(text: str) -> list[str]:
#     doc = _load_spacy_model()(text)
#     sentences = [sent.text.strip() for sent in doc.sents]
#     return sentences

# def extract_sentences_from_image(image_file) -> list[str]:
#     image = Image.open(image_file)
#     # 한국어, 영어, 중국어 간체, 중국어 번체 지원
#     text = pytesseract.image_to_string(image, lang='kor+eng+chi_sim+chi_tra')
#     return split_sentences(text)



# def extract_sentences_with_boxes(image_file) -> list[dict]:
#     """
#     이미지에서 문장과 각 문장의 박스 위치를 추출합니다.
#     """
#     image = Image.open(image_file)
#     data = pytesseract.image_to_data(image, lang='kor+eng', output_type=pytesseract.Output.DICT)
    
#     # 줄(line) 단위로 텍스트와 박스 정보를 수집
#     lines = {}
#     for i in range(len(data['text'])):
#         level = data['level'][i]
#         if level == 4:  # 4는 줄(line) 레벨
#             line_num = data['line_num'][i]
#             if line_num not in lines:
#                 lines[line_num] = {
#                     'text': '',
#                     'left': float('inf'),
#                     'top': float('inf'),
#                     'right': 0,
#                     'bottom': 0
#                 }
#         elif level == 5:  # 5는 단어 레벨
#             word = data['text'][i].strip()
#             if word:
#                 line_num = data['line_num'][i]
#                 if line_num in lines:
#                     # 텍스트 추가
#                     if lines[line_num]['text']:
#                         lines[line_num]['text'] += ' ' + word
#                     else:
#                         lines[line_num]['text'] = word
                    
#                     # 박스 위치 업데이트 (단어들의 박스를 합침)
#                     left = data['left'][i]
#                     top = data['top'][i]
#                     width = data['width'][i]
#                     height = data['height'][i]
                    
#                     lines[line_num]['left'] = min(lines[line_num]['left'], left)
#                     lines[line_num]['top'] = min(lines[line_num]['top'], top)
#                     lines[line_num]['right'] = max(lines[line_num]['right'], left + width)
#                     lines[line_num]['bottom'] = max(lines[line_num]['bottom'], top + height)
    
#     # 줄들을 문장으로 변환
#     results = []
#     for line_num in sorted(lines.keys()):
#         line_data = lines[line_num]
#         line_text = line_data['text'].strip()
        
#         if line_text:
#             # 한 줄을 여러 문장으로 분할할 수 있음
#             sentences = re.split(r'(?<=[,.!?])\s+', line_text)
            
#             if len(sentences) == 1:
#                 # 한 줄에 한 문장만 있는 경우
#                 results.append({
#                     "text": sentences[0].strip(),
#                     "box": {
#                         "left": int(line_data['left']) if line_data['left'] != float('inf') else 0,
#                         "top": int(line_data['top']) if line_data['top'] != float('inf') else 0,
#                         "width": int(line_data['right'] - line_data['left']) if line_data['left'] != float('inf') else 0,
#                         "height": int(line_data['bottom'] - line_data['top']) if line_data['top'] != float('inf') else 0
#                     }
#                 })
#             else:
#                 # 한 줄에 여러 문장이 있는 경우, 전체 줄의 박스를 공유
#                 for sentence in sentences:
#                     sentence = sentence.strip()
#                     if sentence:
#                         results.append({
#                             "text": sentence,
#                             "box": {
#                                 "left": int(line_data['left']) if line_data['left'] != float('inf') else 0,
#                                 "top": int(line_data['top']) if line_data['top'] != float('inf') else 0,
#                                 "width": int(line_data['right'] - line_data['left']) if line_data['left'] != float('inf') else 0,
#                                 "height": int(line_data['bottom'] - line_data['top']) if line_data['top'] != float('inf') else 0
#                             }
#                         })
    
#     return results

# def extract_words_from_image(image_file) -> list[str]:
#     image = Image.open(image_file)
#     # 한국어, 영어, 중국어 간체, 중국어 번체 지원
#     text = pytesseract.image_to_string(image, lang='kor+eng+chi_sim+chi_tra')
#     words = text.strip().split()
#     return words


# def extract_words_with_boxes(image_file) -> list[dict]:
#     image = Image.open(image_file)
#     # 한국어, 영어, 중국어 간체, 중국어 번체 지원
#     data = pytesseract.image_to_data(image, lang='kor+eng+chi_sim+chi_tra', output_type=pytesseract.Output.DICT)

#     results = []
#     for i in range(len(data['text'])):
#         word = data['text'][i].strip()
#         if word:  # 빈 문자열 제외
#             results.append({
#                 "text": word,
#                 "box": {
#                     "left": data['left'][i],
#                     "top": data['top'][i],
#                     "width": data['width'][i],
#                     "height": data['height'][i]
#                 }
#             })
    
#     return results
