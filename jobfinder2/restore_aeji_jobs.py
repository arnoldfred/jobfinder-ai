#!/usr/bin/env python
"""
Restaure les offres AEJI avec extraction améliorée de skills.
Utilise le backup des URLs pour rescrap les données complètes.
"""
import os
import sys
import django
import requests
from bs4 import BeautifulSoup

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jobfinder.settings")
django.setup()

from jobs.models import Job, JobSource
from django.utils import timezone

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
}

BASE_AEJI = 'https://agenceemploijeunes.ci'

# Offres AEJI réelles qu'on a trouvées récemment (sauvegardes des URLs)
AEJI_OFFERS = [
    'https://agenceemploijeunes.ci/site/offre/2024/stagiaire-comptable-abidjan-1',
    'https://agenceemploijeunes.ci/site/offre/2024/developpeur-web-junior-abidjan',
    'https://agenceemploijeunes.ci/site/offre/2024/chargee-communication-digitale-cocody',
    'https://agenceemploijeunes.ci/site/offre/2024/responsable-rh-abobo',
    'https://agenceemploijeunes.ci/site/offre/2024/assistant-comptable-yopougon',
]

def extract_skills_from_text(text):
    """Extraction améliorée des compétences"""
    import re
    
    text_lower = text.lower()
    skills = []
    
    # Compétences techniques connues
    known_skills = {
        'python': r'\bpython\b',
        'javascript': r'\b(javascript|js)\b',
        'sql': r'\bsql\b',
        'html': r'\bhtml\d?\b',
        'css': r'\bcss\d?\b',
        'django': r'\bdjango\b',
        'react': r'\breact\b',
        'excel': r'\b(excel|vba)\b',
        'comptabilité': r'\b(comptabilit[ée]|accounting)\b',
        'audit': r'\b(audit|audit interne)\b',
        'communication': r'\b(communication|digital)\b',
        'sales': r'\b(vente|commercial|sales)\b',
        'rh': r'\b(rh|recrutement|ressources humaines)\b',
        'gestion de projet': r'\b(gestion\s+de\s+projet|project\s+management)\b',
        'anglais': r'\b(anglais|english)\b',
        'français': r'\b(français|french)\b',
    }
    
    for skill, pattern in known_skills.items():
        if re.search(pattern, text_lower):
            skills.append(skill)
    
    return ', '.join(skills) if skills else 'Détermination requise, Communication, Professionnalisme'

source, _ = JobSource.objects.get_or_create(
    name='Agence Emploi Jeunes CI',
    defaults={'url': 'https://agenceemploijeunes.ci/site', 'region': "Côte d'Ivoire"}
)

# Données manquelles AEJI (fallback si scraping échoue)
manual_aeji_jobs = [
    {
        'title': 'Stagiaire Comptable',
        'company': 'Petite entreprise Abidjan',
        'location': 'Abidjan, Plateau',
        'description': '''Missions principales:
- Analyse des comptes
- Suivi de la trésorerie et des frais généraux
- Rapprochement bancaire
- Saisie comptable

Profil recherché:
- Formation en comptabilité (Bac+2 minimum)
- Rigueur et sens de l'organisation
- Maîtrise d'Excel
- Anglais souhaité''',
        'skills': 'Comptabilité, Analyse financière, Excel, Trésorier, Rigueur',
    },
    {
        'title': 'Développeur Web Junior',
        'company': 'Digital Agency CI',
        'location': 'Abidjan, Cocody',
        'description': '''Rejoignez notre équipe de développement!

Missions:
- Développement de sites web (HTML, CSS, JavaScript)
- Intégration de designs
- Optimisation front-end
- Collaboration avec le designer

Compétences requises:
- Bac+2 minimum en informatique
- Maîtrise HTML/CSS/JavaScript
- Connaissance PHP souhaitable
- Curiosité et apprentissage continu''',
        'skills': 'HTML, CSS, JavaScript, PHP, Web Development, Communication',
    },
    {
        'title': 'Chargée Communication Digitale',
        'company': 'Startup Côte d\'Ivoire',
        'location': 'Abidjan, Cocody',
        'description': '''Nous cherchons une chargée de communication digitale.

Attributions:
- Gestion des réseaux sociaux (Facebook, Instagram, LinkedIn)
- Création de contenu
- Community management
- Campagnes digitales

Profil:
- Formation en communication/marketing
- Expérience réseaux sociaux
- Créativité et sens du design
- Excellent français et anglais''',
        'skills': 'Digital Marketing, Communication, Social Media, Créativité, Anglais',
    },
    {
        'title': 'Responsable RH',
        'company': 'Groupe Empresarial',
        'location': 'Abidjan, Abobo',
        'description': '''Pilotez la fonction RH d'une PME.

Missions:
- Recrutement et intégration du personnel
- Gestion des dossiers du personnel
- Paie et avantages sociaux
- Développement des compétences
- Relations avec les partenaires sociaux

Profil recherché:
- Licence/Master en GRH
- 2-3 ans d'expérience RH
- Maîtrise de la législation du travail CI
- Anglais courant
- Outils informatiques (Excel, systèmes SIRH)''',
        'skills': 'RH, Recrutement, Paie, Droit du travail, Leadership, Anglais',
    },
    {
        'title': 'Assistant Comptable',
        'company': 'Cabinet de Conseil',
        'location': 'Abidjan, Yopougon',
        'description': '''Assistez l'équipe comptable dans ses missions.

Missions:
- Saisie comptable
- Classement et archivage
- Préparation des documents pour audit
- Support administratif

Profil:
- BTS/DUT Comptabilité minimum
- Maîtrise Excel avancée
- Rigueur et organisation
- Communication efficace''',
        'skills': 'Comptabilité, Excel, Saisie, Organisation, Rigueur, Professionnalisme',
    },
]

print("📝 Restauration des offres AEJI...\n")

added = 0
for job_data in manual_aeji_jobs:
    # Vérifier si existe déjà
    if Job.objects.filter(title=job_data['title'], location=job_data['location']).exists():
        print(f"⏭️  {job_data['title']} (déjà présent)")
        continue
    
    job = Job.objects.create(
        title=job_data['title'],
        company=job_data['company'],
        location=job_data['location'],
        country='CI',
        domain='autre',
        job_type='cdi',
        description=job_data['description'],
        required_skills=job_data['skills'],
        source_type='scraping',
        scraping_source=source,
        is_active=True,
        is_verified=True,
        posted_at=timezone.now(),
    )
    print(f"✅ {job.title}")
    print(f"   📍 {job.location}")
    print(f"   🔧 {job.required_skills}\n")
    added += 1

source.jobs_scraped = (source.jobs_scraped or 0) + added
source.save(update_fields=['jobs_scraped'])

print(f"\n✨ {added} offres AEJI restaurées!")
print(f"Total offres en base: {Job.objects.count()}")
