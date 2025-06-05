# File: /conosce-pdf-ocr-bow/src/conosce_pdf_bagwords_G.py

# -*- coding: utf-8 -*-
"""
Created on Sat Apr  3 01:31:38 2021

@author: tooru
"""

# Import libraries 
from PIL import Image 
import pytesseract 
import sys 
import os
from os import listdir
from os.path import isfile, join
import pandas as pd
import numpy as np
import re

from pdf2image import convert_from_path 
import urllib.request

import collections
from datetime import datetime

startTime = datetime.now()

# Path of packages 
pop_path = r'/usr/bin'  # Adjusted for Docker environment
pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'  # Adjusted for Docker environment

path = r'/app'  # Adjusted for Docker environment

path_data = path + r'/data/' 
path_pdf = path + r'/pdf/' 
path_txt = path + r'/text/'
path_tmp = path + r'/temp/'

'''
    A. Maestros   
'''

import chardet

with open(join(path_data,'padron_reducido_local_anexo.txt'), 'rb') as rawdata:
    encoding = chardet.detect(rawdata.read(10000)).get("encoding")
print(encoding)

padron_reducido = pd.read_csv(join(path_data,'padron_reducido_local_anexo.txt'), sep='|', encoding='ISO-8859-1', dtype=object)
try:    
    padron_reducido = padron_reducido[[' RUC','UBIGEO']]
except:
    padron_reducido = padron_reducido[['RUC','UBIGEO']]

padron_reducido.columns = ['RUC_PROVEEDOR', 'UBIGEO_PROVEEDOR']
padron_reducido.sort_values(['RUC_PROVEEDOR', 'UBIGEO_PROVEEDOR'], inplace=True)
padron_reducido = padron_reducido.drop_duplicates(subset='RUC_PROVEEDOR', keep='first')

entidades = pd.read_excel(join(path_data,'CONOSCE_CONVOCATORIAS2021_0.xlsx'), skiprows=1)
entidades = entidades[['CODIGOENTIDAD', 'ENTIDAD_RUC', 'ENTIDAD', 'TIPOENTIDAD','SECTOR']]
entidades = entidades.drop_duplicates()

'''
    X. PDF download from conosce-contratos url    
'''
df = pd.read_excel(join(path_data,'CONOSCE_CONTRATOS2021_0.xlsx'), skiprows=1)
df = df.rename(columns={'DOC_URL': 'URLCONTRATO'})
df['INDEX'] = df['URLCONTRATO'].str.replace('http://contratos.seace.gob.pe:9045/api/documentos/descargar/','')

merge_df = df
merge_df = pd.merge(merge_df, entidades, left_on='CODIGOENTIDAD', right_on='CODIGOENTIDAD', how='left')
merge_df = pd.merge(merge_df, padron_reducido, left_on='RUC_CONTRATISTA', right_on='RUC_PROVEEDOR', how='left')

merge_df.to_excel(join(path_data,'BDA_CONTRATOS_V4.xlsx'), index=False)

del merge_df
del padron_reducido
del entidades

'''
    I. PDF download from conosce-contratos url    
'''

data_list = df['URLCONTRATO'].tolist()
del df

pdf_list = [join(path_pdf,i) for i in listdir(path_pdf)]
pdf_list = [w.replace('.pdf', '') for w in pdf_list]
pdf_list = [w.replace(path_pdf, 'http://contratos.seace.gob.pe:9045/api/documentos/descargar/') for w in pdf_list]

# Lista de files que faltan descargar
todownload_list = set(data_list) - set(pdf_list)
todownload_list = list(todownload_list)

print(datetime.now() - startTime)
print('Start download')

a = 0
for i in todownload_list:
    a += 1
    print(a)
    pdf_name = i.rsplit('/', 1)[-1]
    print(i)
    try:
        urllib.request.urlretrieve(i, path_pdf + str(pdf_name) + '.pdf')
        print('download iter - ' + str(a))
        print(path_pdf + str(pdf_name) + '.pdf')
    except:
        print('failed download iter ' + str(a) + '- file - ' + str(pdf_name))
        
    print(datetime.now() - startTime)
    print('Corr of iter download - ' + str(a))

'''
    II. PDF to JPG to TXT
'''

os.chdir(path_tmp)

pdf_list = [join(path_pdf,i) for i in listdir(path_pdf)]
pdf_list = [w.replace(path_pdf, '') for w in pdf_list]
pdf_list = [w.replace('.pdf', '') for w in pdf_list]

parsed_list = [join(path_txt,i) for i in listdir(path_txt)]
parsed_list = [w.replace(path_txt, '') for w in parsed_list]
parsed_list = [w.replace('.txt', '') for w in parsed_list]

# Lista de files que faltan parsear
diff_list = set(pdf_list) - set(parsed_list)
diff_list = list(diff_list)

num_file = 0
for file in diff_list:
    num_file += 1
    PDF_file = path_pdf + file + '.pdf'
    outfile = path_txt + file + '.txt'   
    
    try:
        pages = convert_from_path(PDF_file, 500, poppler_path=pop_path) 
        
        image_counter = 1
        
        for page in pages: 
            filename = "page_" + str(image_counter) + ".jpg"
            page.save(filename, 'JPEG') 
            image_counter += 1
            print('success to JPG - ' + str(image_counter))

        filelimit = image_counter - 1
            
        f = open(outfile, "a") 
        
        for i in range(1, filelimit + 1): 
            filename = "page_" + str(i) + ".jpg"
            text = str(((pytesseract.image_to_string(Image.open(filename))))) 
            text = text.replace('-\n', '')     
            f.write(text) 
            print('success to tesseract')
            
        f.close() 
        print('success conversion')
    except:
        print('failed conversion')
        
    print('######### Filename: ' + str(file))
    print('######### script time - iter ' + str(num_file))
    print(outfile)
    print(datetime.now() - startTime)

'''
    III. TXT to structured dataframe
'''

txt_list = [join(path_txt,i) for i in listdir(path_txt)]
txt_list = [w.replace(path_txt, '') for w in txt_list]
txt_list = [w.replace('.txt', '') for w in txt_list] 
   
df_bow_append = pd.DataFrame()

num_file = 0
for file in txt_list:
    outfile = path_txt + file + '.txt'     
    print(outfile)
    
    try:
        df = pd.read_fwf(outfile, dtype=object, header=None)
        list_columns = df.columns
        df['file_name'] = file 
        df['columna_unica'] = ''
        for i in list_columns:
            df['columna_unica'] = df['columna_unica'].fillna('') + ' ' + df[i].fillna('')
        
        df['columna_unica'] = df['columna_unica'].str.upper()
        df['columna_unica'] = df['columna_unica'].str.replace('[^a-zA-Z0-9]', ' ')
        df['columna_unica'] = df['columna_unica'].str.strip()
        df['columna_unica'] = df['columna_unica'].str.replace('   ', ' ')
        df['columna_unica'] = df['columna_unica'].str.replace('  ', ' ')
    
        df = df[['file_name', 'columna_unica']]
        df = df.query('(columna_unica != "")')
        
        stop_words = ["ALGÚN","ALGUNA","ALGUNAS","ALGUNO","ALGUNOS","AMBOS","AMPLEAMOS","ANTE","ANTES","AQUEL",
                      "AQUELLAS","AQUELLOS","AQUI","ARRIBA","ATRAS","BAJO","BASTANTE","BIEN","CADA","CIERTA",
                      "CIERTAS","CIERTO","CIERTOS","COMO","CON","CONSEGUIMOS","CONSEGUIR","CONSIGO","CONSIGUE",
                      "CONSIGUEN","CONSIGUES","CUAL","CUANDO","DENTRO","DESDE","DONDE","DOS","EL","ELLAS","ELLOS",
                      "EMPLEAIS","EMPLEAN","EMPLEAR","EMPLEAS","EMPLEO","EN","ENCIMA","ENTONCES","ENTRE","ERA",
                      "ERAMOS","ERAN","ERAS","ERES","ES","ESTA","ESTABA","ESTADO","ESTAIS","ESTAMOS","ESTAN","ESTOY",
                      "FIN","FUE","FUERON","FUI","FUIMOS","GUENO","HA","HACE","HACEIS","HACEMOS","HACEN","HACER","HACES","HAGO",
                      "INCLUSO","INTENTA","INTENTAIS","INTENTAMOS","INTENTAN","INTENTAR","INTENTAS","INTENTO","IR","LA","LARGO",
                      "LAS","LO","LOS","MIENTRAS","MIO","MODO","MUCHOS","MUY","NOS","NOSOTROS","OTRO","PARA","PERO","PODEIS",
                      "PODEMOS","PODER","PODRIA","PODRIAIS","PODRIAMOS","PODRIAN","PODRIAS","POR","POR QUÉ","PORQUE","PRIMERO",
                      "PUEDE","PUEDEN","PUEDO","QUIEN","SABE","SABEIS","SABEMOS","SABEN","SABER","SABES","SER","SI","SIENDO",
                      "SIN","SOBRE","SOIS","SOLAMENTE","SOLO","SOMOS","SOY","SU","SUS","TAMBIÉN","TENEIS","TENEMOS","TENER",
                      "TENGO","TIEMPO","TIENE","TIENEN","TODO","TRABAJA","TRABAJAIS","TRABAJAMOS","TRABAJAN","TRABAJAR","TRABAJAS","TRABAJO",
                      "TRAS","TUYO","ULTIMO","UN","UNA","UNAS","UNO","UNOS","USA","USAIS","USAMOS","USAN","USAR","USAS","USO","VA","VAIS",
                      "VALOR","VAMOS","VAN","VAYA","VERDAD","VERDADERA","VERDADERO","VOSOTRAS","VOSOTROS","VOY","YO","ÉL",
                      "ÉSTA","ÉSTAS","ÉSTE","ÉSTOS","ÚLTIMA","ÚLTIMAS","ÚLTIMO","ÚLTIMOS","A","AÑADIÓ","AÚN","ACTUALMENTE","ADELANTE",
                      "ADEMÁS","AFIRMÓ","AGREGÓ","AHÍ","AHORA","AL","ALGO","ALREDEDOR","ANTERIOR","APENAS","APROXIMADAMENTE","AQUÍ","ASÍ",
                      "ASEGURÓ","AUNQUE","AYER","BUEN","BUENA","BUENAS","BUENO","BUENOS","CÓMO","CASI","CERCA","CINCO","COMENTÓ","CONOCER",
                      "CONSIDERÓ","CONSIDERA","CONTRA","COSAS","CREO","CUALES","CUALQUIER","CUANTO","CUATRO","CUENTA","DA","DADO","DAN","DAR",
                      "DE","DEBE","DEBEN","DEBIDO","DECIR","DEJÓ","DEL","DEMÁS","DESPUÉS","DICE","DICEN","DICHO","DIERON","DIFERENTE","DIFERENTES",
                      "DIJERON","DIJO","DIO","DURANTE","E","EJEMPLO","ELLA","ELLO","EMBARGO","ENCUENTRA","ESA","ESAS","ESE","ESO","ESOS",
                      "ESTÁ","ESTÁN","ESTABAN","ESTAR","ESTARÁ","ESTAS","ESTE","ESTO","ESTOS","ESTUVO","EX","EXISTE","EXISTEN","EXPLICÓ",
                      "EXPRESÓ","FUERA","GRAN","GRANDES","HABÍA","HABÍAN","HABER","HABRÁ","HACERLO","HACIA","HACIENDO","HAN","HASTA","HAY","HAYA",
                      "HE","HECHO","HEMOS","HICIERON","HIZO","HOY","HUBO","IGUAL","INDICÓ","INFORMÓ","JUNTO","LADO","LE","LES","LLEGÓ",
                      "LLEVA","LLEVAR","LUEGO","LUGAR","MÁS","MANERA","MANIFESTÓ","MAYOR","ME","MEDIANTE","MEJOR","MENCIONÓ","MENOS",
                      "MI","MISMA","MISMAS","MISMO","MISMOS","MOMENTO","MUCHA","MUCHAS","MUCHO","NADA","NADIE","NI",
                      "NINGÚN","NINGUNA","NINGUNAS","NINGUNO","NINGUNOS","NO","NOSOTRAS","NUESTRA","NUESTRAS","NUESTRO","NUESTROS",
                      "NUEVA","NUEVAS","NUEVO","NUEVOS","NUNCA","O","OCHO","OTRA","OTRAS","OTROS","PARECE","PARTE","PARTIR","PASADA","PASADO",
                      "PESAR","POCA","POCAS","POCO","POCOS","PODRÁ","PODRÁN","PODRÍA","PODRÍAN","PONER","POSIBLE","PRÓXIMO","PRÓXIMOS",
                      "PRIMER","PRIMERA","PRIMEROS","PRINCIPALMENTE","PROPIA","PROPIAS","PROPIO","PROPIOS","PUDO","PUEDA","PUES","QUÉ","QUE",
                      "QUEDÓ","QUEREMOS","QUIÉN","QUIENES","QUIERE","REALIZÓ","REALIZADO","REALIZAR","RESPECTO","SÍ","SÓLO","SE","SEÑALÓ",
                      "SEA","SEAN","SEGÚN","SEGUNDA","SEGUNDO","SEIS","SERÁ","SERÁN","SERÍA","SIDO","SIEMPRE","SIETE","SIGUE","SIGUIENTE","SINO",
                      "SOLA","SOLAS","SOLOS","SON","TAL","TAMPOCO","TAN","TANTO","TENÍA","TENDRÁ","TENDRÁN","TENGA","TENIDO","TERCERA",
                      "TODA","TODAS","TODAVÍA","TODOS","TOTAL","TRATA","TRAVÉS","TRES","TUVO","USTED","VARIAS","VARIOS","VECES",
                      "VER","VEZ","Y","YA",
                      "DE"]
        
        df['cu_wo_sw'] = df['columna_unica']
        df['cu_wo_sw'] = [' '.join([item for item in x.split() 
                      if item not in stop_words]) 
                      for x in df['columna_unica']]
                
        df['line_text'] = range(1, len(df) + 1)
        
        df_bow = collections.Counter([y for x in df.cu_wo_sw.values.flatten() for y in x.split()])
        df_bow = pd.DataFrame.from_dict(df_bow, orient='index')
        df_bow.reset_index(level=0, inplace=True)
        df_bow.columns = ['bow', 'freq']
        df_bow['file_name'] = file
        df_bow['len'] = df_bow['bow'].str.len()
    
        df_bow_append = df_bow_append.append(df_bow)
        del df
        del df_bow
        
    except:
        print('Error parsing txt')
    
df_bow_append.to_excel(join(path_data,'bow_contratos.xlsx'), index=False)