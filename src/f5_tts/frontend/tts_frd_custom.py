import os
import re
import zipfile

import ttsfrd
from modelscope.hub.file_download import model_file_download

from f5_tts.frontend.frontend_utils import contains_chinese, replace_blank, replace_corner_mark, remove_bracket, spell_out_number, split_paragraph


def download_and_extract_zip(repo_id, zip_filename, target_dir):
    os.makedirs(target_dir, exist_ok=True)

    # 下載 zip
    zip_path = model_file_download(model_id=repo_id,file_path=zip_filename, revision='master')
    print(f"Downloaded: {zip_path}")

    # 解壓
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(target_dir)
    print(f"Extracted to: {target_dir}")

    # 刪掉 zip
    os.remove(zip_path)
    print(f"Deleted zip file: {zip_path}")

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(ROOT_DIR, "kantts-ttsfrd")

repo_id = "speech_tts/speech_kantts_ttsfrd"
zip_filename = "resource.zip"

if not os.path.exists(MODEL_DIR):
    download_and_extract_zip(repo_id, zip_filename, MODEL_DIR)

frd = ttsfrd.TtsFrontendEngine()
assert frd.initialize(f'{MODEL_DIR}/resource') is True, 'failed to initialize ttsfrd resource'
frd.set_lang_type('pinyin')
frd.enable_pinyin_mix(True)
frd.set_breakmodel_index(1)

####new normalize
def text_normalize_new(text):
    text = text.strip()
    def split_by_brackets(input_string):
        # Use regex to find text inside and outside the brackets
        inside_brackets = re.findall(r'\[(.*?)\]', input_string)
        outside_brackets = re.split(r'\[.*?\]', input_string)
        
        # Filter out empty strings from the outside list (result of consecutive brackets)
        outside_brackets = [part for part in outside_brackets if part]
        
        return inside_brackets, outside_brackets
    
    def text_normalize_no_split(text, is_last=False):
        text = text.strip()
        text_is_terminated = text[-1] == "。"
        if contains_chinese(text):
            #print(text)
            text = frd.get_frd_extra_info(text, 'input')

            # 特殊處理
            text = text.replace('万', '萬')
            text = text.replace('~', '到')
            text = text.replace('/', ' ')
            text = text.replace(':', ' ')

            if not text_is_terminated and not is_last:
                text = text[:-1]
            #print(text)
            text = text.replace("\n", "")
            text = replace_blank(text)
            text = replace_corner_mark(text)
            text = text.replace(".", "、")
            #print(text)
            text = text.replace(" - ", "，")
            #print(text)
            text = remove_bracket(text)
            #print(text)
            text = re.sub(r'[，,]+$', '。', text)
            #print(text)
        
        return text
    
    def join_interleaved(outside, inside):
        # Ensure the number of parts match between outside and inside
        result = []
        
        # Iterate and combine alternating parts
        for o, i in zip(outside, inside):
            result.append(o + '[' + i + ']')
        
        # Append any remaining part (if outside is longer than inside)
        if len(outside) > len(inside):
            result.append(outside[-1])
        
        return ''.join(result)
    inside_brackets, outside_brackets = split_by_brackets(text)
    #print("io",inside_brackets, outside_brackets)
    #text = re.sub(r'(\[[^\]]*\])(.*?)', normalize_outside_brackets, text)
    #print(text)
    for n in range(len(outside_brackets)):
        e_out = text_normalize_no_split(outside_brackets[n],is_last = n == len(outside_brackets) - 1)
        outside_brackets[n] = e_out
        
    text = join_interleaved(outside_brackets, inside_brackets)

    return text

if __name__ == '__main__':
    ref_text = """您選擇投保本商品的繳別為躉繳；幣別為新臺幣；基
本保額設定為36,000元；本次繳交保費
為360,000元，請問
要保人：陳歐文 是否正確?
被保險人：陳歐文 是否正確?
繳款人：陳歐文 是否正確?"""
    ref_text = text_normalize_new(ref_text)
    print(ref_text)