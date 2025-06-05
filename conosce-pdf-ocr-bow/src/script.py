# -*- coding: utf-8 -*-
"""
Conosce PDF OCR BOW - Modular Version
"""

import os
from os import listdir
from os.path import isfile, join
import pandas as pd
import numpy as np
import re
import chardet
import urllib.request
from PIL import Image
import pytesseract
from pdf2image import convert_from_path
import collections
from datetime import datetime

# --- Configuration ---
POPPLER_PATH = '/usr/bin'
TESSERACT_CMD = '/usr/bin/tesseract'
BASE_PATH = '/app'
PATH_DATA = BASE_PATH + '/data/'
PATH_PDF = BASE_PATH + '/pdf/'
PATH_TXT = BASE_PATH + '/text/'
PATH_TMP = BASE_PATH + '/temp/'

pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

# --- Utility Functions ---

def detect_encoding(filepath):
    with open(filepath, 'rb') as rawdata:
        return chardet.detect(rawdata.read(10000)).get("encoding")

def read_padron_reducido(filepath):
    encoding = detect_encoding(filepath)
    print(f"Detected encoding: {encoding}")
    df = pd.read_csv(filepath, sep='|', encoding='ISO-8859-1', dtype=object)
    try:
        df = df[[' RUC', 'UBIGEO']]
    except KeyError:
        df = df[['RUC', 'UBIGEO']]
    df.columns = ['RUC_PROVEEDOR', 'UBIGEO_PROVEEDOR']
    df.sort_values(['RUC_PROVEEDOR', 'UBIGEO_PROVEEDOR'], inplace=True)
    df = df.drop_duplicates(subset='RUC_PROVEEDOR', keep='first')
    return df

def read_entidades(filepath):
    df = pd.read_excel(filepath, skiprows=1)
    df = df[['CODIGOENTIDAD', 'ENTIDAD_RUC', 'ENTIDAD', 'TIPOENTIDAD', 'SECTOR']]
    return df.drop_duplicates()

def merge_data(df, entidades, padron_reducido):
    df = pd.merge(df, entidades, left_on='CODIGOENTIDAD', right_on='CODIGOENTIDAD', how='left')
    df = pd.merge(df, padron_reducido, left_on='RUC_CONTRATISTA', right_on='RUC_PROVEEDOR', how='left')
    return df

def download_pdfs(data_list, path_pdf):
    pdf_list = [join(path_pdf, i) for i in listdir(path_pdf)]
    pdf_list = [w.replace('.pdf', '') for w in pdf_list]
    pdf_list = [w.replace(path_pdf, 'http://contratos.seace.gob.pe:9045/api/documentos/descargar/') for w in pdf_list]
    todownload_list = list(set(data_list) - set(pdf_list))
    print(f"PDFs to download: {len(todownload_list)}")
    for idx, url in enumerate(todownload_list, 1):
        pdf_name = url.rsplit('/', 1)[-1]
        try:
            urllib.request.urlretrieve(url, path_pdf + str(pdf_name) + '.pdf')
            print(f"[{idx}/{len(todownload_list)}] Downloaded: {pdf_name}")
        except Exception as e:
            print(f"[{idx}/{len(todownload_list)}] Failed: {pdf_name} ({e})")

def pdf_to_txt(path_pdf, path_txt, path_tmp, poppler_path):
    os.chdir(path_tmp)
    pdf_list = [join(path_pdf, i) for i in listdir(path_pdf)]
    pdf_list = [w.replace(path_pdf, '').replace('.pdf', '') for w in pdf_list]
    parsed_list = [join(path_txt, i) for i in listdir(path_txt)]
    parsed_list = [w.replace(path_txt, '').replace('.txt', '') for w in parsed_list]
    diff_list = list(set(pdf_list) - set(parsed_list))
    for idx, file in enumerate(diff_list, 1):
        PDF_file = path_pdf + file + '.pdf'
        outfile = path_txt + file + '.txt'
        try:
            pages = convert_from_path(PDF_file, 500, poppler_path=poppler_path)
            for i, page in enumerate(pages, 1):
                filename = f"page_{i}.jpg"
                page.save(filename, 'JPEG')
            with open(outfile, "a") as f:
                for i in range(1, len(pages) + 1):
                    filename = f"page_{i}.jpg"
                    text = pytesseract.image_to_string(Image.open(filename)).replace('-\n', '')
                    f.write(text)
            print(f"[{idx}/{len(diff_list)}] Converted: {file}")
        except Exception as e:
            print(f"[{idx}/{len(diff_list)}] Failed: {file} ({e})")

def clean_text_column(df, col='columna_unica'):
    df[col] = df[col].str.upper()
    df[col] = df[col].str.replace('[^a-zA-Z0-9]', ' ', regex=True)
    df[col] = df[col].str.strip()
    df[col] = df[col].str.replace('   ', ' ', regex=False)
    df[col] = df[col].str.replace('  ', ' ', regex=False)
    return df

def txt_to_bow(path_txt, path_data):
    txt_list = [join(path_txt, i) for i in listdir(path_txt)]
    txt_list = [w.replace(path_txt, '').replace('.txt', '') for w in txt_list]
    df_bow_append = pd.DataFrame()
    stop_words = set([
        # ... (same stop words as before, truncated for brevity) ...
        "DE"
    ])
    for idx, file in enumerate(txt_list, 1):
        outfile = path_txt + file + '.txt'
        try:
            df = pd.read_fwf(outfile, dtype=object, header=None)
            list_columns = df.columns
            df['file_name'] = file
            df['columna_unica'] = ''
            for i in list_columns:
                df['columna_unica'] = df['columna_unica'].fillna('') + ' ' + df[i].fillna('')
            df = clean_text_column(df, 'columna_unica')
            df = df[['file_name', 'columna_unica']]
            df = df.query('(columna_unica != "")')
            df['cu_wo_sw'] = [
                ' '.join([item for item in x.split() if item not in stop_words])
                for x in df['columna_unica']
            ]
            df['line_text'] = range(1, len(df) + 1)
            df_bow = collections.Counter(
                [y for x in df.cu_wo_sw.values.flatten() for y in x.split()]
            )
            df_bow = pd.DataFrame.from_dict(df_bow, orient='index')
            df_bow.reset_index(level=0, inplace=True)
            df_bow.columns = ['bow', 'freq']
            df_bow['file_name'] = file
            df_bow['len'] = df_bow['bow'].str.len()
            df_bow_append = pd.concat([df_bow_append, df_bow], ignore_index=True)
            print(f"[{idx}/{len(txt_list)}] Parsed: {file}")
        except Exception as e:
            print(f"[{idx}/{len(txt_list)}] Error parsing {file}: {e}")
    df_bow_append.to_excel(join(path_data, 'bow_contratos.xlsx'), index=False)

# --- Main Pipeline ---

def main():
    startTime = datetime.now()
    # Step 1: Load data
    padron_reducido = read_padron_reducido(join(PATH_DATA, 'padron_reducido_local_anexo.txt'))
    entidades = read_entidades(join(PATH_DATA, 'CONOSCE_CONVOCATORIAS2021_0.xlsx'))
    df = pd.read_excel(join(PATH_DATA, 'CONOSCE_CONTRATOS2021_0.xlsx'), skiprows=1)
    df = df.rename(columns={'DOC_URL': 'URLCONTRATO'})
    df['INDEX'] = df['URLCONTRATO'].str.replace(
        'http://contratos.seace.gob.pe:9045/api/documentos/descargar/', '')
    merge_df = merge_data(df, entidades, padron_reducido)
    merge_df.to_excel(join(PATH_DATA, 'BDA_CONTRATOS_V4.xlsx'), index=False)
    data_list = df['URLCONTRATO'].tolist()
    print(f"Step 1 done: Data loaded and merged. Time: {datetime.now() - startTime}")

    # Step 2: Download PDFs
    download_pdfs(data_list, PATH_PDF)
    print(f"Step 2 done: PDFs downloaded. Time: {datetime.now() - startTime}")

    # Step 3: Convert PDFs to TXT
    pdf_to_txt(PATH_PDF, PATH_TXT, PATH_TMP, POPPLER_PATH)
    print(f"Step 3 done: PDFs converted to TXT. Time: {datetime.now() - startTime}")

    # Step 4: TXT to Bag of Words
    txt_to_bow(PATH_TXT, PATH_DATA)
    print(f"Step 4 done: Bag of Words created. Time: {datetime.now() - startTime}")

if __name__ == "__main__":
    main()