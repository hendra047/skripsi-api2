import re
import os
import sys
import requests
import random
import pikepdf
import json
from serpapi import GoogleSearch
from PyPDF2 import PdfReader
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/crawl', methods=['POST'])
def index():
    try:
        # Mendapatkan data dari PHP
        data_json = request.get_json()
        data = data_json['data']
        
        file_api_key = open('api_key.txt', 'r').readlines()

        idx = int(file_api_key[0])
        total_api_key = len(file_api_key) - 1

        api_key = file_api_key[idx + 1].strip("\n")

        # Menyiapkan parameter untuk google search
        # params = {
        #     'q': data,
        #     'engine': 'google_scholar',
        #     'type': 'search',
        #     'api_key': 'f44ba1c22c640b77c37c48bb0fecb64473566280c3287583aeb77d68bca5b8ae'
        # }
        
        output = ''
        while idx < total_api_key:
            params = {
                'q': data,
                'engine': 'google_scholar',
                'type': 'search',
                'api_key': api_key
            }
        
            # Melakukan search ke Google Scholar
            google_scholar = GoogleSearch(params)
            result = google_scholar.get_dict()
            
            if ('error' in result.keys()):
                if ('your searches for the month are exhausted' in result['error'].lower()):
                    if (idx + 1 >= total_api_key): break
                    idx += 1
                    api_key = file_api_key[idx + 1].strip("\n")
                    continue
            organic_results = result['organic_results'] if 'organic_results' in result.keys() else ''
            
            if (organic_results != ''):
                highest_cited = -1
                highest_link_pdf_cited = ''
                for item in organic_results:
                    cited_by = item['inline_links']['cited_by']['total'] if 'cited_by' in item['inline_links'].keys() else -1 
                    link = item['link'] if 'link' in item.keys() else ''
                    link_pdf = item['resources'][0]['link'] if 'resources' in item.keys() else ''

                    # Memberikan nilai awalan pada highest_cited dan highest_link_pdf_cited
                    if (highest_cited == -1):
                        highest_cited = 0
                        highest_link_pdf_cited = link_pdf

                    # Data akan diambil jika:
                    # - link tidak mengandung kata-kata "repository"
                    # - cited_by sekarang lebih besar dari highest_cited
                    # - link_pdf tidak kosong
                    if ('repository' not in link and cited_by > highest_cited and link_pdf != ''):
                        highest_cited = cited_by
                        highest_link_pdf_cited = link_pdf
                
                try:
                    if (highest_link_pdf_cited != ''):
                        # Menghapus "temp.pdf"
                        if (os.path.exists('temp.pdf')):
                            os.remove('temp.pdf')
                            
                        # Menghapus "temp2.pdf"
                        if (os.path.exists('temp2.pdf')):
                            os.remove('temp2.pdf')

                        # Mengambil user-agent random
                        user_agents = requests.get('http://headers.scrapeops.io/v1/user-agents', params={
                            'api_key': '1231a208-40b9-43ab-b0eb-9534be6d35a6'
                        })
                        
                        # Mengambil data dari highest_link_pdf_cited
                        pdf_file = requests.get(highest_link_pdf_cited, 
                                                headers={"user-agent":user_agents.json()['result'][random.randint(0, 9)]})
                                    
                        # Nama file pdf yang di download            
                        filename = "temp.pdf"
                        
                        # Download PDF
                        file = open(filename, "wb")
                        file.write(pdf_file.content)
                        file.close()

                        # Check if pdf secured or not
                        if (PdfReader(filename).is_encrypted):
                            # Menyimpan ulang PDF agar dapat dibaca
                            pdf = pikepdf.open(filename)
                            
                            # Menyimpan dengan nama yang berbeda
                            filename = "temp2.pdf"
                            pdf.save(filename)
                        
                        try:
                            # Membaca PDF
                            reader = PdfReader(filename, strict=False)
                            num_pages = reader.getNumPages()
                        except:
                            # Menyimpan ulang PDF agar dapat dibaca
                            pdf = pikepdf.open(filename)
                            
                            # Menyimpan dengan nama yang berbeda
                            filename = "temp2.pdf"
                            pdf.save(filename)
                            
                            # Membaca ulang PDF yang telah disimpan dengan berbeda nama
                            reader = PdfReader(filename, strict=False)
                            num_pages = reader.getNumPages()
                            

                        # Mencari keyword/kata kunci dari pdf
                        for i in range(0, num_pages):
                            page = reader.getPage(i)
                            page_text = json.dumps(page.extractText().lower().replace(" ,", ","))

                            keyterm = "\n*?((k\*?e\s*?y\s*?w\s*?o\s*?r\s*?d\s*?s?)|(kata\s*?kunci))\s*?:?.*?(?=\.{1,})"
                            search_keyword = re.search(keyterm, page_text)
                            if (search_keyword != None):
                                keyword = re.sub('(k\*?e\s*?y\s*?w\s*?o\s*?r\s*?d\s*?s?)|(k\s*?a\s*?t\s*?a\s*?k\s*?u\s*?n\s*?c\s*?i\s*?)|(:)|(")|(\[)|(\])|(\n)|(\')|(\.)|(—)', '',search_keyword.group(0))
                                if (not re.match(r'^(k\*?e\s*?y\s*?w\s*?o\s*?r\s*?d\s*?s?)|(k\s*?a\s*?t\s*?a\s*?k\s*?u\s*?n\s*?c\s*?i\s*?)$', keyword)):
                                    output = keyword
                                    break
                                    # return jsonify({"keyword": keyword})
                        break
                except:
                    output = ''
                    # return jsonify({"keyword": None})
                    # return jsonify({"keyword": sys.exc_info()})
                break
            else:
                output = ''
                # return jsonify({"keyword": None})
            break
            
        with open('api_key.txt', 'w') as file_save:
            file_api_key[0] = str(idx) + "\n"
            file_save.writelines(file_api_key)
            
        return jsonify({"keyword": output})
    except:
        return jsonify({"keyword": ''})
        # return jsonify({"keyword": sys.exc_info()})

if __name__ == '__main__':
    app.run(debug=True, port=os.getenv("PORT", default=5000))