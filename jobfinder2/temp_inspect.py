import requests
from bs4 import BeautifulSoup
urls = [
    'https://agenceemploijeunes.ci/offres-emploi/PRES-176670-07-2026',
    'https://agenceemploijeunes.ci/offres-emploi/PRES-176670-07-2026/',
    'https://agenceemploijeunes.ci/site/offres-emplois/PRES-176670-07-2026',
    'https://agenceemploijeunes.ci/site/offres-emploi/PRES-176670-07-2026'
]
for u in urls:
    try:
        r=requests.get(u, timeout=20, headers={'User-Agent':'Mozilla/5.0'})
        print('URL', u)
        print('STATUS', r.status_code, 'FINAL', r.url)
        print(r.text[:1000])
        print('---')
    except Exception as e:
        print('ERR', u, e)
