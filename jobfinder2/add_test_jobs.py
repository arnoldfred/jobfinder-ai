#!/usr/bin/env python
"""
Ajoute des offres de TEST avec les vraies données (+skills correctes).
Pour démontrer le système avec des offres réelles bien scrappées.
"""
import os
import sys
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jobfinder.settings")
django.setup()

from jobs.models import Job, JobSource
from django.utils import timezone

# Source manuelle
source, _ = JobSource.objects.get_or_create(
    name='Données Manuelles/Test',
    defaults={'url': 'http://localhost:8000/jobs', 'region': "Côte d'Ivoire"}
)

test_jobs = [
    {
        'title': 'Développeur Python Django',
        'company': 'TechStart CI',
        'location': 'Abidjan, Plateau',
        'country': 'CI',
        'domain': 'it',
        'job_type': 'cdi',
        'description': '''Nous cherchons un développeur Python/Django pour rejoindre notre équipe.

Missions:
- Développement d'applications web avec Django
- Intégration API REST et GraphQL
- Optimisation des bases de données PostgreSQL
- Déploiement sur AWS/Docker

Profil:
- 2-3 ans d'expérience avec Django
- Connaissances en SQL et PostgreSQL
- Maîtrise de Git et contrôle de version
- Pratique de Docker et déploiement

Salaire: 1.200.000 - 1.800.000 FCFA
        ''',
        'required_skills': 'Python, Django, PostgreSQL, Docker, AWS, REST API, Git',
    },
    {
        'title': 'Data Analyst / Reporting',
        'company': 'FinanceCI Solutions',
        'location': 'Abidjan, Cocody',
        'country': 'CI',
        'domain': 'data',
        'job_type': 'cdi',
        'description': '''Rejoignez notre équipe Finance pour analyser et rapporter les données.

Missions:
- Création de rapports et dashboards avec Tableau/Power BI
- Analyse des données financières avec SQL et Python
- Automatisation des processus de reporting
- Support des stakeholders pour l'analyse de données

Profil:
- 2-4 ans en data analysis ou finance
- Expert en SQL et Power BI/Tableau  
- Pratique de Python (pandas, numpy)
- Excellente communication

Salaire: 1.400.000 - 1.900.000 FCFA
        ''',
        'required_skills': 'SQL, Tableau, Power BI, Python, pandas, Excel avancé, Data Analysis',
    },
    {
        'title': 'Développeur Frontend React.js',
        'company': 'WebDesign Agency',
        'location': 'Abidjan, Yopougon',
        'country': 'CI',
        'domain': 'it',
        'job_type': 'cdi',
        'description': '''Nous recherchons un développeur React expérimenté.

Missions:
- Développement d'interfaces modernes avec React
- Intégration avec APIs REST
- Responsive design et optimisation UX
- Tests unitaires et E2E avec Jest/Cypress

Compétences requises:
- 2-3 ans avec React et JavaScript/TypeScript
- Maîtrise de HTML/CSS et frameworks UI
- Expérience avec npm/yarn et webpack
- Connaissance de Git

Salaire: 900.000 - 1.400.000 FCFA
        ''',
        'required_skills': 'JavaScript, React, TypeScript, HTML, CSS, REST API, Jest, Git',
    },
    {
        'title': 'Responsable Comptabilité',
        'company': 'Cabinet Audit & Finance',
        'location': 'Abidjan, Plateau',
        'country': 'CI',
        'domain': 'finance',
        'job_type': 'cdi',
        'description': '''Pilotez la comptabilité générale et analytique.

Attributions:
- Gestion complète de la comptabilité (saisie, rapprochement)
- Préparation des états financiers mensuels
- Contrôle budgétaire et analyse de variance
- Audit interne et conformité réglementaire

Profil recherché:
- Diplôme Bac+3 minimum (Comptabilité/Finance)
- 3-5 ans d'expérience en comptabilité générale
- Maîtrise de SAP ou ERP similaire
- Anglais courant indispensable

Salaire: 1.500.000 - 2.200.000 FCFA
        ''',
        'required_skills': 'Comptabilité, SAP, SQL, Excel avancé, Audit, Fiscal, Finance',
    },
    {
        'title': 'Chef de Projet Digital',
        'company': 'Consulting Group CI',
        'location': 'Abidjan, Abobo',
        'country': 'CI',
        'domain': 'marketing',
        'job_type': 'cdi',
        'description': '''Pilotez des projets digitaux de transformation.

Responsabilités:
- Gestion budgétaire et planning des projets
- Coordination avec équipes techniques et métier
- Suivi des indicateurs de performance
- Reporting aux stakeholders

Profil:
- Bac+4/5 en Management de Projet ou IT
- 3-4 ans en gestion de projet (Agile/Scrum)
- Certifications PRINCE2 ou PMP appréciées
- Anglais courant et compétences de communication

Salaire: 1.600.000 - 2.000.000 FCFA
        ''',
        'required_skills': 'Gestion de projet, Agile, Scrum, Jira, Communication, Leadership',
    }
]

print("📝 Ajout des offres de test avec vraies compétences...\n")

for job_data in test_jobs:
    # Vérifier si existe déjà
    if Job.objects.filter(title=job_data['title']).exists():
        print(f"⏭️  {job_data['title']} (déjà en base)")
        continue
    
    job = Job.objects.create(
        title=job_data['title'],
        company=job_data['company'],
        location=job_data['location'],
        country=job_data['country'],
        domain=job_data['domain'],
        job_type=job_data['job_type'],
        description=job_data['description'],
        required_skills=job_data['required_skills'],
        source_type='manual',
        scraping_source=source,
        is_active=True,
        is_verified=True,
        posted_at=timezone.now(),
    )
    print(f"✅ {job.title}")
    print(f"   Skills: {job.required_skills}\n")

print("\n✨ Offres de test ajoutées!")
print("\nMaintenant les éléments ont des compétences réelles détectées:")
print("- Développeur Python Django → Python, Django, PostgreSQL, Docker...")
print("- Data Analyst → SQL, Tableau, Power BI, pandas...")
print("- Développeur React → JavaScript, React, TypeScript, HTML CSS...")
print("- Comptabilité → Comptabilité, SAP, Fiscal...")
print("\nTestez le matching: http://127.0.0.1:8000/jobs/")
