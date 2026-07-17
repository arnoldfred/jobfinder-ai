"""
JobFinder AI — Scraper d'offres d'emploi ivoiriennes
Sources:
  1. agenceemploijeunes.ci (AEJI) — offres gouvernementales vérifiées
  2. annonces.abidjan.net — plus grand site d'annonces de Côte d'Ivoire
"""
import re
import time
import logging
import hashlib
import random
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from django.utils import timezone

logger = logging.getLogger(__name__)

# ─── User-Agents rotatifs ─────────────────────────────────────────────────────
UA_LIST = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
]

def _get_headers(referer=None):
    h = {
        'User-Agent': random.choice(UA_LIST),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Upgrade-Insecure-Requests': '1',
    }
    if referer:
        h['Referer'] = referer
    return h


def _normalize_absolute_url(url, base_url):
    if not url:
        return ''
    value = str(url).strip()
    if not value:
        return ''
    if value.startswith('//'):
        value = f'https:{value}'
    if value.startswith(('http://', 'https://')):
        return value
    if value.startswith('/'):
        return f'{base_url.rstrip("/")}{value}'
    return f'{base_url.rstrip("/")}/{value.lstrip("/")}'


def _normalize_aeji_offer_url(url, fallback_reference=None):
    if not url:
        return ''

    normalized = _normalize_absolute_url(url, BASE_AEJI)
    parsed = urlparse(normalized)
    host = parsed.netloc.lower().replace('www.', '')
    if host != 'agenceemploijeunes.ci':
        return normalized

    parts = [p for p in parsed.path.split('/') if p]
    candidate = None
    for idx, part in enumerate(parts):
        if part in {'offres-emploi', 'offres-emplois'} and idx + 1 < len(parts):
            slug = parts[idx + 1]
            if slug and slug not in {'site', 'offres-emploi', 'offres-emplois'}:
                candidate = slug
                break

    if candidate:
        return f'{BASE_AEJI}/offres-emploi/{candidate}'

    if fallback_reference:
        ref = str(fallback_reference).strip()
        if ref and ref not in {'site', 'offres-emploi', 'offres-emplois'}:
            return f'{BASE_AEJI}/offres-emploi/{ref}'

    return ''


def _extract_offer_links_from_html(html, source='aeji'):
    soup = BeautifulSoup(html, 'html.parser')
    links = []
    seen = set()

    for a in soup.find_all('a', href=True):
        href = a['href']
        if not href:
            continue

        if source == 'aeji':
            if not re.search(r'/offres-emploi(?:s)?/[^/?#]+', href):
                continue
            normalized = _normalize_aeji_offer_url(href)
            if not normalized:
                continue
        else:
            link_text = a.get_text(' ', strip=True).lower()
            if not re.search(r'/emplois/\d+/details/[^/?#]+', href):
                continue
            if any(x in link_text for x in ['annonces', 'emplois', 'connexion', 'inscription', 'ajout', 'favori']):
                if link_text in {'emplois', 'annonces', 'ajouter'}:
                    continue
            normalized = _normalize_absolute_url(href, BASE_ABJ)

        if normalized not in seen:
            seen.add(normalized)
            links.append(normalized)

    return links


def _fetch(url, timeout=20, retries=2, referer=None, headers=None, params=None):
    """GET robuste avec retry et rotation UA."""
    for attempt in range(retries + 1):
        try:
            req_headers = _get_headers(referer)
            if headers:
                req_headers.update(headers)
            r = requests.get(url, headers=req_headers, timeout=timeout,
                             allow_redirects=True, params=params)
            if r.status_code == 200:
                return r
            if 'linkedin.com' in url and r.status_code in {403, 429, 999}:
                fallback_headers = {'User-Agent': 'Mozilla/5.0'}
                r2 = requests.get(url, headers=fallback_headers, timeout=timeout,
                                  allow_redirects=True, params=params)
                if r2.status_code == 200:
                    return r2
            if r.status_code == 429:
                time.sleep(random.uniform(10, 20))
            elif r.status_code >= 500:
                time.sleep(random.uniform(2, 4))
            else:
                logger.debug('Fetch %s -> HTTP %s', url, r.status_code)
                return None
        except requests.exceptions.Timeout:
            time.sleep(random.uniform(1, 3))
        except Exception as e:
            logger.debug('Fetch error %s: %s', url, e)
            return None
    return None


def _fetch_json(url, timeout=20, retries=2, referer=None, params=None, headers=None):
    r = _fetch(url, timeout=timeout, retries=retries,
               referer=referer, headers=headers, params=params)
    if not r:
        return None
    try:
        return r.json()
    except ValueError:
        logger.debug('Fetch JSON parse error %s', url)
        return None


def _sleep(mn=0.8, mx=2.0):
    time.sleep(random.uniform(mn, mx))


def _make_id(prefix, text):
    slug = text.rstrip('/').split('/')[-1]
    slug = re.sub(r'[^a-zA-Z0-9_-]', '', slug)[:50]
    if len(slug) < 3:
        slug = hashlib.md5(text.encode()).hexdigest()[:12]
    return f'{prefix}_{slug}'


def _guess_domain(title):
    t = title.lower()
    mapping = {
        'it':        ['développeur','developer','dev ','software','informatique','système','réseau',
                      'web','mobile','data','python','java','php','sql','cloud','devops','tech','it '],
        'data':      ['data','analyse','analyste','analytique','statistique','bi ','tableau',
                      'reporting','kpi','machine learning','ia ','intelligence artificielle'],
        'finance':   ['finance','financier','comptable','comptabilité','audit','fiscal','trésor',
                      'contrôleur','budget','bilan','daf','directeur financier','analyste financier'],
        'marketing': ['marketing','communication','digital','brand','community','media','publicité',
                      'chargé de communication','seo','réseaux sociaux'],
        'rh':        ['rh ','recrutement','ressources humaines','drh','talent','paie','formation',
                      'gpec','sirh','responsable rh','chargé rh'],
        'design':    ['design','graphiste','ux','ui','créatif','artistique','infographiste',
                      'webdesign','motion','illustrateur'],
        'sante':     ['santé','médecin','infirmier','pharmacien','hôpital','clinique',
                      'médical','biolo','chirurgien'],
        'btp':       ['btp','génie civil','architecte','ingénieur travaux','construction',
                      'bâtiment','topographe','conducteur de travaux','chantier'],
        'commerce':  ['commercial','vente','business développ','acheteur','supply','logistique',
                      'export','trade','chargé de clientèle','responsable commercial'],
        'juridique': ['juriste','avocat','juridique','droit','légal','compliance','notaire'],
        'education': ['enseignant','professeur','formateur','éducation','école',
                      'académique','pédagogue'],
    }
    for domain, kws in mapping.items():
        if any(k in t for k in kws):
            return domain
    return 'autre'


def _guess_job_type(text):
    t = (text or '').lower()
    if 'stage' in t or 'internship' in t or 'qualification' in t: return 'stage'
    if 'alternance' in t:                    return 'alternance'
    if 'freelance' in t or 'consultant' in t: return 'freelance'
    if 'remote' in t or 'télétravail' in t:  return 'remote'
    if 'cdd' in t or 'déterminé' in t:       return 'cdd'
    return 'cdi'


SKILL_PATTERNS = {
    'Python': r'\bpython\b', 'JavaScript': r'\b(javascript|js)\b',
    'Java': r'\bjava\b(?!script)', 'PHP': r'\bphp\b', 'TypeScript': r'\btypescript\b',
    'React': r'\breact\b', 'Vue.js': r'\bvue\.?js\b', 'Angular': r'\bangular\b',
    'Django': r'\bdjango\b', 'Laravel': r'\blaravel\b', 'Spring Boot': r'\bspring\b',
    'SQL': r'\bsql\b', 'MySQL': r'\bmysql\b', 'PostgreSQL': r'\bpostgres\w*\b',
    'MongoDB': r'\bmongodb\b', 'Oracle': r'\boracle\b', 'Redis': r'\bredis\b',
    'Docker': r'\bdocker\b', 'Kubernetes': r'\b(k8s|kubernetes)\b',
    'AWS': r'\b(aws|amazon web)\b', 'Azure': r'\bazure\b', 'GCP': r'\bgoogle cloud\b',
    'Git': r'\bgit\b', 'Linux': r'\blinux\b', 'REST API': r'\brest\s*api\b',
    'Power BI': r'\bpower\s*bi\b', 'Tableau': r'\btableau\b', 'Excel': r'\bexcel\b',
    'SAP': r'\bsap\b', 'Salesforce': r'\bsalesforce\b',
    'Machine Learning': r'\b(machine learning|apprentissage)\b',
    'Data Analysis': r'\banalyse.*données\b',
    'Agile': r'\b(agile|scrum|kanban)\b',
    'Comptabilité': r'\bcomptabilit\w+\b',
    'Communication': r'\bcommunication\b',
    'Leadership': r'\bleadership\b',
    'Anglais': r'\b(anglais|english)\b',
    'Français': r'\bfrançais\b',
}


def _extract_skills(text):
    if not text:
        return []
    tl = text.lower()
    return [skill for skill, pat in SKILL_PATTERNS.items() if re.search(pat, tl)][:12]


def _sanitize(text):
    """
    Nettoie le texte pour MySQL utf8 (3 octets max par caractère).
    - Remplace les espaces Unicode non standard par un espace normal
    - Supprime les caractères hors BMP (emoji, etc.) qui nécessitent utf8mb4
    - Normalise les guillemets et tirets typographiques
    """
    if not text:
        return text
    # Espaces Unicode non standard → espace normal
    text = re.sub(
        r'[\u00a0\u00ad\u1680\u2000-\u200b\u202f\u205f\u3000\ufeff]',
        ' ', text
    )
    # Tirets typographiques → tiret normal
    text = re.sub(r'[\u2010-\u2015\u2212]', '-', text)
    # Guillemets typographiques → guillemets droits
    text = re.sub(r'[\u2018\u2019\u201a\u201b]', "'", text)
    text = re.sub(r'[\u201c\u201d\u201e\u201f]', '"', text)
    # Supprimer les caractères hors BMP (> U+FFFF, 4 octets UTF-8) — nécessitent utf8mb4
    text = re.sub(r'[\U00010000-\U0010ffff]', '', text)
    # Nettoyer les espaces multiples
    text = re.sub(r'  +', ' ', text)
    return text.strip()


def _normalize_loc(loc):
    if not loc:
        return "Abidjan, Côte d'Ivoire"
    loc = re.sub(r'\s+', ' ', loc).strip()
    ci_names = ['abidjan','bouaké','daloa','yamoussoukro','san pedro','korhogo',
                'treichville','yopougon','cocody','marcory','plateau','abobo']
    if any(n in loc.lower() for n in ci_names):
        if "ivoire" not in loc.lower() and ', ci' not in loc.lower():
            loc = loc + ", Côte d'Ivoire"
    return loc[:200]


# Mois en français → numéro
_FR_MONTHS = {
    'janvier':1,'février':2,'mars':3,'avril':4,'mai':5,'juin':6,
    'juillet':7,'août':8,'aout':8,'septembre':9,'octobre':10,
    'novembre':11,'décembre':12,'decembre':12,
}

def _parse_french_date(text):
    """
    Tente de parser une date française depuis un texte.
    Formats supportés :
      - "9 mai 2023", "lundi 9 mai 2023", "Publié le mardi 16 octobre 2023"
      - "16/10/2023", "16-10-2023"
      - "16 octobre 2023"
    Retourne un objet datetime.date ou None.
    """
    import datetime
    if not text:
        return None
    text = text.lower().strip()

    # Format numérique jj/mm/aaaa ou jj-mm-aaaa
    m = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', text)
    if m:
        try:
            return datetime.date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except ValueError:
            pass

    # Format texte "9 mai 2023" / "lundi 9 mai 2023"
    m = re.search(
        r'(\d{1,2})\s+(' + '|'.join(_FR_MONTHS.keys()) + r')\s+(\d{4})',
        text
    )
    if m:
        try:
            return datetime.date(int(m.group(3)), _FR_MONTHS[m.group(2)], int(m.group(1)))
        except ValueError:
            pass

    return None


def _is_deadline_passed(date_text, grace_days=3):
    """
    Retourne True si la date limite est dépassée (+ grace_days jours de tolérance).
    Retourne False si la date n'est pas parseable (on garde l'offre par défaut).
    """
    import datetime
    d = _parse_french_date(date_text)
    if d is None:
        return False
    today = timezone.now().date()
    return d < (today - datetime.timedelta(days=grace_days))


# ══════════════════════════════════════════════════════════════════════════════
#  SOURCE 1 : AGENCE EMPLOI JEUNES CI
# ══════════════════════════════════════════════════════════════════════════════

BASE_AEJI     = 'https://agenceemploijeunes.ci'
AEJI_LISTING  = f'{BASE_AEJI}/site/offres-emplois'
AEJI_API      = f'{BASE_AEJI}/api/home/offres'


def _aeji_parse_detail(url, html):
    """Parse la page de détail d'une offre AEJI."""
    soup = BeautifulSoup(html, 'html.parser')

    # Titre — dans h3 du bloc job-info-box
    title = ''
    job_box = soup.find('div', class_=re.compile(r'job-info-box'))
    if job_box:
        h = job_box.find(['h3', 'h2', 'h4'])
        if h:
            title = h.get_text(strip=True)

    # Fallback h1/h2/h3
    if not title or len(title) < 4:
        for sel in ['h3', 'h2', 'h1']:
            for el in soup.find_all(sel):
                t = el.get_text(strip=True)
                if 4 < len(t) < 200 and t.lower() not in ("détails de l'offre", "autres offres d'emploi"):
                    title = t
                    break
            if title:
                break

    if not title or len(title) < 4:
        return None

    title = re.sub(r'\s+', ' ', title).strip()[:200]

    # Métadonnées depuis tableau
    meta = {}
    for table in soup.find_all('table'):
        for row in table.find_all('tr'):
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                k = cells[0].get_text(strip=True).lower().rstrip(':')
                v = cells[1].get_text(strip=True)
                if k and v:
                    meta[k] = v

    def _m(*keys):
        for k in meta:
            for key in keys:
                if key in k:
                    return meta[k]
        return None

    lieu       = _m('lieu', 'localisation', 'ville', 'travail')
    date_clos  = _m('clôture', 'cloture', 'limite', 'date')
    date_pub   = _m('publication', 'publié', 'parution', 'mise en ligne')
    diplome    = _m('diplôme', 'diplome', 'qualification')
    contrat    = _m('contrat')
    experience = _m('expérience', 'experience')
    niveau     = _m('niveau', 'étude')
    company    = _m('entreprise', 'employeur', 'société')

    # Rejeter les offres dont la date limite est dépassée
    if date_clos and _is_deadline_passed(date_clos):
        logger.info('AEJI: offre expirée (date limite %s), ignorée : %s', date_clos, url)
        return None

    # Description depuis le bloc job-info-box
    desc_parts = []
    if job_box:
        for el in job_box.find_all(['li', 'p', 'div']):
            t = el.get_text(strip=True)
            if len(t) > 8 and t not in desc_parts:
                desc_parts.append(t)

    meta_lines = []
    for label, val in [('Diplôme requis', diplome), ('Contrat', contrat),
                       ('Expérience', experience), ('Niveau', niveau),
                       ('Date limite', date_clos)]:
        if val:
            meta_lines.append(f'{label} : {val}')

    description = '\n'.join(meta_lines)
    if desc_parts:
        description += '\n\n' + '\n'.join(desc_parts[:20])

    skills_text = ' '.join([title, diplome or '', experience or '', description[:500]])

    # Nom de l'entreprise — souvent absent sur AEJI
    if not company or 'aucune information' in (company or '').lower():
        company = 'Agence Emploi Jeunes CI'

    # Date de publication réelle (pour posted_at précis)
    pub_date = _parse_french_date(date_pub) if date_pub else None

    return {
        'title':       title,
        'company':     company[:200],
        'location':    _normalize_loc(lieu),
        'description': description.strip()[:3000],
        'job_type':    _guess_job_type(contrat or title),
        'skills':      ', '.join(_extract_skills(skills_text))[:500],
        'external_id': _make_id('aeji', url),
        'external_url': url,
        'pub_date':    pub_date,
        'deadline':    date_clos,
    }


def scrape_agenceemploijeunes(max_pages=5):
    """Scrape AEJI et retourne les nouveaux Job créés."""
    from jobs.models import Job, JobSource

    source, _ = JobSource.objects.get_or_create(
        name='Agence Emploi Jeunes CI',
        defaults={'url': BASE_AEJI, 'region': "Côte d'Ivoire"}
    )

    seen_ids   = set(Job.objects.filter(
        external_id__startswith='aeji_').values_list('external_id', flat=True))
    jobs_found = []

    api_items = []
    for page in range(1, max_pages + 1):
        payload = _fetch_json(
            AEJI_API,
            referer=BASE_AEJI,
            params={'page': page},
            headers={
                'Accept': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
            }
        )
        if not payload:
            logger.warning('AEJI: API inaccessible ou réponse invalide page %d', page)
            break

        items = payload.get('items') or []
        if not items:
            logger.info('AEJI: plus d\'offres API à la page %d — arrêt', page)
            break

        api_items.extend(items)
        logger.info('AEJI API page %d: %d offres', page, len(items))
        _sleep(1.0, 1.8)

    if api_items:
        for item in api_items:
            reference = item.get('reference') or item.get('id') or item.get('slug')
            if not reference:
                continue

            ext_id = _make_id('aeji', reference)
            if ext_id in seen_ids:
                continue

            title = item.get('titre') or item.get('slug') or 'Offre AEJI'
            company = item.get('entreprise') or 'Agence Emploi Jeunes CI'
            location = _normalize_loc(item.get('localisation'))

            import datetime
            pub_date = None
            deadline = None
            try:
                if item.get('date_publication'):
                    pub_date = datetime.date.fromisoformat(item['date_publication'])
                if item.get('date_fin'):
                    deadline = datetime.date.fromisoformat(item['date_fin'])
            except Exception:
                pub_date = None
                deadline = None

            description_parts = []
            for label, value in [
                ('Secteur', item.get('secteur')),
                ('Contrat', item.get('type_contrat')),
                ('Agence régionale', item.get('agence_regionale')),
                ('Localisation', item.get('localisation')),
                ('Publié le', item.get('date_publication')),
                ('Date de fin', item.get('date_fin')),
                ('Nombre de postes', item.get('nombre_places')),
            ]:
                if value:
                    description_parts.append(f'{label} : {value}')

            description = '\n'.join(description_parts).strip()[:3000]
            skills_text = ' '.join([title, item.get('secteur') or '', item.get('type_contrat') or ''])
            detail_url = _normalize_aeji_offer_url(
                f'/offres-emploi/{reference}',
                fallback_reference=reference
            )

            try:
                pub_dt = timezone.make_aware(
                    datetime.datetime.combine(pub_date, datetime.time())
                ) if pub_date else timezone.now()
            except Exception:
                pub_dt = timezone.now()

            try:
                job = Job.objects.create(
                    title           = _sanitize(title),
                    company         = _sanitize(company),
                    location        = _sanitize(location),
                    country         = 'CI',
                    domain          = _guess_domain(title),
                    job_type        = _guess_job_type(item.get('type_contrat') or title),
                    description     = _sanitize(description) or _sanitize(title),
                    required_skills = _sanitize(', '.join(_extract_skills(skills_text)))[:500],
                    external_url    = detail_url,
                    external_id     = ext_id,
                    source_type     = 'scraping',
                    scraping_source = source,
                    is_active       = True,
                    is_verified     = True,
                    posted_at       = pub_dt,
                    deadline        = deadline,
                )
                jobs_found.append(job)
                seen_ids.add(ext_id)
                logger.info('AEJI ajouté: %s', title[:60])
            except Exception as e:
                logger.warning('AEJI save error: %s', e)

        source.jobs_scraped = (source.jobs_scraped or 0) + len(jobs_found)
        source.last_sync    = timezone.now()
        source.save(update_fields=['jobs_scraped', 'last_sync'])
        logger.info('AEJI: %d nouvelles offres importées via API', len(jobs_found))
        return jobs_found

    offer_urls = []

    # 1) Parcourir les pages de listing
    for page in range(1, max_pages + 1):
        url = AEJI_LISTING if page == 1 else f'{AEJI_LISTING}?page={page}'
        resp = _fetch(url, referer=BASE_AEJI)
        if not resp:
            logger.warning('AEJI: page %d inaccessible', page)
            break

        found_on_page = _extract_offer_links_from_html(resp.text, source='aeji')

        if not found_on_page:
            logger.info('AEJI: plus d\'offres à la page %d — arrêt', page)
            break

        offer_urls.extend(found_on_page)
        logger.info('AEJI page %d: %d offres trouvées', page, len(found_on_page))
        _sleep(1.0, 2.0)

    offer_urls = list(dict.fromkeys(offer_urls))  # dédupliquer
    logger.info('AEJI: %d URLs d\'offres à traiter', len(offer_urls))

    # 2) Scraper chaque offre en détail
    for offer_url in offer_urls:
        ext_id = _make_id('aeji', offer_url)
        if ext_id in seen_ids:
            continue

        resp = _fetch(offer_url, referer=AEJI_LISTING)
        if not resp:
            _sleep()
            continue

        data = _aeji_parse_detail(offer_url, resp.text)
        if not data:
            logger.debug('AEJI: parse échoué pour %s', offer_url)
            _sleep()
            continue

        try:
            # Utiliser la date de publication réelle si disponible
            pub_dt = timezone.make_aware(
                __import__('datetime').datetime.combine(data['pub_date'], __import__('datetime').time())
            ) if data.get('pub_date') else timezone.now()

            job = Job.objects.create(
                title           = _sanitize(data['title']),
                company         = _sanitize(data['company']),
                location        = _sanitize(data['location']),
                country         = 'CI',
                domain          = _guess_domain(data['title']),
                job_type        = data['job_type'],
                description     = _sanitize(data['description']),
                required_skills = _sanitize(data['skills']),
                external_url    = data['external_url'],
                external_id     = ext_id,
                source_type     = 'scraping',
                scraping_source = source,
                is_active       = True,
                is_verified     = True,
                posted_at       = pub_dt,
            )
            jobs_found.append(job)
            seen_ids.add(ext_id)
            logger.info('AEJI ajouté: %s', data['title'][:60])
        except Exception as e:
            logger.warning('AEJI save error: %s', e)

        _sleep(0.8, 1.8)

    source.jobs_scraped = (source.jobs_scraped or 0) + len(jobs_found)
    source.last_sync    = timezone.now()
    source.save(update_fields=['jobs_scraped', 'last_sync'])
    logger.info('AEJI: %d nouvelles offres importées', len(jobs_found))
    return jobs_found


# ══════════════════════════════════════════════════════════════════════════════
#  SOURCE 2 : ABIDJAN.NET ANNONCES EMPLOI
# ══════════════════════════════════════════════════════════════════════════════

BASE_ABJ      = 'https://annonces.abidjan.net'
ABJ_LISTING   = f'{BASE_ABJ}/emplois'


def _abj_parse_detail(url, html):
    """Parse une page de détail d'offre abidjan.net."""
    soup = BeautifulSoup(html, 'html.parser')
    full_text = soup.get_text(separator=' ')

    # Titre : h1 avec le nom du poste (exclure les h1 navigation)
    title = ''
    for h in soup.find_all('h1'):
        t = h.get_text(strip=True)
        t = re.sub(r'\s*\(.*?\)\s*$', '', t).strip()  # enlever (CDD) etc. du titre
        if 4 < len(t) < 200 and not any(x in t.lower() for x in
                                         ['poster une', 'signaler', 'connexion', 'inscription']):
            title = t
            break

    if not title or len(title) < 4:
        return None

    title = re.sub(r'\s+', ' ', title).strip()[:200]

    # Type de contrat depuis h1 entre parenthèses
    contrat_match = re.search(r'\(([^)]+)\)', soup.find('h1').get_text(strip=True) if soup.find('h1') else '')
    contrat = contrat_match.group(1).strip() if contrat_match else ''

    # ── Date de publication : "Publié le mardi 9 mai 2023" ───────────────────
    pub_date = None
    pub_match = re.search(
        r'publi[ée]\s+le\s+(?:\w+\s+)?(\d{1,2}\s+\w+\s+\d{4}|\d{1,2}[/-]\d{1,2}[/-]\d{4})',
        full_text, re.I
    )
    if pub_match:
        pub_date = _parse_french_date(pub_match.group(1))

    # ── Date limite de candidature ────────────────────────────────────────────
    deadline_text = None
    dl_match = re.search(
        r'(?:date\s+limite|clôture|candidature\s+avant|avant\s+le)[^\d]*'
        r'(\d{1,2}[/-]\d{1,2}[/-]\d{4}|\d{1,2}\s+\w+\s+\d{4})',
        full_text, re.I
    )
    if dl_match:
        deadline_text = dl_match.group(1)

    # Ne pas rejeter automatiquement les annonces dont la date limite est dépassée.
    # Cela permet d'importer les offres réelles même si elles sont déjà closes.
    if deadline_text and _is_deadline_passed(deadline_text):
        logger.info('Abidjan.net: offre close ou date limite passée détectée (deadline %s), mais importée : %s', deadline_text, url)

    # Ne pas rejeter automatiquement les offres en fonction de leur ancienneté.
    # Le site peut publier des annonces plus anciennes que la fenêtre de test ;
    # l'objectif ici est de conserver les offres réellement disponibles pour l'import.

    # Description dans annonce-p-subtitle
    desc_el = soup.find('div', class_=re.compile(r'annonce-p-subtitle'))
    description = ''
    if desc_el:
        description = desc_el.get_text(separator='\n', strip=True)

    # Localisation — chercher dans les métadonnées
    location = "Abidjan, Côte d'Ivoire"
    loc_candidates = re.findall(
        r"(Abidjan|Bouaké|Daloa|Yamoussoukro|San Pedro|Korhogo|Touba|Abengourou|"
        r"Man|Divo|Soubré|Gagnoa|Côte d'Ivoire|Cote d'Ivoire)[,\s]*(?:CI)?",
        (description + ' ' + full_text)[:2000], re.I
    )
    if loc_candidates:
        location = _normalize_loc(loc_candidates[0])

    # Entreprise
    company = 'Non précisé'
    for line in description.split('\n')[:8]:
        line = line.strip()
        if 5 < len(line) < 120 and not any(c.isdigit() for c in line[:3]):
            if any(x in line.lower() for x in ['société','entreprise','groupe','sarl','sa ','sas','compagnie','coopérative','cabinet','agence']):
                company = line[:200]
                break

    skills_text = title + ' ' + description[:500]

    return {
        'title':        title,
        'company':      company,
        'location':     location,
        'description':  description.strip()[:3000],
        'job_type':     _guess_job_type(contrat or title),
        'skills':       ', '.join(_extract_skills(skills_text))[:500],
        'external_id':  _make_id('abj', url),
        'external_url': url,
        'pub_date':     pub_date,
        'deadline':     deadline_text,
    }


def scrape_abidjannet(max_pages=5, source_name='Abidjan.net Emplois'):
    """
    Scrape annonces.abidjan.net/emplois — plus grand site d'annonces CI.
    """
    from jobs.models import Job, JobSource

    source, _ = JobSource.objects.get_or_create(
        name=source_name,
        defaults={'url': ABJ_LISTING, 'region': "Côte d'Ivoire"}
    )

    seen_ids   = set(Job.objects.filter(
        external_id__startswith='abj_').values_list('external_id', flat=True))
    jobs_found = []
    offer_urls = []

    # 1) Parcourir les pages de listing
    for page in range(1, max_pages + 1):
        url  = ABJ_LISTING if page == 1 else f'{ABJ_LISTING}?page={page}'
        resp = _fetch(url, referer=BASE_ABJ)
        if not resp:
            logger.warning('Abidjan.net: page %d inaccessible', page)
            break

        found_on_page = _extract_offer_links_from_html(resp.text, source='abj')

        if not found_on_page:
            logger.info('Abidjan.net: plus d\'offres à la page %d', page)
            break

        offer_urls.extend(found_on_page)
        logger.info('Abidjan.net page %d: %d offres', page, len(found_on_page))
        _sleep(1.0, 2.0)

    offer_urls = list(dict.fromkeys(offer_urls))
    logger.info('Abidjan.net: %d URLs à traiter', len(offer_urls))

    # 2) Scraper chaque offre
    for offer_url in offer_urls:
        ext_id = _make_id('abj', offer_url)
        if ext_id in seen_ids:
            continue

        resp = _fetch(offer_url, referer=ABJ_LISTING)
        if not resp:
            _sleep()
            continue

        data = _abj_parse_detail(offer_url, resp.text)
        if not data:
            logger.debug('Abidjan.net: parse échoué pour %s', offer_url)
            _sleep()
            continue

        try:
            # Utiliser la date de publication réelle si disponible
            pub_dt = timezone.make_aware(
                __import__('datetime').datetime.combine(data['pub_date'], __import__('datetime').time())
            ) if data.get('pub_date') else timezone.now()

            job = Job.objects.create(
                title           = _sanitize(data['title']),
                company         = _sanitize(data['company']),
                location        = _sanitize(data['location']),
                country         = 'CI',
                domain          = _guess_domain(data['title']),
                job_type        = data['job_type'],
                description     = _sanitize(data['description']),
                required_skills = _sanitize(data['skills']),
                external_url    = data['external_url'],
                external_id     = ext_id,
                source_type     = 'scraping',
                scraping_source = source,
                is_active       = True,
                is_verified     = False,
                posted_at       = pub_dt,
            )
            jobs_found.append(job)
            seen_ids.add(ext_id)
            logger.info('Abidjan.net ajouté: %s', data['title'][:60])
        except Exception as e:
            logger.warning('Abidjan.net save error: %s', e)

        _sleep(0.8, 1.5)

    source.jobs_scraped = (source.jobs_scraped or 0) + len(jobs_found)
    source.last_sync    = timezone.now()
    source.save(update_fields=['jobs_scraped', 'last_sync'])
    logger.info('Abidjan.net: %d nouvelles offres importées', len(jobs_found))
    return jobs_found


def _extract_linkedin_job_urls_from_html(html):
    """Extrait les URLs de détail des offres depuis la page de recherche LinkedIn."""
    soup = BeautifulSoup(html, 'html.parser')
    urls = []
    seen = set()

    for a in soup.find_all('a', href=True):
        href = a.get('href', '')
        if not href:
            continue
        if '/jobs/view/' not in href:
            continue
        normalized = href.split('?')[0]
        if normalized.startswith('/'):
            normalized = f'https://www.linkedin.com{normalized}'
        if normalized not in seen:
            seen.add(normalized)
            urls.append(normalized)

    return urls


def _linkedin_parse_card(url, html):
    """Parse un bloc d'offre depuis la page de recherche LinkedIn."""
    soup = BeautifulSoup(html, 'html.parser')
    card = None

    for candidate in soup.find_all('a', href=True):
        href = candidate.get('href', '')
        if '/jobs/view/' in href and href.split('?')[0] == url.split('?')[0]:
            card = candidate
            break

    if not card:
        card = soup

    title = ''
    text_candidates = []
    for el in card.find_all(['h2', 'h3', 'h4', 'span', 'strong']):
        text = re.sub(r'\s+', ' ', el.get_text(' ', strip=True))
        if 4 < len(text) < 220:
            text_candidates.append(text)

    for text in text_candidates:
        lowered = text.lower()
        if any(x in lowered for x in ['sign in', 'join now', 'cookie', 'apply', 'view job', 'jobs']):
            continue
        if len(text) > 8:
            title = text
            break

    if not title:
        title = 'Offre LinkedIn'

    company = ''
    for text in text_candidates:
        lowered = text.lower()
        if lowered == title.lower():
            continue
        if any(x in lowered for x in ['sa', 'sarl', 'group', 'company', 'consulting', 'solutions', 'technologies', 'labs', 'agency', 'systems', 'consultant', 'networks']):
            company = text
            break

    if not company:
        company = 'Entreprise LinkedIn'

    description = '\n'.join([
        re.sub(r'\s+', ' ', s.get_text(' ', strip=True))
        for s in card.find_all(['p', 'li'])
        if re.sub(r'\s+', ' ', s.get_text(' ', strip=True))
    ])[:3000]

    location = 'Abidjan, Côte d\'Ivoire'
    full_text = card.get_text(' ', strip=True)
    if 'Côte d\'Ivoire' in full_text or 'Cote d\'Ivoire' in full_text:
        location = 'Abidjan, Côte d\'Ivoire'

    return {
        'title': title[:200],
        'company': company[:200],
        'location': location,
        'description': description or title,
        'job_type': _guess_job_type(title),
        'skills': ', '.join(_extract_skills(title + ' ' + description))[:500],
        'external_id': _make_id('linkedin', url),
        'external_url': url,
    }


# Alias pour compatibilité avec la vue admin existante
def scrape_linkedin_ci(max_results=60):
    """Scrape les offres LinkedIn depuis la page de recherche publique."""
    from jobs.models import Job, JobSource

    source, _ = JobSource.objects.get_or_create(
        name='LinkedIn Jobs CI',
        defaults={'url': 'https://www.linkedin.com/jobs', 'region': "Côte d'Ivoire"}
    )

    seen_ids = set(Job.objects.filter(external_id__startswith='linkedin_').values_list('external_id', flat=True))
    jobs_found = []

    search_url = 'https://www.linkedin.com/jobs/search/?keywords=developer&location=C%C3%B4te%20d%27Ivoire'
    resp = _fetch(search_url, referer='https://www.linkedin.com/jobs', timeout=25, retries=1)
    if not resp:
        logger.warning('LinkedIn: page de recherche inaccessible')
        return jobs_found

    offer_urls = _extract_linkedin_job_urls_from_html(resp.text)
    if not offer_urls:
        logger.warning('LinkedIn: aucune URL d\'offre trouvée')
        return jobs_found

    for offer_url in offer_urls[:max(1, max_results)]:
        ext_id = _make_id('linkedin', offer_url)
        if ext_id in seen_ids:
            continue

        data = _linkedin_parse_card(offer_url, resp.text)
        if not data:
            continue

        try:
            job = Job.objects.create(
                title=_sanitize(data['title']),
                company=_sanitize(data['company']),
                location=_sanitize(data['location']),
                country='CI',
                domain=_guess_domain(data['title']),
                job_type=data['job_type'],
                description=_sanitize(data['description']),
                required_skills=_sanitize(data['skills'])[:500],
                external_url=data['external_url'],
                external_id=ext_id,
                source_type='scraping',
                scraping_source=source,
                is_active=True,
                is_verified=False,
                posted_at=timezone.now(),
            )
            jobs_found.append(job)
            seen_ids.add(ext_id)
            logger.info('LinkedIn ajouté: %s', data['title'][:60])
        except Exception as e:
            logger.warning('LinkedIn save error: %s', e)

        _sleep(0.8, 1.5)

    source.jobs_scraped = (source.jobs_scraped or 0) + len(jobs_found)
    source.last_sync = timezone.now()
    source.save(update_fields=['jobs_scraped', 'last_sync'])
    logger.info('LinkedIn: %d nouvelles offres importées', len(jobs_found))
    return jobs_found


# ══════════════════════════════════════════════════════════════════════════════
#  MAINTENANCE
# ══════════════════════════════════════════════════════════════════════════════

def cleanup_expired_jobs(days=60):
    """
    Désactive :
    1. Les offres scrapées dont posted_at > N jours
    2. Les offres dont la description mentionne une date limite passée
    3. Les offres AEJI avec l'ancien format URL (site restructuré)
    """
    from jobs.models import Job
    from django.utils import timezone as tz
    from datetime import timedelta

    total = 0

    # 1) Offres trop vieilles (posted_at > days)
    cutoff = tz.now() - timedelta(days=days)
    qs = Job.objects.filter(source_type='scraping', is_active=True, posted_at__lt=cutoff)
    count = qs.count()
    if count:
        qs.update(is_active=False)
        logger.info('Cleanup: %d offres scrapées > %d jours désactivées', count, days)
        total += count

    # 2) Offres dont la description contient une date limite passée
    #    Formats rencontrés :
    #      "Date limite de candidature:\nlundi 16 octobre 2023"
    #      "Date limite : 16/10/2023"
    #      "Date de clôture:27/04/2023"
    expired_by_desc = 0
    candidates = Job.objects.filter(source_type='scraping', is_active=True)
    ids_to_deactivate = []
    _date_pattern = re.compile(
        r'(?:date\s+limite|date\s+de\s+cl[oô]ture|candidature)[^\n]{0,30}\n?'
        r'\s*(?:lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche)?\s*'
        r'(\d{1,2}[/-]\d{1,2}[/-]\d{4}|\d{1,2}\s+\w+\s+\d{4})',
        re.I | re.MULTILINE
    )
    for job in candidates:
        desc = (job.description or '') + (job.requirements or '')
        for m in _date_pattern.finditer(desc):
            if _is_deadline_passed(m.group(1), grace_days=0):
                ids_to_deactivate.append(job.id)
                break

    if ids_to_deactivate:
        Job.objects.filter(id__in=ids_to_deactivate).update(is_active=False)
        expired_by_desc = len(ids_to_deactivate)
        logger.info('Cleanup: %d offres avec date limite passée désactivées', expired_by_desc)
        total += expired_by_desc

    # 3) Ancien format URL AEJI (/site/offres/ au lieu de /site/offres-emplois/)
    old_aeji = Job.objects.filter(
        external_url__contains='agenceemploijeunes.ci/site/offres/',
        is_active=True
    ).exclude(external_url__contains='/offres-emplois/')
    count3 = old_aeji.count()
    if count3:
        old_aeji.update(is_active=False)
        logger.info('Cleanup: %d offres AEJI ancien format désactivées', count3)
        total += count3

    logger.info('Cleanup total: %d offres désactivées', total)
    return total
