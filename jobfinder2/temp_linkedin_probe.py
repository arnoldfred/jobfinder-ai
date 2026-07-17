import requests
url='https://www.linkedin.com/jobs/search/?keywords=developer&location=C%C3%B4te%20d%27Ivoire'
for headers in [None, {'User-Agent':'Mozilla/5.0'}, {'User-Agent':'Mozilla/5.0','Accept-Language':'fr-FR,fr;q=0.9,en;q=0.8'}]:
    try:
        r=requests.get(url, headers=headers, timeout=25, allow_redirects=True)
        print('headers', headers, 'status', r.status_code, 'final', r.url)
        print(r.text[:500])
        print('---')
    except Exception as e:
        print('ERR', e)
