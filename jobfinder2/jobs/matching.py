"""
Moteur de matching NLP — JobFinder AI v2.1
Score 0–97 basé sur 6 critères pondérés.

Poids :
  Skills techniques  45 pts  (compétences métier — critère principal)
  Expérience         15 pts  (années d'expérience vs exigences de l'offre)
  NLP TF-IDF         17 pts  (similarité sémantique globale, modulée par les skills)
  Titre / domaine    12 pts  (concordance du poste recherché)
  Formation           5 pts  (niveau diplôme vs exigences)
  Localisation        3 pts  (bonus géographique — avantage, pas critère bloquant)
  ─────────────────────────
  TOTAL MAX          97 pts  (jamais 100 — incertitude humaine)

Principes :
  - Skills + Expérience = 60 pts → ce qui compte vraiment
  - Localisation = bonus pur (0 si autre pays, jamais pénalité bloquante)
  - Skills candidat normalisés par extraction depuis le texte du profil
  - Soft-skills seuls ne peuvent PAS dépasser 30/97
  - NLP réduit à 40 % si aucun skill ne matche, 65 % si skills faibles
  - Profil hors-domaine (skill=0 ET titre=0) capé à exp+loc+edu+5
"""
import re
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)

MATCH_WEIGHTS = {
    'skills': 45,
    'experience': 15,
    'nlp': 17,
    'title': 12,
    'education': 5,
    'location': 3,
}

# ── Villes CI ─────────────────────────────────────────────────────────────────
CI_CITIES = {
    'abidjan':      ['abidjan', 'plateau', 'cocody', 'yopougon', 'abobo', 'adjamé',
                     'treichville', 'marcory', 'koumassi', 'port-bouët', 'bingerville',
                     'riviera', 'marcori'],
    'bouake':       ['bouaké', 'bouake'],
    'daloa':        ['daloa'],
    'yamoussoukro': ['yamoussoukro'],
    'korhogo':      ['korhogo'],
    'san pedro':    ['san-pédro', 'san pedro', 'san-pedro'],
    'man':          ['man'],
    'gagnoa':       ['gagnoa'],
    'abengourou':   ['abengourou'],
    'divo':         ['divo'],
}

COUNTRY_CODES = {
    'CI':     "Côte d'Ivoire",
    'SN':     'Sénégal',
    'NG':     'Nigeria',
    'GH':     'Ghana',
    'CM':     'Cameroun',
    'ML':     'Mali',
    'BF':     'Burkina Faso',
    'REMOTE': 'Remote',
}

TITLE_DOMAIN_KEYWORDS = {
    'it': ['développeur', 'dev', 'developer', 'software', 'ingénieur', 'ingenieur', 'engineer', 'tech', 'informatique', 'système', 'systeme', 'backend', 'frontend', 'fullstack', 'full-stack', 'data'],
    'data': ['data', 'analyse', 'analyst', 'analytics', 'bi', 'statistique', 'machine learning', 'ml', 'scientifique', 'scientist'],
    'finance': ['finance', 'comptabil', 'audit', 'fiscal', 'trésorier', 'tresorier', 'contrôleur', 'controleur'],
    'marketing': ['marketing', 'communication', 'digital', 'brand', 'média', 'media'],
    'rh': ['rh', 'recrutement', 'talent', 'ressources humaines', 'formation'],
    'legal': ['juriste', 'juridique', 'droit', 'avocat', 'compliance'],
    'logistics': ['logistique', 'supply', 'achat', 'approvisionnement', 'stock'],
    'sales': ['commercial', 'vente', 'business', 'client', 'sales'],
    'medical': ['médical', 'medical', 'santé', 'sante', 'infirmier', 'pharmacien', 'clinique'],
}

TITLE_ALIASES = {
    'developer': 'developpeur',
    'developpeur': 'developpeur',
    'dev': 'developpeur',
    'engineer': 'ingenieur',
    'ingenieur': 'ingenieur',
    'analyst': 'analyste',
    'analyste': 'analyste',
    'scientist': 'scientifique',
    'scientifique': 'scientifique',
    'manager': 'manager',
    'lead': 'lead',
    'consultant': 'consultant',
    'specialist': 'specialiste',
    'specialiste': 'specialiste',
    'administrator': 'administrateur',
    'administrateur': 'administrateur',
    'assistant': 'assistant',
    'intern': 'stagiaire',
    'stagiaire': 'stagiaire',
}

# ── Compétences reconnues — techniques ET soft ─────────────────────────────────
SKILL_PATTERNS = {
    # ── Développement ──
    'Python':             r'\bpython\b',
    'JavaScript':         r'\b(javascript|js)\b',
    'Java':               r'\bjava\b(?!script)',
    'PHP':                r'\bphp\b',
    'TypeScript':         r'\btypescript\b',
    'React':              r'\breact\b',
    'Vue.js':             r'\bvue\.?js\b',
    'Angular':            r'\bangular\b',
    'Django':             r'\bdjango\b',
    'Laravel':            r'\blaravel\b',
    'Spring Boot':        r'\bspring\b',
    'Node.js':            r'\bnode\.?js\b',
    'C#':                 r'\bc#\b',
    'C++':                r'\bc\+\+\b',
    # ── Data / BI ──
    'SQL':                r'\bsql\b',
    'MySQL':              r'\bmysql\b',
    'PostgreSQL':         r'\bpostgres\w*\b',
    'MongoDB':            r'\bmongodb\b',
    'Oracle':             r'\boracle\b',
    'Redis':              r'\bredis\b',
    'Power BI':           r'\bpower\s*bi\b',
    'Tableau':            r'\btableau\b',
    'Machine Learning':   r'\b(machine learning|apprentissage automatique|ml\b)',
    'Data Analysis':      r'\b(analyse\s*de?\s*données|data anal\w+)\b',
    # ── DevOps / Cloud ──
    'Docker':             r'\bdocker\b',
    'Kubernetes':         r'\b(k8s|kubernetes)\b',
    'AWS':                r'\b(aws|amazon web services)\b',
    'Azure':              r'\bazure\b',
    'GCP':                r'\bgoogle cloud\b',
    'Git':                r'\bgit\b',
    'Linux':              r'\blinux\b',
    'REST API':           r'\brest\s*api\b',
    # ── Outils métier ──
    'SAP':                r'\bsap\b',
    'Salesforce':         r'\bsalesforce\b',
    'Excel':              r'\bexcel\b',
    # ── Gestion / Finance ──
    'Comptabilité':       r'\bcomptabilit\w+\b',
    'Fiscalité':          r'\bfiscalit\w+\b',
    'Audit':              r'\baudit\b',
    'Finance':            r'\bfinanc\w+\b',
    'Trésorerie':         r'\btrésorerie\b',
    # ── Droit ──
    'Juridique':          r'\bjuridique\b',
    # ── RH ──
    'Ressources Humaines': r'\b(ressources humaines|rh\b)',
    'Recrutement':        r'\brecrutement\b',
    # ── Supply ──
    'Logistique':         r'\blogistique\b',
    'Supply Chain':       r'\bsupply chain\b',
    # ── Commerce ──
    'Marketing':          r'\bmarketing\b',
    'Communication':      r'\bcommunication\b',
    'Vente':              r'\bvente\b',
    'Commerce':           r'\bcommerce\b',
    # ── Transversaux ──
    'Agile':              r'\b(agile|scrum|kanban)\b',
    'Gestion de projet':  r'\bgestion de projet\b',
    'Leadership':         r'\bleadership\b',
    'Anglais':            r'\b(anglais|english)\b',
    'Français':           r'\bfrançais\b',
}

# Soft skills génériques — présents partout, faible valeur discriminante
SOFT_SKILLS = {
    'communication', 'leadership', 'anglais', 'français', 'agile',
    'gestion de projet', 'excel', 'marketing', 'vente', 'commerce',
}

# Stopwords pour TF-IDF
_STOPWORDS_FR = {
    'de','du','des','le','la','les','un','une','au','aux','et','en','que','qui',
    'pour','par','sur','dans','avec','est','sont','ont','être','avoir','faire',
    'plus','très','tout','tous','toute','toutes','bien','aussi','même','mais',
    'si','ou','ni','ne','pas','sans','sous','entre','vers','comme','dont',
    'ce','se','sa','ses','son','leur','leurs','mon','ma','mes','ton','ta','tes',
    'nos','vos','ils','elles','nous','vous','il','elle','je','tu',
    'abidjan','côte','ivoire','cote','ivoir','afrique','ouest','africain',
    'emploi','offre','poste','candidature','candidat','recrutement','recruter',
    'limite','date','secteur','activité','activite','région','region',
    'entreprise','société','societe','information','aucune',
    'qualification','stage','contrat','niveau','diplôme','diplome',
    'experience','expérience','requis','requise','requises',
}


def _clean(text):
    if not text:
        return ''
    return re.sub(r'\s+', ' ', re.sub(r'[^\w\s]', ' ', text.lower())).strip()


def _city_group(loc):
    loc = (loc or '').lower()
    for city, aliases in CI_CITIES.items():
        if any(a in loc for a in aliases):
            return city
    return loc.strip()


def _extract_skills(text):
    """Extrait les compétences reconnues depuis un texte libre (normalisées)."""
    if not text:
        return []
    tl = text.lower()
    return [skill for skill, pat in SKILL_PATTERNS.items() if re.search(pat, tl)][:20]


def _normalize_title_tokens(text):
    tokens = [t for t in _clean(text).split() if len(t) > 2]
    normalized = []
    for token in tokens:
        normalized.append(TITLE_ALIASES.get(token, token))
    return normalized


def _title_similarity_score(candidate_title, job_title):
    if not candidate_title or not job_title:
        return 0

    cand_tokens = set(_normalize_title_tokens(candidate_title))
    job_tokens = set(_normalize_title_tokens(job_title))
    if not cand_tokens or not job_tokens:
        return 0

    overlap = cand_tokens & job_tokens
    if overlap:
        base = min(12, 6 + len(overlap) * 2)
    else:
        base = 0

    cand_text = _clean(candidate_title).lower()
    job_text = _clean(job_title).lower()

    cand_domains = {d for d, kws in TITLE_DOMAIN_KEYWORDS.items() if any(k in cand_text for k in kws)}
    job_domains = {d for d, kws in TITLE_DOMAIN_KEYWORDS.items() if any(k in job_text for k in kws)}

    if cand_domains and job_domains and (cand_domains & job_domains):
        base = max(base, 5)
    elif cand_domains and job_domains:
        base = max(base, 2)

    if cand_domains and job_domains and not (cand_domains & job_domains):
        base = max(0, base - 3)

    return max(0, min(12, base))


def _skill_similarity_score(job_skill, cand_skill):
    js = (job_skill or '').lower().strip()
    cs = (cand_skill or '').lower().strip()
    if not js or not cs:
        return 0.0
    if js == cs:
        return 1.0
    if len(js) > 4 and len(cs) > 4 and (js in cs or cs in js):
        return 0.85
    if len(js) > 4 and len(cs) > 4 and js[:4] == cs[:4]:
        return 0.65
    return 0.0


def _skill_coverage_score(candidate_skills, job_skills):
    if not job_skills:
        return 0, set(), set()

    cand_set = {s.lower().strip() for s in candidate_skills if s}
    job_set = {s.lower().strip() for s in job_skills if s}
    if not job_set:
        return 0, set(), set()

    weighted_matches = 0.0
    matched = set()
    for js in job_set:
        best = 0.0
        for cs in cand_set:
            best = max(best, _skill_similarity_score(js, cs))
        if best >= 0.85:
            matched.add(js)
            weighted_matches += 1.0
        elif best >= 0.65:
            matched.add(js)
            weighted_matches += 0.7
        elif best >= 0.4:
            matched.add(js)
            weighted_matches += 0.4

    score = int((weighted_matches / len(job_set)) * MATCH_WEIGHTS['skills'])
    return min(MATCH_WEIGHTS['skills'], score), matched, job_set - matched


def build_candidate_vector(user):
    try:
        p = user.profile
    except Exception:
        return {
            'text': '', 'skills': [], 'title': '', 'exp_years': 0,
            'location': '', 'city_group': '', 'country': 'CI',
            'has_edu': False, 'edu_level': '',
        }

    stored_skills = list(p.skills.values_list('name', flat=True))
    experiences   = p.experiences.all()
    educations    = p.educations.all()

    # ── Calcul des années d'expérience ──
    exp_years = 0.0
    for exp in experiences:
        if exp.start_date:
            end    = exp.end_date or timezone.now().date()
            months = (end.year - exp.start_date.year) * 12 + end.month - exp.start_date.month
            exp_years += max(0, months / 12)

    # ── Technologies des expériences ──
    tech_skills = []
    for exp in experiences:
        if exp.technologies:
            tech_skills += [t.strip() for t in exp.technologies.split(',') if t.strip()]

    # ── Texte complet du profil ──
    parts = [p.desired_title or '', p.summary or ''] + stored_skills + tech_skills
    for exp in experiences:
        parts += [exp.title or '', exp.company or '', exp.description or '', exp.technologies or '']
    for edu in educations:
        parts += [edu.degree or '', edu.institution or '']
    full_text = ' '.join(_clean(pt) for pt in parts if pt)

    # ── Skills normalisés : stockés (lowercase) + extraits du texte du profil ──
    raw_skills       = [s.lower() for s in stored_skills + tech_skills]
    extracted_skills = [s.lower() for s in _extract_skills(full_text)]
    all_skills       = list(set(raw_skills + extracted_skills))

    # ── Niveau d'éducation ──
    edu_level = ''
    if educations.exists():
        deg = (educations.order_by('-end_year').first().degree or '').lower()
        if any(w in deg for w in ['doctorat', 'phd', 'thèse']):
            edu_level = 'doctorat'
        elif any(w in deg for w in ['master', 'mba', 'ingénieur', 'ingenieur', 'bac 5', 'bac+5', 'bac+5']):
            edu_level = 'master'
        elif any(w in deg for w in ['licence', 'bachelor', 'bac 3', 'bac+3', 'bts', 'dut', 'bac+2']):
            edu_level = 'licence'
        else:
            edu_level = 'autre'

    location     = _clean(p.location or '')
    user_country = getattr(user, 'country', 'CI') or 'CI'

    return {
        'text':       full_text,
        'skills':     all_skills,
        'title':      _clean(p.desired_title or ''),
        'exp_years':  round(exp_years, 1),
        'location':   location,
        'city_group': _city_group(location),
        'country':    user_country,
        'has_edu':    educations.exists(),
        'edu_level':  edu_level,
    }


def build_job_vector(job):
    skills = [s.strip().lower() for s in job.required_skills.split(',') if s.strip()]
    parts  = [job.title or '', job.description or '', job.missions or '', job.requirements or '']
    text   = ' '.join(_clean(p) for p in parts if p)
    loc    = _clean(job.location or '')
    return {
        'text':         text,
        'skills':       skills,
        'title':        _clean(job.title or ''),
        'location':     loc,
        'city_group':   _city_group(loc),
        'country':      job.country,
        'is_remote':    job.is_remote,
        'job_type':     job.job_type,
        'requirements': _clean(job.requirements or ''),
        'has_structured_skills': bool(skills),
    }


def compute_match_score(user, job):
    """
    Score 0-97 basé sur 6 critères. Réaliste et non biaisé.
    Poids : skills(45) + NLP(17) + titre(12) + exp(15) + loc(3) + edu(5) = 97 max.
    """
    cand = build_candidate_vector(user)
    jv   = build_job_vector(job)

    # Profil vide → score 0
    if not cand['skills'] and not cand['title'] and not cand['text']:
        return {
            'score': 0, 'label': 'Profil incomplet', 'color': 'red',
            'advice': 'Complétez votre profil pour obtenir un score réel.',
            'matched_skills': [], 'missing_skills': list(jv['skills']),
            'details': {'skills': 0, 'nlp': 0, 'title': 0, 'exp': 0, 'location': 0, 'edu': 0},
        }

    # ── 1. Compétences (45 pts) ───────────────────────────────────────────────
    cand_set = set(cand['skills'])

    # Compétences de l'offre : structurées en priorité, sinon extraites du texte
    job_set = set(jv['skills'])
    if not job_set and jv['text']:
        job_set = set(s.lower() for s in _extract_skills(jv['text']))

    if job_set:
        skill_score, matched, missing = _skill_coverage_score(cand_set, job_set)

        # Séparer compétences techniques vs soft skills
        tech_required = job_set - SOFT_SKILLS
        soft_required = job_set & SOFT_SKILLS
        tech_matched = matched - SOFT_SKILLS
        soft_matched = matched & SOFT_SKILLS

        # Anti-inflation soft skills :
        # Si l'offre exige des compétences techniques mais que seuls des soft skills matchent
        # → plafonner la contribution des skills à 18/45
        if tech_required and not tech_matched and soft_matched:
            skill_score = min(skill_score, 18)
        elif tech_required and not tech_matched and not soft_matched:
            skill_score = min(skill_score, 8)

    else:
        # Aucune compétence identifiable — NLP + titre porteront le jugement
        matched, missing = set(), set()
        skill_score = 0
        tech_required, tech_matched = set(), set()

    # ── 2. NLP TF-IDF (17 pts — modulé par les skills) ───────────────────────
    nlp_max = MATCH_WEIGHTS['nlp']
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        if cand['text'] and jv['text']:
            vec = TfidfVectorizer(
                max_features=600, ngram_range=(1, 2), min_df=1,
                stop_words=list(_STOPWORDS_FR), sublinear_tf=True,
            )
            mat = vec.fit_transform([cand['text'], jv['text']])
            sim = float(cosine_similarity(mat[0:1], mat[1:2])[0][0])
            nlp_score = int(sim * nlp_max)
        else:
            nlp_score = _keyword_score(cand['text'], jv['text'], nlp_max)
    except ImportError:
        nlp_score = _keyword_score(cand['text'], jv['text'], nlp_max)
    except Exception as e:
        logger.warning('NLP error: %s', e)
        nlp_score = 0

    # Modulation NLP selon la force des skills :
    # Le NLP seul ne suffit pas pour valider une compatibilité métier
    if skill_score == 0 and not matched:
        nlp_score = int(nlp_score * 0.2)  # Texte similaire mais aucun skill → très peu fiable
    elif skill_score < 15:
        nlp_score = int(nlp_score * 0.35)  # Skills faibles → réduire fortement la contribution NLP
    elif skill_score < 30:
        nlp_score = int(nlp_score * 0.7)  # Skills partiels → NLP compte moins
    else:
        nlp_score = int(nlp_score * 0.95)

    nlp_score = max(0, min(nlp_max, nlp_score))

    # ── 3. Titre / domaine (12 pts) ──────────────────────────────────────────
    title_score = 0
    domain_kws = {
        'it':        ['développeur', 'dev', 'ingénieur', 'software', 'tech', 'informatique', 'système'],
        'data':      ['data', 'analyse', 'statistique', 'bi', 'analytique'],
        'finance':   ['finance', 'comptable', 'audit', 'fiscal', 'trésorier', 'contrôleur'],
        'marketing': ['marketing', 'communication', 'digital', 'brand', 'média'],
        'rh':        ['rh', 'recrutement', 'talent', 'ressources humaines', 'formation'],
        'legal':     ['juriste', 'juridique', 'droit', 'avocat', 'compliance'],
        'logistics': ['logistique', 'supply', 'achat', 'approvisionnement', 'stock'],
        'sales':     ['commercial', 'vente', 'business', 'client'],
        'medical':   ['médical', 'santé', 'infirmier', 'pharmacien', 'clinique'],
    }

    if cand['title'] and jv['title']:
        title_score = _title_similarity_score(cand['title'], jv['title'])

        # Bonus supplémentaire si les intitulés sont proches et le domaine est cohérent
        if title_score >= 6 and any(k in _clean(cand['title']).lower() for k in ['développeur', 'developpeur', 'data', 'analyste', 'ingénieur', 'finance', 'marketing', 'rh', 'logistique', 'commercial']):
            title_score = min(title_score + 1, MATCH_WEIGHTS['title'])

    # ── 4. Expérience (15 pts) ────────────────────────────────────────────────
    exp_years = cand['exp_years']
    req_text  = jv['requirements']

    if jv['job_type'] == 'stage':
        if exp_years <= 1:   exp_score = 15
        elif exp_years <= 2: exp_score = 10
        elif exp_years <= 4: exp_score = 5
        else:                exp_score = 2

    elif any(w in req_text for w in ['junior', 'débutant', 'entry', 'assistant']):
        if exp_years <= 1:   exp_score = 15
        elif exp_years <= 2: exp_score = 12
        elif exp_years <= 3: exp_score = 8
        else:                exp_score = 3

    elif any(w in req_text for w in ['senior', 'lead', 'manager', 'expert']):
        if exp_years >= 5:   exp_score = 15
        elif exp_years >= 3: exp_score = 10
        elif exp_years >= 1: exp_score = 5
        else:                exp_score = 1

    else:
        years_match = re.search(r'(\d+)\s*(?:an|ans|year|years)', req_text)
        if years_match:
            req_years = int(years_match.group(1))
            if req_years <= 1:
                if exp_years <= 1: exp_score = 15
                elif exp_years <= 2: exp_score = 10
                else: exp_score = 4
            elif req_years <= 2:
                if exp_years >= 2: exp_score = 15
                elif exp_years >= 1: exp_score = 10
                else: exp_score = 4
            elif req_years <= 3:
                if exp_years >= 3: exp_score = 15
                elif exp_years >= 2: exp_score = 11
                elif exp_years >= 1: exp_score = 7
                else: exp_score = 3
            elif req_years <= 5:
                if exp_years >= 5: exp_score = 15
                elif exp_years >= 3: exp_score = 11
                elif exp_years >= 1: exp_score = 6
                else: exp_score = 2
            else:
                if exp_years >= req_years: exp_score = 15
                elif exp_years >= req_years - 2: exp_score = 10
                elif exp_years >= req_years - 4: exp_score = 6
                else: exp_score = 2
        elif any(w in req_text for w in ['confirmé', 'expérimenté', '3 ans', '4 ans']):
            if exp_years >= 3: exp_score = 15
            elif exp_years >= 2: exp_score = 10
            elif exp_years >= 1: exp_score = 6
            else: exp_score = 2
        else:
            # Exigence d'expérience non précisée : progressif mais moins généreux
            exp_score = (12 if exp_years >= 7 else
                         10 if exp_years >= 5 else
                         8  if exp_years >= 3 else
                         5  if exp_years >= 1 else 2)

    # ── 5. Localisation (3 pts — bonus pur, jamais bloquant) ─────────────────
    # La localisation est un avantage, pas un critère éliminatoire.
    # Un candidat compétent dans un autre pays reste pertinent.
    if jv['is_remote']:
        loc_score = 3   # Remote = pas de contrainte géographique
    else:
        cand_country = (cand.get('country', 'CI') or 'CI').upper()
        job_country  = (jv['country'] or 'CI').upper()

        if cand_country == job_country:
            cg, jg = cand['city_group'], jv['city_group']
            if cg and jg and cg == jg:  loc_score = 3   # Même ville → bonus maximal
            elif cg or jg:              loc_score = 2   # Même pays, ville différente
            else:                       loc_score = 1   # Même pays, localisation floue
        else:
            loc_score = 0   # Pays différent → pas de bonus (mais pas de malus non plus)

    # ── 6. Formation (5 pts) ─────────────────────────────────────────────────
    edu_score = 0
    if cand['has_edu']:
        req_edu = req_text + ' ' + jv['text']
        req_high = any(w in req_edu for w in ['bac+5', 'bac 5', 'master', 'ingenieur', 'ingénieur', 'mba', 'doctorat'])
        req_med  = any(w in req_edu for w in ['bac+3', 'bac 3', 'licence', 'bts', 'dut', 'bac+2'])

        if req_high:
            if cand['edu_level'] in ('doctorat', 'master'): edu_score = 5
            elif cand['edu_level'] == 'licence':           edu_score = 3
            else:                                          edu_score = 1
        elif req_med:
            if cand['edu_level'] in ('licence', 'master', 'doctorat'): edu_score = 4
            else:                                                        edu_score = 2
        else:
            edu_score = 2  # Formation présente, mais ce n'est pas un discriminant fort en soi

    # ── Calcul total ─────────────────────────────────────────────────────────
    total = skill_score + nlp_score + title_score + exp_score + loc_score + edu_score

    # ── Critères bloquants (ordre du plus sévère au moins sévère) ─────────────

    # 1. Aucune compétence + aucun titre commun = hors domaine
    if skill_score == 0 and title_score == 0:
        domain_ceiling = exp_score + loc_score + edu_score + 5
        total = min(total, domain_ceiling)

    # 2. Soft skills uniquement sur une offre avec des exigences techniques
    if tech_required and not tech_matched and skill_score > 0:
        total = min(total, 35)

    # 3. Si une grande partie des compétences requises manque, limiter le score global
    if job_set and len(missing) / len(job_set) >= 0.5:
        total = min(total, 55)
    if job_set and len(missing) / len(job_set) >= 0.75:
        total = min(total, 35)

    # 4. Si aucun signal métier sérieux n'est présent, garder le score très conservateur
    if skill_score == 0 and title_score <= 2 and not matched:
        total = min(total, exp_score + loc_score + edu_score + 8)

    # Note : pas de cap géographique — la localisation est un bonus, pas un filtre

    total = max(0, min(97, total))

    # ── Labels ───────────────────────────────────────────────────────────────
    summary = get_match_summary(total, default_label='Incompatible')
    label = summary['label']
    color = summary['color']
    if label == 'Excellent match':
        advice = 'Profil très compatible — postulez sans hésiter !'
    elif label == 'Bon match':
        advice = 'Bon profil. Mettez en avant vos compétences clés dans la lettre de motivation.'
    elif label == 'Match partiel':
        advice = 'Profil partiel. Certaines compétences manquent — une lettre ciblée peut aider.'
    elif label == 'Faible match':
        advice = 'Des compétences importantes manquent. Enrichissez votre profil ou ciblez mieux.'
    else:
        advice = 'Votre profil ne correspond pas à cette offre.'

    return {
        'score':          total,
        'label':          label,
        'color':          color,
        'advice':         advice,
        'matched_skills': list(matched),
        'missing_skills': list(missing),
        'details': {
            'skills':   skill_score,
            'nlp':      nlp_score,
            'title':    title_score,
            'exp':      exp_score,
            'location': loc_score,
            'edu':      edu_score,
        },
    }


def get_match_summary(score, *, default_label='Match partiel'):
    score = max(0, min(97, int(score or 0)))
    if score >= 80:
        return {'label': 'Excellent match', 'color': 'green', 'level': 'excellent'}
    if score >= 62:
        return {'label': 'Bon match', 'color': 'gold', 'level': 'good'}
    if score >= 44:
        return {'label': 'Match partiel', 'color': 'orange', 'level': 'partial'}
    if score >= 25:
        return {'label': 'Faible match', 'color': 'red', 'level': 'weak'}
    return {'label': default_label, 'color': 'red', 'level': 'poor'}


def compute_display_score(user, job, base_score=None, *, refresh_base=False):
    """Retourne le score affiché à l'utilisateur (score de base + ajustement ML)."""
    if base_score is None or refresh_base:
        try:
            base_score = compute_match_score(user, job)['score']
        except Exception:
            base_score = 0

    try:
        ml_delta, _ = compute_learned_adjustment(user, job)
    except Exception:
        ml_delta = 0

    adjusted = base_score + ml_delta if ml_delta != 0 else base_score
    return max(0, min(97, adjusted))


def compute_learned_adjustment(user, job):
    """
    Ajustement ML basé sur l'historique des interactions de l'utilisateur.

    Principe :
      1. Récupère les 150 dernières interactions de l'utilisateur.
      2. Construit un vecteur de préférences (domaine, type contrat, compétences).
      3. Compare avec l'offre courante → delta entre -15 et +15.

    Retourne :
      delta  (int)   : ajustement à ajouter au score de base
      reasons (list) : explications lisibles (pour transparence / mémoire)
    """
    try:
        from applications.models import JobInteraction
    except ImportError:
        return 0, []

    if not user.is_authenticated:
        return 0, []

    # ── Récupérer l'historique ────────────────────────────────────────────────
    history = list(
        JobInteraction.objects.filter(user=user)
        .select_related('job')
        .order_by('-created_at')[:150]
    )

    if len(history) < 3:
        # Pas assez de données pour un apprentissage fiable
        return 0, []

    ACTION_WEIGHTS = {'applied': 3, 'saved': 2, 'viewed': 1, 'dismissed': -2}

    # ── Agréger les préférences ───────────────────────────────────────────────
    domain_score   = {}   # domain_code → poids cumulé
    jobtype_score  = {}   # job_type    → poids cumulé
    skill_score    = {}   # skill_lower → poids cumulé

    for inter in history:
        w = ACTION_WEIGHTS.get(inter.action, 0)
        j = inter.job

        if j.domain:
            domain_score[j.domain] = domain_score.get(j.domain, 0) + w

        if j.job_type:
            jobtype_score[j.job_type] = jobtype_score.get(j.job_type, 0) + w

        for sk in j.required_skills.split(','):
            sk = sk.strip().lower()
            if sk:
                skill_score[sk] = skill_score.get(sk, 0) + w

    delta   = 0
    reasons = []

    # ── 1. Domaine préféré / évité (max ±8) ──────────────────────────────────
    if job.domain:
        d_val = domain_score.get(job.domain, 0)
        if d_val >= 3:
            bonus = min(8, d_val * 2)
            delta += bonus
            reasons.append(f'+{bonus} domaine souvent postulé')
        elif d_val <= -3:
            delta -= 5
            reasons.append('-5 domaine ignoré par le passé')

    # ── 2. Type de contrat préféré (max ±4) ──────────────────────────────────
    if job.job_type:
        t_val = jobtype_score.get(job.job_type, 0)
        if t_val >= 2:
            bonus = min(4, t_val)
            delta += bonus
            reasons.append(f'+{bonus} type de contrat préféré')
        elif t_val <= -2:
            delta -= 3
            reasons.append('-3 type de contrat évité')

    # ── 3. Compétences déjà valorisées / évitées (max ±8) ────────────────────
    job_skills = [s.strip().lower() for s in job.required_skills.split(',') if s.strip()]
    # Si pas de compétences structurées, extraire du texte
    if not job_skills:
        job_skills = [s.lower() for s in _extract_skills(
            (job.description or '') + ' ' + (job.requirements or '')
        )]

    if job_skills:
        cumul = sum(skill_score.get(sk, 0) for sk in job_skills)
        if cumul >= 3:
            bonus = min(8, cumul)
            delta += bonus
            reasons.append(f'+{bonus} compétences valorisées dans l\'historique')
        elif cumul <= -3:
            malus = max(-8, cumul)
            delta += malus
            reasons.append(f'{malus} compétences peu appréciées dans l\'historique')

    # ── Borner le delta ───────────────────────────────────────────────────────
    delta = max(-15, min(15, delta))
    return delta, reasons


def _keyword_score(text_a, text_b, max_s):
    if not text_a or not text_b:
        return 0
    wa = {w for w in _clean(text_a).split() if len(w) > 3}
    wb = {w for w in _clean(text_b).split() if len(w) > 3}
    if not wb:
        return 0
    return int(min(1.0, len(wa & wb) / len(wb)) * max_s)


def bulk_compute_matches(user, jobs=None, limit=50):
    """Calcule les scores pour plusieurs offres. Retourne [{job, detail}] trié DESC."""
    from jobs.models import Job, JobMatch
    if jobs is None:
        jobs = list(Job.objects.filter(is_active=True).order_by('-posted_at')[:limit])

    cand = build_candidate_vector(user)
    if not cand['skills'] and not cand['title']:
        return []

    results = []
    for job in jobs:
        try:
            result = compute_match_score(user, job)
            JobMatch.objects.update_or_create(
                user=user, job=job,
                defaults={'score': result['score']}
            )
            results.append({'job': job, 'detail': result})
        except Exception as e:
            logger.warning('bulk_match error %s: %s', job.pk, e)

    results.sort(key=lambda x: -x['detail']['score'])
    logger.info('bulk_compute_matches: %d scores pour user %s', len(results), user.pk)
    return results
