#!/usr/bin/env python
"""
Script pour ajouter 10 nouvelles offres pour CineTech
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobfinder.settings')
django.setup()

from accounts.models import User
from jobs.models import Job
from django.utils import timezone
from datetime import timedelta

# Offres pour CineTech
OFFERS = [
    {
        'title': 'Développeur Backend Python/FastAPI',
        'company': 'CineTech',
        'company_about': 'Leader en solutions audiovisuelle et streaming video',
        'location': 'Abidjan, Plateau',
        'country': 'CI',
        'job_type': 'cdi',
        'domain': 'it',
        'description': '''Rejoignez CineTech en tant que développeur backend pour construire nos APIs et services cloud.

Nous travaillons avec :
- FastAPI et Django
- PostgreSQL, Redis
- Docker & containerization
- Microservices et gestion de vidéos

Vous participerez à la création de solutions innovantes pour l\'industrie audiovisuelle africaine.''',
        'missions': '''- Développer et maintenir les APIs backend
- Optimiser les performances et scalabilité
- Collaborer avec les équipes frontend et DevOps
- Implémenter les bonnes pratiques de sécurité
- Participer au design d\'architecture''',
        'requirements': '''- 3+ ans d\'expérience Python
- Excellente maîtrise de FastAPI ou Django REST
- PostgreSQL et Redis
- Git et méthodologies agile
- Anglais courant''',
        'required_skills': 'Python, FastAPI, PostgreSQL, Redis, Docker, API REST, Git',
        'nice_to_have': 'Kubernetes, Streaming video, AWS, gRPC',
        'salary_min': 2000000,
        'salary_max': 3200000,
        'deadline_days': 35,
    },
    {
        'title': 'Ingénieur DevOps / Cloud',
        'company': 'CineTech',
        'company_about': 'Plateforme de streaming video innovante en Afrique',
        'location': 'Abidjan, Deux-Plateaux',
        'country': 'CI',
        'job_type': 'cdi',
        'domain': 'it',
        'description': '''CineTech cherche un DevOps engineer pour gérer son infrastructure cloud.

Stack :
- AWS (EC2, S3, CloudFront, Lambda)
- Kubernetes et Docker
- CI/CD avec GitLab/GitHub Actions
- Monitoring et logging
- Infrastructure as Code (Terraform)''',
        'missions': '''- Configurer et maintenir l\'infrastructure AWS
- Déployer et orchestrer avec Kubernetes
- Implémenter les pipelines CI/CD
- Automatiser les opérations
- Assurer la sécurité et disponibilité''',
        'requirements': '''- 4+ ans en DevOps/Cloud
- AWS (obligatoire)
- Kubernetes et Docker
- Scripting (Bash, Python)
- IaC avec Terraform
- Excellent en troubleshooting''',
        'required_skills': 'AWS, Kubernetes, Docker, Terraform, Linux, CI/CD, Monitoring',
        'nice_to_have': 'ArgoCD, Prometheus, ELK stack, Security', 
        'salary_min': 2200000,
        'salary_max': 3400000,
        'deadline_days': 30,
    },
    {
        'title': 'Développeur Frontend React/Next.js Senior',
        'company': 'CineTech',
        'company_about': 'Créateur de contenu et distribution vidéo numérique',
        'location': 'Abidjan, Plateau',
        'country': 'CI',
        'job_type': 'cdi',
        'domain': 'it',
        'description': '''CineTech recrute un développeur frontend expérimenté pour construire des interfaces modernes et réactives.

Technologies :
- React 18+ avec TypeScript
- Next.js pour SSR/SSG
- Tailwind CSS et design system
- State management (Redux, Zustand)
- Testing (Jest, React Testing Library)''',
        'missions': '''- Développer les interfaces utilisateur
- Optimiser les performances et UX
- Créer un design system à l\'échelle
- Collaborer avec designers et backend
- Mentorer les développeurs juniors''',
        'requirements': '''- 5+ ans avec React
- TypeScript (obligatoire)
- Next.js ou Remix
- Connaissances avancées CSS
- Git et agile
- Sense du design UI/UX''',
        'required_skills': 'React, TypeScript, Next.js, CSS, JavaScript, Testing, Git',
        'nice_to_have': 'GraphQL, Storybook, Performance optimization, Accessibility',
        'salary_min': 2100000,
        'salary_max': 3300000,
        'deadline_days': 32,
    },
    {
        'title': 'Data Engineer / Analytics',
        'company': 'CineTech',
        'company_about': 'Plateforme video avec millions d\'utilisateurs en Afrique',
        'location': 'Abidjan, Cocody',
        'country': 'CI',
        'job_type': 'cdi',
        'domain': 'data',
        'description': '''CineTech a besoin d\'un Data Engineer pour gérer et analyser d\'énormes volumes de données vidéo et utilisateurs.

Stack :
- Airflow pour l\'orchestration
- Spark pour le traitement
- Data Lake avec S3 et Parquet
- ClickHouse ou BigQuery
- Python et SQL''',
        'missions': '''- Concevoir des pipelines ETL/ELT
- Optimiser les requêtes et performance
- Créer des dashboards analytiques
- Gérer la qualité des données
- Documenter les processus''',
        'requirements': '''- 3+ ans en Data Engineering
- Python et SQL avancé
- Spark ou similaire
- Cloud (AWS/GCP)
- Airflow ou Prefect
- Anglais professionnel''',
        'required_skills': 'Python, SQL, Spark, Airflow, AWS, ETL, Data modeling',
        'nice_to_have': 'ClickHouse, Kafka, dbt, Machine Learning',
        'salary_min': 2300000,
        'salary_max': 3500000,
        'deadline_days': 28,
    },
    {
        'title': 'QA Engineer / Quality Automation',
        'company': 'CineTech',
        'company_about': 'Besoin de qualité impeccable pour 100% satisfaction utilisateur',
        'location': 'Abidjan, Plateau',
        'country': 'CI',
        'job_type': 'cdi',
        'domain': 'it',
        'description': '''CineTech cherche un QA Engineer pour assurer la qualité de ses services streaming.

Focus :
- Testing automation avec Selenium/Cypress
- API testing avec Postman/RestAssured
- Performance et load testing
- Manual testing approfondi
- Gestion de défauts et regression''',
        'missions': '''- Créer et maintenir les tests automatisés
- Planifier et exécuter les tests manuels
- Tester les APIs et services
- Rapporter et tracker les défauts
- Collaborer avec les développeurs''',
        'requirements': '''- 2+ ans en QA Automation
- Selenium ou Cypress
- Python ou Java
- SQL pour DBtesting
- Git
- Méthodologies agile''',
        'required_skills': 'Selenium, Python, API testing, SQL, Test management, Git',
        'nice_to_have': 'Cypress, Performance testing, Load testing, CI/CD integration',
        'salary_min': 1700000,
        'salary_max': 2500000,
        'deadline_days': 25,
    },
    {
        'title': 'Product Manager / Responsable Produit',
        'company': 'CineTech',
        'company_about': 'Diriger la vision produit d\'une plateforme vidéo innovante',
        'location': 'Abidjan, Plateau',
        'country': 'CI',
        'job_type': 'cdi',
        'domain': 'autre',
        'description': '''CineTech recrute un Product Manager pour piloter la roadmap produit et l\'expérience utilisateur.

Responsabilités :
- Définir la stratégie produit
- Analyser les données et retours utilisateurs
- Gérer les priorités et roadmap
- Collaborer avec design, tech et business
- Conduire les lancements de features''',
        'missions': '''- Owning la roadmap produit
- Écrire et valider les requirements
- Conduire les entretiens utilisateurs
- Analyser les métriques et KPIs
- Collaborer avec tous les teams''',
        'requirements': '''- 4+ ans en Product Management
- Background tech ou business
- Excellente communication
- Données et analytics
- Méthodologies agile
- Anglais courant''',
        'required_skills': 'Product strategy, Analytics, Agile, Communication, User research',
        'nice_to_have': 'Figma, SQL, Growth hacking, Video/streaming domain',
        'salary_min': 2200000,
        'salary_max': 3400000,
        'deadline_days': 35,
    },
    {
        'title': 'Développeur Mobile React Native',
        'company': 'CineTech',
        'company_about': 'Créer l\'app mobile pour des millions d\'Africa users',
        'location': 'Abidjan, Cocody',
        'country': 'CI',
        'job_type': 'cdi',
        'domain': 'it',
        'description': '''CineTech cherche un développeur React Native pour construire l\'application mobile streaming.

Stack :
- React Native avec TypeScript
- Expo ou React Native CLI
- Native modules et APIs
- Firebase ou backend custom
- Testing et performance''',
        'missions': '''- Développer features iOS et Android
- Optimiser les performances
- Intégrer les APIs backend
- Tester sur devices réels
- Gérer les releases App Store/Play Store''',
        'requirements': '''- 3+ ans React Native
- TypeScript (important)
- iOS et Android basics
- JavaScript expert
- Git et CI/CD
- Passion pour mobile''',
        'required_skills': 'React Native, TypeScript, JavaScript, Mobile development, Firebase',
        'nice_to_have': 'Expo, Native modules, Performance optimization, Analytics',
        'salary_min': 1900000,
        'salary_max': 2900000,
        'deadline_days': 30,
    },
    {
        'title': 'DevSecOps Engineer / Security Specialist',
        'company': 'CineTech',
        'company_about': 'Sécuriser les données et infrastructure d\'une plateforme avec millions utilisateurs',
        'location': 'Abidjan, Plateau',
        'country': 'CI',
        'job_type': 'cdi',
        'domain': 'it',
        'description': '''CineTech recrute un DevSecOps pour intégrer la sécurité à tous les niveaux.

Domaines :
- Vulnerability scanning et penetration testing
- Secure coding practices
- Infrastructure security
- Incident response
- Compliance (RGPD, etc)''',
        'missions': '''- Implémenter Security best practices
- Auditer code et infrastructure
- Gérer les vulnérabilités
- Conduire des security trainings
- Répondre aux incidents''',
        'requirements': '''- 4+ ans Security Engineering
- Linux et networking
- Cloud security (AWS)
- Vulnerability management
- Scripting/coding
- Certifications type OSCP/CEH appréciées''',
        'required_skills': 'Security, AWS, Linux, Vulnerability assessment, Incident response',
        'nice_to_have': 'Kubernetes security, Penetration testing, Compliance, SIEM',
        'salary_min': 2400000,
        'salary_max': 3600000,
        'deadline_days': 32,
    },
    {
        'title': 'Solutions Architect / Technical Lead',
        'company': 'CineTech',
        'company_about': 'Architected les solutions scalables pour la croissance d\'une unicorn africaine',
        'location': 'Abidjan, Plateau',
        'country': 'CI',
        'job_type': 'cdi',
        'domain': 'it',
        'description': '''CineTech recrute un Solutions Architect pour diriger l\'architecture technique.

Responsabilités :
- Concevoir les architectures évolutives
- Évaluer les technologies
- Mentor les teams d\'ingénierie
- Gérer les décisions techniques
- Optimiser coûts et performance''',
        'missions': '''- Owning l\'architecture globale
- Design des systems distribués
- Leadership technique du team
- Technology evaluation et selection
- Documentation et standards''',
        'requirements': '''- 7+ ans en engineering/architecture
- Expertise multiple technologies
- Leadership et mentoring
- Communication exceptionnelle
- Pensée business et technique
- Anglais courant''',
        'required_skills': 'Architecture, Distributed systems, Cloud, Leadership, Design patterns',
        'nice_to_have': 'Microservices, Event-driven, Video streaming, Scaling expertise',
        'salary_min': 2800000,
        'salary_max': 4200000,
        'deadline_days': 40,
    },
    {
        'title': 'Content Operations Manager',
        'company': 'CineTech',
        'company_about': 'Gérer les opérations de contenu vidéo à grande échelle',
        'location': 'Abidjan, Plateau',
        'country': 'CI',
        'job_type': 'cdi',
        'domain': 'autre',
        'description': '''CineTech cherche un Content Operations Manager pour optimiser son pipeline de contenu vidéo.

Activités :
- Gestion des workflows de contenu
- Coordination avec les créateurs et studios
- Optimisation des processus
- Gestion de projets
- Analytics et reporting''',
        'missions': '''- Gérer les workflows de publication
- Coordonner les partenaires contenu
- Optimiser les processus opérationnels
- Créer des dashboards de metrics
- Résoudre les blocages''',
        'requirements': '''- 3+ ans en content/project management
- Excellent organisation
- Gestion d\'équipes
- Analytics et reporting
- Tool management (Jira, etc)
- Adaptabilité et résilience''',
        'required_skills': 'Project management, Content operations, Analytics, Communication, Organisation',
        'nice_to_have': 'Video production knowledge, Automation, SQL basics, Leadership',
        'salary_min': 1600000,
        'salary_max': 2400000,
        'deadline_days': 28,
    },
]

def create_or_get_employer():
    """Créer ou récupérer le compte recruteur CineTech"""
    user, created = User.objects.get_or_create(
        email='recruteur@cinettech.ci',
        defaults={
            'username': 'cinettech_recruiter',
            'first_name': 'CineTech',
            'last_name': 'Recruitment',
            'role': 'employer',
            'is_active': True,
        }
    )
    if created:
        user.set_password('CineTechRecruteur2026!')
        user.save()
        print(f"✅ Créé: {user.email}")
    else:
        print(f"ℹ️  Existe déjà: {user.email}")
    return user

def add_jobs():
    """Ajoute les 10 offres"""
    employer = create_or_get_employer()
    
    print(f"\n📝 Ajout de {len(OFFERS)} offres pour CineTech...\n")
    
    for i, offer_data in enumerate(OFFERS, 1):
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
                'salary_currency': 'FCFA',
                'deadline': deadline.date(),
                'is_active': True,
                'is_verified': True,
            }
        )
        
        if created:
            print(f"  {i:2d}. ✅ {job.title}")
        else:
            print(f"  {i:2d}. ℹ️  {job.title} (existe déjà)")
    
    print(f"\n{'='*70}")
    print(f"✅ Total: 10 offres CineTech ajoutées avec succès!")
    print(f"{'='*70}")

if __name__ == '__main__':
    add_jobs()
