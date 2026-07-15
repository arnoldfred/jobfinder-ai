"""python manage.py seed_data"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from datetime import date, timedelta
from django.utils import timezone

User = get_user_model()

JOBS = [
    dict(title="Développeur Backend Python", company="CInet Technologies", location="Abidjan, Plateau", country="CI",
         domain="it", job_type="cdi", description="Nous recrutons un Développeur Backend Python pour rejoindre notre équipe tech en pleine croissance. Vous concevrez et maintiendrez des APIs robustes pour nos clients entreprises.",
         missions="- Développer et maintenir des APIs REST avec Django/FastAPI\n- Concevoir les architectures de données\n- Code review et mentorat des juniors\n- Collaboration avec les équipes front-end",
         requirements="3+ ans d'expérience Python. Maîtrise Django REST Framework. Connaissance des bases PostgreSQL et Redis. Bon niveau en Git.",
         required_skills="Python, Django, PostgreSQL, REST API, Git, Docker", salary_min=400000, salary_max=650000, salary_currency="FCFA", is_featured=True),
    dict(title="Data Analyst", company="Orange Côte d'Ivoire", location="Abidjan, Marcory", country="CI",
         domain="data", job_type="cdi", description="Orange CI cherche un Data Analyst pour analyser les données de notre réseau de 14 millions d'abonnés et guider les décisions stratégiques de la direction.",
         missions="- Construire des tableaux de bord de performance\n- Analyser les comportements clients\n- Préparer des rapports pour la direction\n- Identifier les opportunités de croissance",
         requirements="Bac+4/5 statistiques ou informatique. 2+ ans expérience analytique. Maîtrise SQL indispensable.",
         required_skills="SQL, Python, Tableau, Excel, Power BI, Statistiques", salary_min=350000, salary_max=550000, salary_currency="FCFA", is_featured=True),
    dict(title="Responsable Marketing Digital", company="Jumia CI", location="Abidjan, Cocody", country="CI",
         domain="marketing", job_type="cdi", description="Jumia CI recrute un Responsable Marketing Digital pour piloter notre stratégie digitale et augmenter notre présence en ligne sur le marché ivoirien.",
         missions="- Gérer les campagnes Google Ads et Meta Ads\n- Piloter le SEO/SEA\n- Analyser les performances et optimiser le ROI\n- Coordonner avec l'équipe contenu",
         requirements="3+ ans en marketing digital. Expérience e-commerce appréciée. Certifications Google/Meta souhaitées.",
         required_skills="Google Ads, Meta Ads, SEO, Analytics, CRM, Excel", salary_min=300000, salary_max=500000, salary_currency="FCFA"),
    dict(title="Comptable Senior", company="Cabinet Audit & Conseil CI", location="Abidjan, Zone 4", country="CI",
         domain="finance", job_type="cdi", description="Cabinet d'expertise comptable recherche un Comptable Senior pour gérer un portefeuille clients PME/ETI et superviser une équipe de 3 collaborateurs.",
         missions="- Tenue et révision des comptabilités\n- Établissement des déclarations fiscales\n- Supervision des collaborateurs\n- Conseil client",
         requirements="DSCG ou équivalent. 5+ ans en cabinet. Maîtrise du SYSCOHADA révisé. Rigueur et sens du client.",
         required_skills="SYSCOHADA, Sage Comptabilité, Fiscalité CI, Contrôle interne, Excel", salary_min=450000, salary_max=700000, salary_currency="FCFA"),
    dict(title="UX/UI Designer", company="Digitech Africa", location="Abidjan, Cocody 2 Plateaux", country="CI",
         domain="design", job_type="cdi", description="Startup fintech en forte croissance recherche un UX/UI Designer créatif pour concevoir des expériences utilisateur innovantes pour notre application mobile.",
         missions="- Recherche utilisateur (interviews, tests)\n- Wireframes et prototypes Figma\n- Design system et composants réutilisables\n- Collaboration avec les développeurs",
         requirements="Portfolio solide indispensable. 2+ ans UX/UI. Maîtrise Figma. Sensibilité aux marchés africains.",
         required_skills="Figma, Adobe XD, User Research, Prototyping, Design System, HTML/CSS notions", salary_min=280000, salary_max=420000, salary_currency="FCFA"),
    dict(title="Chargé(e) de Recrutement", company="ManpowerGroup CI", location="Abidjan, Plateau", country="CI",
         domain="rh", job_type="cdi", description="ManpowerGroup recrute un(e) Chargé(e) de Recrutement pour gérer des missions de recrutement pour nos clients grands comptes dans les secteurs banque, télécom et FMCG.",
         missions="- Analyse des besoins clients\n- Sourcing et présélection des candidats\n- Conduite des entretiens\n- Gestion des relations candidats/clients",
         requirements="Bac+4 RH ou équivalent. 2+ ans en cabinet ou en entreprise. Excellent relationnel. Maîtrise des outils de sourcing.",
         required_skills="LinkedIn Recruiter, Entretiens, ATS, Droit du travail CI, Sourcing", salary_min=250000, salary_max=380000, salary_currency="FCFA"),
    dict(title="Ingénieur Génie Civil", company="Groupe SETACI", location="Abidjan / chantiers CI", country="CI",
         domain="btp", job_type="cdi", description="Groupe SETACI recrute un Ingénieur Génie Civil pour superviser des chantiers d'infrastructure routière et hydraulique à travers la Côte d'Ivoire.",
         missions="- Direction technique des chantiers\n- Suivi des plannings et budgets\n- Contrôle qualité des travaux\n- Coordination sous-traitants",
         requirements="Ingénieur ESTP, INPHB ou équivalent. 3+ ans chantiers. Mobilité géographique indispensable.",
         required_skills="AutoCAD, MS Project, Béton armé, Topographie, Management chantier", salary_min=500000, salary_max=800000, salary_currency="FCFA"),
    dict(title="Développeur Fullstack React/Node", company="Startupbootcamp Africa", location="Remote / Abidjan", country="CI",
         domain="it", job_type="remote", is_remote=True, description="Accélérateur de startups africaines recherche un Développeur Fullstack pour travailler sur plusieurs produits en mode remote avec des équipes distribuées.",
         missions="- Développer des fonctionnalités front (React) et back (Node.js)\n- Participer aux sprints Agile\n- Contribuer à l'architecture technique",
         requirements="3+ ans full-stack. Portfolio GitHub requis. Autonomie totale en remote. Bonne communication écrite.",
         required_skills="React, Node.js, TypeScript, MongoDB, AWS, Docker, GraphQL", salary_min=500, salary_max=900, salary_currency="USD", salary_display_text="500–900 USD/mois (Remote"),
    dict(title="Stagiaire Analyste Financier", company="Société Générale CI", location="Abidjan, Plateau", country="CI",
         domain="finance", job_type="stage", description="Société Générale CI offre un stage de 6 mois au sein de sa direction financière pour accompagner les équipes dans l'analyse des performances et la préparation des reportings.",
         missions="- Aide à la préparation des reportings mensuels\n- Analyse des indicateurs financiers\n- Modélisation Excel",
         requirements="Étudiant Bac+4/5 finance, gestion ou équivalent. Rigoureux, analytique, maîtrise Excel avancée.",
         required_skills="Excel avancé, Comptabilité, Modélisation financière, PowerPoint"),
    dict(title="Chef de Projet IT", company="BICICI Banque", location="Abidjan, Plateau", country="CI",
         domain="it", job_type="cdi", description="La BICICI recrute un Chef de Projet IT pour piloter la transformation digitale de ses processus bancaires et coordonner les équipes techniques et métiers.",
         missions="- Pilotage de projets SI en mode Agile/cycle en V\n- Coordination équipes IT et métiers\n- Gestion des budgets et délais\n- Conduite du changement",
         requirements="5+ ans gestion de projets IT. Certifications PMP ou PRINCE2 appréciées. Secteur bancaire souhaité.",
         required_skills="Gestion de projet, Agile/Scrum, MS Project, JIRA, Banque, Change management", salary_min=650000, salary_max=950000, salary_currency="FCFA", is_featured=True),
]


class Command(BaseCommand):
    help = 'Seed database with realistic sample data'

    def handle(self, *args, **kwargs):
        from jobs.models import Job, JobSource
        from accounts.models import UserProfile, Skill, Experience, Education
        from employers.models import EmployerProfile

        self.stdout.write('🌱 Seeding...')

        # Sources
        src, _ = JobSource.objects.get_or_create(
            name='Agence Emploi Jeunes CI',
            defaults={'url': 'https://agenceemploijeunes.ci/site', 'region': "Côte d'Ivoire"}
        )

        # Seed jobs
        count = 0
        for jd in JOBS:
            if not Job.objects.filter(title=jd['title'], company=jd['company']).exists():
                jd.setdefault('missions', '')
                jd.setdefault('requirements', '')
                jd.setdefault('nice_to_have', '')
                jd.setdefault('company_about', '')
                jd.setdefault('salary_display_text', '')
                jd.setdefault('is_featured', False)
                jd.setdefault('is_remote', False)
                jd.setdefault('salary_min', None)
                jd.setdefault('salary_max', None)
                jd.setdefault('salary_currency', 'FCFA')
                jd.setdefault('deadline', date.today() + timedelta(days=30))
                Job.objects.create(
                    source_type='scraping',
                    scraping_source=src,
                    is_active=True,
                    is_verified=True,
                    **jd
                )
                count += 1
        self.stdout.write(f'  ✓ {count} offres créées')

        # Demo user (chercheur d'emploi)
        user, created = User.objects.get_or_create(
            email='demo@jobfinder.ai',
            defaults={
                'username': 'demo@jobfinder.ai',
                'first_name': 'Kouassi', 'last_name': 'Koffi',
                'role': 'jobseeker', 'country': 'CI', 'plan': 'free',
            }
        )
        if created:
            user.set_password('Demo2025!')
            user.save()

        profile, _ = UserProfile.objects.get_or_create(user=user, defaults={
            'location': 'Abidjan, Cocody',
            'desired_title': 'Développeur Backend Python',
            'summary': 'Développeur Python avec 3 ans d\'expérience en développement web et APIs REST. Passionné par les technologies africaines et le fintech.',
        })
        for name, cat in [('Python','technical'),('Django','technical'),('SQL','technical'),('Git','tool'),('Docker','tool'),('React','technical'),('Français','language'),('Anglais','language')]:
            Skill.objects.get_or_create(profile=profile, name=name, defaults={'category': cat})
        if not profile.experiences.exists():
            Experience.objects.create(
                profile=profile, title='Développeur Python Junior', company='Startup CI',
                location='Abidjan', start_date=date(2022,1,1), is_current=True,
                description='Développement d\'APIs REST pour une plateforme e-commerce locale.',
                technologies='Python, Django, PostgreSQL, Redis'
            )
        if not profile.educations.exists():
            Education.objects.create(
                profile=profile, degree='Licence Informatique',
                institution='INPHB — Institut National Polytechnique Houphouët-Boigny',
                location='Yamoussoukro, CI', start_year=2018, end_year=2021, gpa='Mention Bien'
            )
        profile.compute_completion()
        self.stdout.write(f'  ✓ Compte démo: demo@jobfinder.ai / Demo2025!')

        # Demo employer
        emp_user, created = User.objects.get_or_create(
            email='recruteur@cinettech.ci',
            defaults={
                'username': 'recruteur@cinettech.ci',
                'first_name': 'Adjoua', 'last_name': 'Konan',
                'role': 'employer', 'country': 'CI',
            }
        )
        if created:
            emp_user.set_password('Recruteur2025!')
            emp_user.save()
        EmployerProfile.objects.get_or_create(user=emp_user, defaults={
            'company_name': 'CInet Technologies',
            'company_description': 'Éditeur de logiciels ivoirien spécialisé dans les solutions fintech et e-commerce pour l\'Afrique de l\'Ouest.',
            'industry': 'Technologies de l\'information', 'location': 'Abidjan, Plateau',
            'company_size': '51-200',
        })
        self.stdout.write(f'  ✓ Compte recruteur: recruteur@cinettech.ci / Recruteur2025!')

        # Admin
        if not User.objects.filter(email='admin@jobfinder.ai').exists():
            User.objects.create_superuser(
                username='admin@jobfinder.ai',
                email='admin@jobfinder.ai',
                password='Admin2025!',
                first_name='Admin', last_name='JobFinder',
                role='admin'
            )
            self.stdout.write('  ✓ Admin: admin@jobfinder.ai / Admin2025!')

        self.stdout.write(self.style.SUCCESS('\n✅ Seed terminé avec succès !'))
