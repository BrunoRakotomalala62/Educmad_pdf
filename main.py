import requests
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify, send_file
import re
import os
from weasyprint import HTML
import io

app = Flask(__name__)

# Configuration des IDs de cours par matière et série
# Ces IDs ont été extraits par exploration du site EducMad
COURSE_MAP = {
    "physique": {
        "A": 819,
        "C": 820,
        "D": 821
    },
    "maths": {
        "A": 128,
        "C": 129,
        "D": 127,
        "L": 618,
        "S": 620,
        "OSE": 619
    },
    "svt": {
        "A": 822,
        "C": 823,
        "D": 824
    },
    "hg": {
        "A": 132,
        "C": 132,
        "D": 132,
        "L": 132,
        "S": 132
    },
    "philo": {
        "A": 131,
        "C": 131,
        "D": 131,
        "L": 131
    },
    "malagasy": {
        "A": 130,
        "C": 130,
        "D": 130,
        "S": 130,
        "OSE": 130
    },
    "francais": {
        "A": 125,
        "C": 125,
        "D": 125
    },
    "anglais": {
        "A": 126,
        "C": 126,
        "D": 126
    }
}

# Alias pour faciliter la recherche
ALIASES = {
    "physique-chimie": "physique",
    "pc": "physique",
    "mathematiques": "maths",
    "math": "maths",
    "histoire-geographie": "hg",
    "histoire-geo": "hg",
    "philosophie": "philo",
    "français": "francais"
}

def get_course_id(sujet, serie):
    sujet = ALIASES.get(sujet, sujet)
    if sujet in COURSE_MAP:
        return COURSE_MAP[sujet].get(serie)
    return None

def get_pdf_links(course_id, doc_type, serie):
    # Dans la plupart des cours EducMad :
    # Section 1 ou 2 = Énoncés
    # Section 2 ou 3 = Corrigés
    # On va scanner toutes les sections pour être sûr, ou cibler intelligemment
    
    all_links = []
    # On scanne les sections probables (1 à 4)
    for section_id in range(1, 5):
        url = f"http://mediatheque.accesmad.org/educmad/course/view.php?id={course_id}&section={section_id}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code != 200: continue
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Vérifier si la section correspond au type demandé (énoncé ou correction)
            section_title = soup.select_one(f"#section-{section_id} h3")
            section_text = section_title.get_text().lower() if section_title else ""
            
            # Si on cherche des corrections et que la section ne mentionne pas "corrigé" ou "correction", on ignore
            # Sauf si c'est la seule section trouvée
            is_correction_section = "corrig" in section_text or "correction" in section_text
            is_enonce_section = "énoncé" in section_text or "enonce" in section_text or "sujet" in section_text
            
            if doc_type == "correction" and not is_correction_section and (is_enonce_section):
                continue
            if doc_type == "enonce" and is_correction_section:
                continue

            activities = soup.find_all('a', href=re.compile(r'mod/(resource|page)/view\.php\?id=\d+'))
            for a in activities:
                title = a.get_text(strip=True)
                href = a.get('href')
                
                # Filtrage par type dans le titre si la section est ambiguë
                if doc_type == "correction" and "corrig" not in title.lower() and "correction" not in title.lower() and not is_correction_section:
                    continue
                if doc_type == "enonce" and ("corrig" in title.lower() or "correction" in title.lower()) and not is_enonce_section:
                    continue
                
                # FILTRAGE PAR SÉRIE
                # On vérifie si le titre mentionne une autre série que celle demandée
                # Si on demande "A", et que le titre dit "C" ou "D" ou "S" sans mentionner "A", on rejette
                title_clean = title.upper()
                series_to_check = ["A", "C", "D", "L", "S", "OSE"]
                other_series = [s for s in series_to_check if s != serie]
                
                # Cas spécial "CD" ou "C-D"
                if serie in ["C", "D"]:
                    # Si on cherche C ou D, on accepte les titres qui mentionnent C, D ou CD
                    is_valid_serie = any(s in title_clean for s in [serie, "CD", "C-D"])
                else:
                    # Pour les autres, on vérifie que la série demandée est présente
                    # ou qu'aucune autre série spécifique n'est mentionnée
                    is_valid_serie = serie in title_clean or not any(s in title_clean for s in other_series)

                if not is_valid_serie:
                    continue

                title = title.replace("Sélectionner l’activité", "").replace("Fichier", "").replace("Page", "").strip()
                year_match = re.search(r'(199\d|20[0-2]\d)', title)
                year = int(year_match.group(1)) if year_match else None
                
                if href and year and 1999 <= year <= 2023:
                    is_page = "mod/page/" in href
                    final_url = href
                    if is_page:
                        module_id = re.search(r'id=(\d+)', href).group(1)
                        final_url = f"/convert_to_pdf?id={module_id}&title={title.replace(' ', '_')}"

                    if not any(l['url'] == final_url for l in all_links):
                        all_links.append({"titre": title, "url": final_url, "annee": year})
        except:
            continue
            
    all_links.sort(key=lambda x: x['annee'], reverse=True)
    return all_links

@app.route('/recherche', methods=['GET'])
def recherche():
    sujet = request.args.get('sujet', '').lower()
    serie = request.args.get('serie', '').upper()
    doc_type = request.args.get('type', 'enonce').lower()
    
    course_id = get_course_id(sujet, serie)
    if not course_id:
        return jsonify({"error": f"Combinaison sujet '{sujet}' et série '{serie}' non trouvée."}), 404

    data = get_pdf_links(course_id, doc_type, serie)
    base_host = request.host_url.rstrip('/')
    
    results = []
    for item in data:
        url = item["url"]
        if url.startswith('/convert_to_pdf'):
            url = base_host + url
        results.append({"titre": item["titre"], "url": url})
    
    return jsonify(results)

@app.route('/convert_to_pdf', methods=['GET'])
def convert_to_pdf():
    module_id = request.args.get('id')
    title = request.args.get('title', 'document')
    target_url = f"http://mediatheque.accesmad.org/educmad/mod/page/view.php?id={module_id}"
    try:
        response = requests.get(target_url, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        content = soup.select_one('.generalbox') or soup.select_one('#region-main')
        if not content: return "Contenu non trouvé", 404
        
        html_content = f"<html><head><meta charset='UTF-8'><style>body{{font-family:Arial;margin:40px;}}img{{max-width:100%;}}</style></head><body>{content.decode_contents()}</body></html>"
        pdf_file = io.BytesIO()
        HTML(string=html_content, base_url="http://mediatheque.accesmad.org").write_pdf(pdf_file)
        pdf_file.seek(0)
        return send_file(pdf_file, mimetype='application/pdf', as_attachment=True, download_name=f"{title}.pdf")
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
