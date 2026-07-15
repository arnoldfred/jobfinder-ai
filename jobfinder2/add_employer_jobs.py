#!/usr/bin/env python
"""
Script pour ajouter plusieurs offres d'emploi via des comptes recruteurs
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobfinder.settings')
django.setup()

from accounts.models import User
from jobs.models import Job
from django.utils import timezone
from datetime import timedelta

# Données des offres à créer
OFFERS = [
    {
        'title': 'Développeur Python Senior',
        'company': 'TechCorp Abidjan',
        'company_about': 'Leader en solutions digitales en Côte d\'Ivoire',
        'location': 'Abidjan, Plateau',
        'country': 'CI',
        'job_type': 'cdi',
        'domain': 'it',
        'description': '''Nous recrutons un Développeur Python Senior pour rejoindre notre équipe dynamique.

C est une excellente opportunité pour contribuer à des projets innovants et avoir un réel impact sur la transformation digitale en Afrique.

Vous travaillerez avec:
- Django 4.0+
- PostgreSQL, Redis
- Docker & Kubernetes
- APIs REST GraphQL
- Tests unitaires & intégration''',
        'missions': '''- Développer et maintenir des applications Python/Django
- Concevoir des architectures scalables
- Mentorer les développeurs juniors
- Participer aux code reviews
- Contribuer à l\'amélioration continue des processus''',
        'requirements': '''- 5+ ans d\'expérience en développement Python
- Maîtrise de Django et des bonnes pratiques
- Connaissance de PostgreSQL et Redis
- Familiarité avec Docker
- Excellent communication en français et anglais
- Capacité à travailler en équipe agile''',
        'required_skills': 'Python, Django, PostgreSQL, Redis, Docker, REST API, Git',
        'nice_to_have': 'Kubernetes, GraphQL, AWS, Machine Learning',
        'salary_min': 2500000,
        'salary_max': 3500000,
        'salary_currency': 'FCFA',
        'deadline_days': 30,
    },
    {
        'title': 'Data Scientist / Machine Learning Engineer',
        'company': 'AI Solutions Africa',
        'company_about': 'Startup spécialisée en IA et analytics pour PME africaines',
        'location': 'Abidjan, Cocody',
        'country': 'CI',
        'job_type': 'cdi',
        'domain': 'data',
        'description': '''Rejoignez notre équipe de data scientists pour créer des solutions IA impactantes.

Nous travaillons sur:
- Prédiction de comportement clients
- Optimisation de processus métier
- Computer Vision
- NLP et chatbots

Vous aurez accès à des datasets réels et à une infrastructure moderne.''',
        'missions': '''- Développer et déployer des modèles ML en production
- Analyser des datasets complexes
- Créer des dashboards et visualisations
- Collaborer avec les équipes produit
- Documenter les processes et méthodologies''',
        'requirements': '''- Master en informatique, mathématiques ou domaine connexe
- 3+ ans d\'expérience en Data Science / ML
- Expertise en Python (pandas, scikit-learn, TensorFlow)
- Connaissance de SQL
- Expérience avec des outils de BI
- Anglais courant''',
        'required_skills': 'Python, Machine Learning, pandas, scikit-learn, SQL, Statistics, Jupyter',
        'nice_to_have': 'TensorFlow, Spark, AWS SageMaker, MLflow, Docker',
        'salary_min': 2800000,
        'salary_max': 4000000,
        'salary_currency': 'FCFA',
        'deadline_days': 25,
    },
    {
        'title': 'Développeur React / Frontend Senior',
        'company': 'Digital Revolution SARL',
        'company_about': 'Agence web créative avec clients internationaux',
        'location': 'Abidjan, Marcory',
        'country': 'CI',
        'job_type': 'cdi',
        'domain': 'it',
        'description': '''Nous cherchons un Développeur React Senior passionné par créer des interfaces exceptionnelles.

Vous serez responsable de:
- Développer des applications web modernes et réactives
- Optimiser les performances frontend
- Collaborer avec designers et backend
- Définir les standards de qualité''',
        'missions': '''- Coder en React/TypeScript
- Créer des components réutilisables
- Gérer l\'état avec Redux ou Context
- Tester le code (Jest, React Testing Library)
- Optimiser les performances et l\'accessibilité''',
        'requirements': '''- 4+ ans d\'expérience React
- Maîtrise de TypeScript
- Connaissance de Webpack/Vite
- Familiarity with REST APIs et fetch
- Git et méthodologies agile
- Expérience en responsive design''',
        'required_skills': 'React, TypeScript, JavaScript, CSS, HTML, REST API, Git',
        'nice_to_have': 'Next.js, GraphQL, Redux, Testing, Figma',
        'salary_min': 2200000,
        'salary_max': 3200000,
        'salary_currency': 'FCFA',
        'deadline_days': 20,
    },
    {
        'title': 'Responsable Marketing Digital & Growth',
        'company': 'E-Commerce Plus',
        'company_about': 'Plateforme de commerce électronique en croissance rapide',
        'location': 'Abidjan, Plateau',
        'country': 'CI',
        'job_type': 'cdi',
        'domain': 'marketing',
        'description': '''Pilotez notre stratégie digitale et accéléreriez notre croissance.

Contexte:
- Startup en phase de scaling
- Présence multi-canaux (réseaux sociaux, email, paid ads)
- Équipe petite mais motivée
- Budget marketing significatif''',
        'missions': '''- Définir et exécuter la stratégie marketing digitale
- Gérer les campagnes paid (Google Ads, Facebook)
- Optimiser le funnel de conversion
- Analyser les métriques KPI
- Manager l\'équipe marketing''',
        'requirements': '''- 3+ ans en marketing digital
- Google Analytics, SEO/SEM
- Gestion de réseaux sociaux
- Connaissance des outils : Hubspot, GTM
- Excellente communication
- Français et anglais courants''',
        'required_skills': 'Digital Marketing, Google Analytics, SEO, SEM, Social Media, Content Marketing',
        'nice_to_have': 'Growth Hacking, A/B Testing, Conversion Rate Optimization, Figma',
        'salary_min': 1800000,
        'salary_max': 2600000,
        'salary_currency': 'FCFA',
        'deadline_days': 28,
    },
    {
        'title': 'Gestionnaire de Projet / Product Manager',
        'company': 'Innovation Hub CI',
        'company_about': 'Hub d\'innovation et d\'incubation de startups',
        'location': 'Abidjan, Deux-Plateaux',
        'country': 'CI',
        'job_type': 'cdi',
        'domain': 'autre',
        'description': '''Rejoignez Innovation Hub en tant que Product Manager pour piloter nos projets.

Nous avons:
- 8-10 projets en portefeuille
- Équipes techniques distribuées
- Clients variés (PME, gouvernement, ONG)
- Méthodologie agile/Scrum''',
        'missions': '''- Définir la roadmap produit
- Gérer les priorités et sprints
- Communiquer avec stakeholders
- Analyser les retours utilisateurs
- Assurer la qualité livrables''',
        'requirements': '''- 4+ ans en gestion de projet agile
- Certifications SCRUM/Agile appréciées
- Maîtrise de Jira, Confluence
- Bonnes connaissances techniques
- Excellente communication
- Anglais courant obligatoire''',
        'required_skills': 'Project Management, Agile, Scrum, Jira, Communication, Stakeholder Management',
        'nice_to_have': 'Product Strategy, UX Understanding, Analytics, Leadership',
        'salary_min': 2000000,
        'salary_max': 2800000,
        'salary_currency': 'FCFA',
        'deadline_days': 35,
    },
]

def create_or_get_employer(email, first_name, last_name, company_name):
    """Crée ou récupère un compte recruteur"""
    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            'username': email.split('@')[0],
            'first_name': first_name,
            'last_name': last_name,
            'role': 'employer',
            'is_active': True,
        }
    )
    if created:
        user.set_password('RecruteurTest123!')
        user.save()
        print(f"✅ Créé: {email}")
    else:
        print(f"ℹ️  Existe déjà: {email}")
    return user

def add_jobs():
    """Ajoute les offres"""
    # Créer les comptes recruteurs
    employers = [
        create_or_get_employer('techcorp@jobfinder.ci', 'Alain', 'Kouamé', 'TechCorp'),
        create_or_get_employer('aisolutions@jobfinder.ci', 'Marie', 'Diallo', 'AI Solutions'),
        create_or_get_employer('digital@jobfinder.ci', 'Jean', 'Traore', 'Digital Revolution'),
        create_or_get_employer('ecommerce@jobfinder.ci', 'Fatima', 'Sow', 'E-Commerce Plus'),
        create_or_get_employer('innovationhub@jobfinder.ci', 'Pierre', 'Mensah', 'Innovation Hub'),
    ]

    # Ajouter les offres
    for i, offer_data in enumerate(OFFERS):
        employer = employers[i % len(employers)]
        
        deadline = timezone.now() + timedelta(days=offer_data['deadline_days'])
        
        job, created = Job.objects.get_or_create(
            title=offer_data['title'],
            company=offer_data['company'],
            employer=employer,
            source_type='employer',
            defaults={
                'company_about': offer_data['company_about'],
                'location': offer_data['location'],
                'country': offer_data['country'],
                'job_type': offer_data['job_type'],
                'domain': offer_data['domain'],
                'description': offer_data['description'],
                'missions': offer_data['missions'],
                'requirements': offer_data['requirements'],
                'required_skills': offer_data['required_skills'],
                'nice_to_have': offer_data['nice_to_have'],
                'salary_min': offer_data.get('salary_min'),
                'salary_max': offer_data.get('salary_max'),
                'salary_currency': offer_data['salary_currency'],
                'deadline': deadline.date(),
                'is_active': True,
                'is_verified': True,
            }
        )
        
        if created:
            print(f"✅ Offre créée: {job.title} ({employer.email})")
        else:
            print(f"ℹ️  Offre existe: {job.title}")

    print(f"\n{'='*60}")
    print(f"✅ Total: {len(employers)} recruteurs, {len(OFFERS)} offres ajoutées")
    print(f"{'='*60}")

if __name__ == '__main__':
    add_jobs()
