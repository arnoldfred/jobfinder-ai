import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobfinder.settings')

import django

django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils import timezone
from datetime import date, timedelta

from accounts.models import User, UserProfile, Skill, Experience, Education
from employers.models import EmployerProfile
from jobs.models import Job, SavedJob, SearchAlert, JobMatch
from applications.models import Application, Notification, JobInteraction, Message

UserModel = get_user_model()

preserved_emails = ['demo@jobfinder.ai', 'adjoua.konan@cinettech.ci', 'admin@jobfinder.ai']

for model in [Message, Notification, JobInteraction, SavedJob, SearchAlert, JobMatch, Application, Skill, Experience, Education, UserProfile, EmployerProfile, Job]:
    model.objects.all().delete()

UserModel.objects.exclude(email__in=preserved_emails).delete()

for name in ['jobseekers', 'employers', 'admins']:
    Group.objects.get_or_create(name=name)


def create_user(email, first_name, last_name, role, password):
    user, created = UserModel.objects.get_or_create(
        email=email,
        defaults={
            'username': email,
            'first_name': first_name,
            'last_name': last_name,
            'role': role,
            'country': 'CI',
        },
    )
    if created:
        user.set_password(password)
        user.save()
    else:
        user.first_name = first_name
        user.last_name = last_name
        user.role = role
        user.country = 'CI'
        user.save(update_fields=['first_name', 'last_name', 'role', 'country'])
    return user


def create_profile(user, location, desired_title, summary, phone, linkedin, github):
    profile, _ = UserProfile.objects.get_or_create(
        user=user,
        defaults={
            'location': location,
            'desired_title': desired_title,
            'summary': summary,
            'phone': phone,
            'linkedin_url': linkedin,
            'github_url': github,
        },
    )
    return profile


# Core accounts
create_user('demo@jobfinder.ai', 'Kouassi', 'Koffi', 'jobseeker', 'Demo2025!')
create_user('adjoua.konan@cinettech.ci', 'Adjoua', 'Konan', 'employer', 'Recruteur2025!')
admin_user = create_user('admin@jobfinder.ai', 'Admin', 'JobFinder', 'admin', 'Admin2025!')
admin_user.is_staff = True
admin_user.is_superuser = True
admin_user.save(update_fields=['is_staff', 'is_superuser'])

# Employers
employer_specs = [
    ('mariam.diakite@orange.ci', 'Mariam', 'Diakité', 'Orange Côte d’Ivoire', 'Télécom', 'Abidjan, Marcory', 'https://orangeci.com', '+225 07 10 20 30'),
    ('yves.kouassi@cinettech.ci', 'Yves', 'Kouassi', 'CinetTech', 'Technologie', 'Abidjan, Plateau', 'https://cinettech.ci', '+225 07 11 22 31'),
    ('nadia.bamba@jumia.ci', 'Nadia', 'Bamba', 'Jumia CI', 'E-commerce', 'Abidjan, Cocody', 'https://www.jumia.ci', '+225 07 12 23 32'),
    ('brahima.traore@setaci.ci', 'Brahima', 'Traoré', 'Groupe SETACI', 'BTP', 'Abidjan, Yopougon', 'https://setaci.ci', '+225 07 13 24 33'),
    ('awa.soro@manpower.ci', 'Awa', 'Soro', 'ManpowerGroup CI', 'RH', 'Abidjan, Plateau', 'https://manpowergroupci.com', '+225 07 14 25 34'),
    ('koffi.nguessan@dicom.ci', 'Koffi', 'N’Guessan', 'DICOM', 'Fintech', 'Abidjan, Riviera', 'https://dicom.ci', '+225 07 15 26 35'),
]

employers = []
for email, first, last, company, industry, location, website, phone in employer_specs:
    employer = create_user(email, first, last, 'employer', 'Recruit123!')
    EmployerProfile.objects.get_or_create(
        user=employer,
        defaults={
            'company_name': company,
            'company_website': website,
            'company_description': 'Entreprise locale active dans les services, la technologie et la transformation numérique.',
            'industry': industry,
            'location': location,
            'company_size': '51-200',
            'phone': phone,
        },
    )
    employers.append(employer)

# Additional employers (20 more)
extra_employer_specs = [
    ('nicolas.kone@itafrique.ci', 'Nicolas', 'Kone', 'IT Afrique', 'Technologie', 'Abidjan, Treichville', 'https://itafrique.ci', '+225 07 16 27 36'),
    ('mohamed.bah@africdata.ci', 'Mohamed', 'Bah', 'AfricData', 'Data', 'Abidjan, Koumassi', 'https://africdata.ci', '+225 07 17 28 37'),
    ('celine.ahoussi@softwave.ci', 'Celine', 'Ahoussi', 'SoftWave CI', 'Logiciels', 'Abidjan, Cocody', 'https://softwave.ci', '+225 07 18 29 38'),
    ('serge.yao@kapitalbank.ci', 'Serge', 'Yao', 'KapitalBank', 'Finance', 'Abidjan, Plateau', 'https://kapitalbank.ci', '+225 07 19 30 39'),
    ('karim.soro@horizonbuild.ci', 'Karim', 'Soro', 'Horizon Build', 'BTP', 'Abidjan, Yopougon', 'https://horizonbuild.ci', '+225 07 20 31 40'),
    ('patricia.bamba@greenlabs.ci', 'Patricia', 'Bamba', 'GreenLabs', 'Énergie', 'Abidjan, Riviera', 'https://greenlabs.ci', '+225 07 21 32 41'),
    ('donald.ouattara@novatech.ci', 'Donald', 'Ouattara', 'NovaTech', 'Technologie', 'Abidjan, Plateau', 'https://novatech.ci', '+225 07 22 33 42'),
    ('sarah.traore@medisys.ci', 'Sarah', 'Traore', 'MediSys', 'Santé', 'Abidjan, Marcory', 'https://medisys.ci', '+225 07 23 34 43'),
    ('abdoulaye.diallo@smartlog.ci', 'Abdoulaye', 'Diallo', 'SmartLog', 'Logistique', 'Abidjan, Port-Bouet', 'https://smartlog.ci', '+225 07 24 35 44'),
    ('fanta.konate@cloudix.ci', 'Fanta', 'Konate', 'Cloudix', 'Cloud', 'Abidjan, Cocody', 'https://cloudix.ci', '+225 07 25 36 45'),
    ('yacouba.mensah@agrihub.ci', 'Yacouba', 'Mensah', 'AgriHub', 'Agriculture', 'Bouaké', 'https://agrihub.ci', '+225 07 26 37 46'),
    ('amina.konan@calliope.ci', 'Amina', 'Konan', 'Calliope', 'Services', 'Abidjan, Angre', 'https://calliope.ci', '+225 07 27 38 47'),
    ('guy.loukou@cofinex.ci', 'Guy', 'Loukou', 'Cofinex', 'Fintech', 'Abidjan, Plateau', 'https://cofinex.ci', '+225 07 28 39 48'),
    ('mariame.soro@eduplus.ci', 'Mariame', 'Soro', 'EduPlus', 'Éducation', 'Yamoussoukro', 'https://eduplus.ci', '+225 07 29 40 49'),
    ('souleymane.kelly@neovest.ci', 'Souleymane', 'Kelly', 'NeoVest', 'Immobilier', 'Abidjan, Marcory', 'https://neovest.ci', '+225 07 30 41 50'),
    ('hawa.toure@pulsemedia.ci', 'Hawa', 'Toure', 'PulseMedia', 'Marketing', 'Abidjan, Cocody', 'https://pulsemedia.ci', '+225 07 31 42 51'),
    ('ismael.doumbia@qim.ci', 'Ismael', 'Doumbia', 'QIM', 'Industrie', 'San Pedro', 'https://qim.ci', '+225 07 32 43 52'),
    ('esther.kan@nextgen.ci', 'Esther', 'Kan', 'NextGen', 'Télécom', 'Abidjan, Riviera', 'https://nextgen.ci', '+225 07 33 44 53'),
    ('bakari.yapi@workforce.ci', 'Bakari', 'Yapi', 'Workforce CI', 'RH', 'Abidjan, Treichville', 'https://workforce.ci', '+225 07 34 45 54'),
    ('mohamed.traore@civis.ci', 'Mohamed', 'Traore', 'Civis', 'Conseil', 'Abidjan, Plateau', 'https://civis.ci', '+225 07 35 46 55'),
]
for email, first, last, company, industry, location, website, phone in extra_employer_specs:
    employer = create_user(email, first, last, 'employer', 'Recruit123!')
    EmployerProfile.objects.get_or_create(
        user=employer,
        defaults={
            'company_name': company,
            'company_website': website,
            'company_description': 'Entreprise active sur le terrain local avec un fort besoin de talents qualifiés.',
            'industry': industry,
            'location': location,
            'company_size': '51-200',
            'phone': phone,
        },
    )
    employers.append(employer)

# Candidates
candidate_specs = [
    ('amara.yao@jobfinder.ai', 'Amara', 'Yao', 'Développeur Backend Python', 'Abidjan, Cocody', 'Développeur backend passionné par les APIs, la fiabilité et l’automatisation.', 'https://linkedin.com/in/amara-yao', 'https://github.com/amara-yao', 'Python, Django, SQL, Docker'),
    ('fatou.kouassi@jobfinder.ai', 'Fatou', 'Kouassi', 'Data Analyst', 'Abidjan, Marcory', 'Analyste de données avec 5 ans d’expérience sur la performance, l’optimisation et les tableaux de bord.', 'https://linkedin.com/in/fatou-kouassi', 'https://github.com/fatou-kouassi', 'SQL, Power BI, Excel, Python'),
    ('jean.diarra@jobfinder.ai', 'Jean', 'Diarra', 'Product Manager', 'Yamoussoukro', 'PM expérimenté dans les produits digitaux et la coordination d’équipes techniques et métiers.', 'https://linkedin.com/in/jean-diarra', 'https://github.com/jean-diarra', 'Roadmap, Jira, Communication, Agile'),
    ('grace.toure@jobfinder.ai', 'Grace', 'Toure', 'UX/UI Designer', 'Abidjan, Plateau', 'Designer UX/UI orientée expérience utilisateur, accessibilité et design systems.', 'https://linkedin.com/in/grace-toure', 'https://github.com/grace-toure', 'Figma, UX Research, Prototypage, Design Systems'),
    ('moussa.sangare@jobfinder.ai', 'Moussa', 'Sangaré', 'Ingénieur DevOps', 'Abidjan, Riviera', 'Ops orienté automatisation, CI/CD et stabilité des plateformes cloud.', 'https://linkedin.com/in/moussa-sangare', 'https://github.com/moussa-sangare', 'Linux, Docker, AWS, Kubernetes'),
    ('salimata.coulibaly@jobfinder.ai', 'Salimata', 'Coulibaly', 'Analyste Financier', 'Abidjan, Zone 4', 'Finance avec forte maîtrise de l’analyse de coûts, reporting et pilotage de performance.', 'https://linkedin.com/in/salimata-coulibaly', 'https://github.com/salimata-coulibaly', 'Excel, Reporting, Power BI, Finance'),
    ('olivier.aka@jobfinder.ai', 'Olivier', 'Aka', 'Développeur Fullstack React', 'Abidjan, Cocody', 'Développeur fullstack orienté productivité, qualité et collaboration agile.', 'https://linkedin.com/in/olivier-aka', 'https://github.com/olivier-aka', 'React, Node.js, TypeScript, MongoDB'),
    ('aicha.kone@jobfinder.ai', 'Aïcha', 'Kone', 'Community Manager', 'Abidjan, Marcory', 'Community manager avec expérience sur les réseaux sociaux, contenus et croissance digitale.', 'https://linkedin.com/in/aicha-kone', 'https://github.com/aicha-kone', 'Meta Ads, Content, Canva, Analytics'),
    ('lamine.kouassi@jobfinder.ai', 'Lamine', 'Kouassi', 'Consultant ERP', 'San Pedro', 'Consultant ERP avec expérience sur l’intégration de solutions métier et la conduite du changement.', 'https://linkedin.com/in/lamine-kouassi', 'https://github.com/lamine-kouassi', 'ERP, Process, Formation, Analyse'),
    ('aude.nguessan@jobfinder.ai', 'Aude', 'N’Guessan', 'Chef de Projet IT', 'Bouaké', 'PMO et chef de projet digital avec background en banque et télécom.', 'https://linkedin.com/in/aude-nguessan', 'https://github.com/aude-nguessan', 'Agile, MS Project, JIRA, Change Management'),
    ('dramane.ouattara@jobfinder.ai', 'Dramane', 'Ouattara', 'Ingénieur Génie Civil', 'Abidjan, Yopougon', 'Ingénieur civil ayant travaillé sur des projets de construction et de suivi de chantier.', 'https://linkedin.com/in/dramane-ouattara', 'https://github.com/dramane-ouattara', 'AutoCAD, Topographie, Gestion chantier'),
    ('mireille.brou@jobfinder.ai', 'Mireille', 'Brou', 'Responsable RH', 'Abidjan, Plateau', 'Responsable RH orientée recrutement, gestion des talents et amélioration des processus RH.', 'https://linkedin.com/in/mireille-brou', 'https://github.com/mireille-brou', 'Recrutement, RH, Talent, Sourcing'),
    ('kevin.fofana@jobfinder.ai', 'Kevin', 'Fofana', 'Cybersecurity Analyst', 'Abidjan, Cocody', 'Analyste cybersécurité avec une forte sensibilité à la gouvernance et à l’audit.', 'https://linkedin.com/in/kevin-fofana', 'https://github.com/kevin-fofana', 'Sécurité, SIEM, Audit, ISO 27001'),
    ('ruth.konan@jobfinder.ai', 'Ruth', 'Konan', 'Marketing Digital', 'Abidjan, Treichville', 'Marketing digital avec forte expérience sur le growth, les campagnes et l’analyse ROI.', 'https://linkedin.com/in/ruth-konan', 'https://github.com/ruth-konan', 'Google Ads, Meta Ads, Analytics, SEO'),
    ('seydou.yapi@jobfinder.ai', 'Seydou', 'Yapi', 'Data Engineer', 'Abidjan, Riviera', 'Ingénieur data orienté pipelines, modélisation et performance.', 'https://linkedin.com/in/seydou-yapi', 'https://github.com/seydou-yapi', 'Python, Spark, SQL, Airflow'),
]

candidates = []
for email, first, last, desired_title, location, summary, linkedin, github, skills_text in candidate_specs:
    user = create_user(email, first, last, 'jobseeker', 'Candidate123!')
    profile = create_profile(user, location, desired_title, summary, f'+225 07 55 66 77 {len(candidates)+1}', linkedin, github)
    for skill_name in skills_text.split(', '):
        category = 'technical'
        if skill_name in {'Communication', 'Agile', 'Roadmap', 'Jira'}:
            category = 'soft'
        elif skill_name in {'Python', 'Django', 'SQL', 'Docker', 'React', 'Node.js', 'TypeScript', 'MongoDB', 'Power BI', 'Excel', 'AWS', 'Kubernetes', 'Spark', 'Airflow'}:
            category = 'technical'
        else:
            category = 'tool'
        Skill.objects.get_or_create(profile=profile, name=skill_name, defaults={'category': category, 'level': 'avance'})
    Experience.objects.create(profile=profile, title='Consultant IT', company='Entreprise locale', location=location.split(',')[0], start_date=date(2021, 1, 1), end_date=None, is_current=True, description='Mission d’accompagnement sur la transformation digitale et l’exécution opérationnelle.', technologies='Python, SQL, Excel')
    Experience.objects.create(profile=profile, title='Collaborateur technique', company='Société de services', location='Abidjan', start_date=date(2018, 6, 1), end_date=date(2020, 12, 31), is_current=False, description='Participation à des projets de mise en place de solutions métiers et de support utilisateur.', technologies='Django, React, Power BI')
    Education.objects.create(profile=profile, degree='Master en Informatique' if 'Data' in desired_title or 'Backend' in desired_title or 'DevOps' in desired_title else 'Master en Gestion' if 'RH' in desired_title or 'Product' in desired_title else 'Licence Informatique', institution='Université Félix Houphouët-Boigny' if 'Abidjan' in location else 'INPHB', location='Abidjan', start_year=2014, end_year=2018, gpa='Très bien')
    profile.compute_completion()
    candidates.append(user)

# Additional candidates (20 more)
extra_candidate_specs = [
    ('abdoulaye.diarra@jobfinder.ai', 'Abdoulaye', 'Diarra', 'Data Engineer', 'Abidjan, Koumassi', 'Ingénieur data orienté pipelines et qualité de données.', 'https://linkedin.com/in/abdoulaye-diarra', 'https://github.com/abdoulaye-diarra', 'Python, Spark, SQL, Airflow'),
    ('clementine.ouedraogo@jobfinder.ai', 'Clementine', 'Ouedraogo', 'Product Designer', 'Abidjan, Adjamé', 'Designer produit passionnée par la simplicité et l’expérience utilisateur.', 'https://linkedin.com/in/clementine-ouedraogo', 'https://github.com/clementine-ouedraogo', 'Figma, UX Research, Prototypage'),
    ('michael.kouassi@jobfinder.ai', 'Michael', 'Kouassi', 'Administrateur Système', 'Yamoussoukro', 'Administrateur système orienté stabilité et automatisation.', 'https://linkedin.com/in/michael-kouassi', 'https://github.com/michael-kouassi', 'Linux, Bash, Ansible, Docker'),
    ('noemie.sorho@jobfinder.ai', 'Noemie', 'Sorho', 'Business Analyst', 'Abidjan, Marcory', 'Analyste métier avec une forte appétence pour l’innovation digitale.', 'https://linkedin.com/in/noemie-sorho', 'https://github.com/noemie-sorho', 'SQL, Excel, Analyse métier, Jira'),
    ('karim.toure@jobfinder.ai', 'Karim', 'Toure', 'Ingénieur IA', 'Abidjan, Riviera', 'Ingénieur IA porté sur l’industrialisation des modèles et l’optimisation.', 'https://linkedin.com/in/karim-toure', 'https://github.com/karim-toure', 'Python, PyTorch, MLOps, AWS'),
    ('lina.konan@jobfinder.ai', 'Lina', 'Konan', 'Responsable Support Client', 'Abidjan, Plateau', 'Spécialiste support client et amélioration de l’expérience utilisateur.', 'https://linkedin.com/in/lina-konan', 'https://github.com/lina-konan', 'Zendesk, Communication, CRM, Support'),
    ('sylvain.diallo@jobfinder.ai', 'Sylvain', 'Diallo', 'Chef de Projet Digital', 'Bouaké', 'Chef de projet digital avec expérience en transformation et pilotage d’équipes.', 'https://linkedin.com/in/sylvain-diallo', 'https://github.com/sylvain-diallo', 'Agile, Jira, Communication, PMO'),
    ('coumba.yapi@jobfinder.ai', 'Coumba', 'Yapi', 'Community Manager', 'Abidjan, Cocody', 'Community manager orientée contenu, engagement et croissance sociale.', 'https://linkedin.com/in/coumba-yapi', 'https://github.com/coumba-yapi', 'Meta Ads, Canva, Content, Analytics'),
    ('amine.kouassi@jobfinder.ai', 'Amine', 'Kouassi', 'Développeur Mobile', 'San Pedro', 'Développeur mobile passionné par l’expérience utilisateur mobile.', 'https://linkedin.com/in/amine-kouassi', 'https://github.com/amine-kouassi', 'Flutter, React Native, Firebase, API'),
    ('hugo.brou@jobfinder.ai', 'Hugo', 'Brou', 'Consultant ERP', 'Abidjan, Yopougon', 'Consultant ERP avec expertise sur l’intégration et l’adoption des solutions.', 'https://linkedin.com/in/hugo-brou', 'https://github.com/hugo-brou', 'ERP, Process, Formation, Analyse'),
    ('djeneba.toure@jobfinder.ai', 'Djeneba', 'Toure', 'Data Scientist', 'Abidjan, Treichville', 'Data scientist intéressant les modèles prédictifs et les enjeux business.', 'https://linkedin.com/in/djeneba-toure', 'https://github.com/djeneba-toure', 'Python, SQL, Scikit-learn, Statistics'),
    ('thierry.soro@jobfinder.ai', 'Thierry', 'Soro', 'Architecte Cloud', 'Abidjan, Koumassi', 'Architecte cloud orienté infrastructure robuste et automatisée.', 'https://linkedin.com/in/thierry-soro', 'https://github.com/thierry-soro', 'AWS, Azure, Terraform, Kubernetes'),
    ('mariam.kone@jobfinder.ai', 'Mariam', 'Kone', 'Marketing Digital', 'Abidjan, Riviera', 'Marketing digital avec forte expertise sur les campagnes social et web.', 'https://linkedin.com/in/mariam-kone', 'https://github.com/mariam-kone', 'Google Ads, SEO, Analytics, CRM'),
    ('fred.koffi@jobfinder.ai', 'Fred', 'Koffi', 'QA Engineer', 'Abidjan, Plateau', 'QA engineer attaché à la qualité logicielle et à l’automatisation des tests.', 'https://linkedin.com/in/fred-koffi', 'https://github.com/fred-koffi', 'Selenium, Python, Testing, CI/CD'),
    ('nourou.mensah@jobfinder.ai', 'Nourou', 'Mensah', 'Consultant RH', 'Bouaké', 'Consultant RH orienté recrutement et accompagnement des talents.', 'https://linkedin.com/in/nourou-mensah', 'https://github.com/nourou-mensah', 'Recrutement, Sourcing, RH, Entretiens'),
    ('mouhamed.yao@jobfinder.ai', 'Mouhamed', 'Yao', 'DevOps Engineer', 'Abidjan, Cocody', 'DevOps engineer spécialisé dans les pipelines CI/CD et l’orchestration.', 'https://linkedin.com/in/mouhamed-yao', 'https://github.com/mouhamed-yao', 'Docker, Kubernetes, GitHub Actions, Linux'),
    ('joelle.diallo@jobfinder.ai', 'Joelle', 'Diallo', 'UX Writer', 'Abidjan, Marcory', 'UX writer attachée à la clarté des messages et à l’accessibilité numérique.', 'https://linkedin.com/in/joelle-diallo', 'https://github.com/joelle-diallo', 'UX Writing, Figma, Content Strategy'),
    ('yvan.ahou@jobfinder.ai', 'Yvan', 'Ahou', 'Ingénieur Sécurité', 'Abidjan, Angre', 'Ingénieur sécurité concerné par la gouvernance et la protection des systèmes.', 'https://linkedin.com/in/yvan-ahou', 'https://github.com/yvan-ahou', 'Sécurité, SIEM, Audit, ISO 27001'),
    ('chloe.traore@jobfinder.ai', 'Chloe', 'Traore', 'Business Developer', 'Abidjan, Plateau', 'Business developer compétente sur le terrain commercial et l’identification d’opportunités.', 'https://linkedin.com/in/chloe-traore', 'https://github.com/chloe-traore', 'Sales, CRM, Prospection, Negotiation'),
]
for email, first, last, desired_title, location, summary, linkedin, github, skills_text in extra_candidate_specs:
    user = create_user(email, first, last, 'jobseeker', 'Candidate123!')
    profile = create_profile(user, location, desired_title, summary, f'+225 07 60 00 {len(candidates)+1}', linkedin, github)
    for skill_name in skills_text.split(', '):
        category = 'technical'
        if skill_name in {'Communication', 'Agile', 'Roadmap', 'Jira', 'Support', 'CRM', 'Prospection', 'Negotiation'}:
            category = 'soft'
        elif skill_name in {'Python', 'SQL', 'Docker', 'AWS', 'Kubernetes', 'Flutter', 'React Native', 'Firebase', 'Airflow', 'PyTorch', 'MLOps', 'Selenium', 'GitHub Actions', 'Terraform', 'Scikit-learn'}:
            category = 'technical'
        else:
            category = 'tool'
        Skill.objects.get_or_create(profile=profile, name=skill_name, defaults={'category': category, 'level': 'intermediaire'})
    Experience.objects.create(profile=profile, title='Responsable fonctionnel', company='Structure locale', location=location.split(',')[0], start_date=date(2020, 1, 1), end_date=None, is_current=True, description='Accompagnement des équipes sur des missions concrètes et des projets opérationnels.', technologies='Excel, Power BI')
    Education.objects.create(profile=profile, degree='Master en Informatique' if 'Data' in desired_title or 'IA' in desired_title or 'DevOps' in desired_title else 'Licence Management' if 'Business' in desired_title or 'Marketing' in desired_title else 'Licence Informatique', institution='Université Félix Houphouët-Boigny', location='Abidjan', start_year=2014, end_year=2018, gpa='Bien')
    profile.compute_completion()
    candidates.append(user)

# Jobs (20+)
job_specs = [
    ('Développeur Backend Python', 'Orange Côte d’Ivoire', 'Abidjan, Marcory', 'CI', True, 'cdi', 'it', 'Construire des APIs robustes et des services métier au cœur de l’expérience client.', 'Développer des endpoints, contribuer à la qualité logicielle et participer aux revues de code.', 'Python, Django, PostgreSQL, Docker', 'FastAPI, Redis, Celery', employers[1], 'Technologie'),
    ('Data Analyst', 'CinetTech', 'Abidjan, Plateau', 'CI', False, 'cdi', 'data', 'Analyser les données de trafic, de ventes et de performance pour piloter les décisions.', 'Créer des tableaux de bord et accompagner les équipes métier.', 'SQL, Power BI, Excel', 'Python, Tableau', employers[1], 'Technologie'),
    ('Product Manager', 'Jumia CI', 'Abidjan, Cocody', 'CI', True, 'cdi', 'rh', 'Piloter la roadmap produit de plusieurs expériences digitales avec des équipes transverses.', 'Prioriser des sujets, aligner les équipes et challenger les hypothèses produit.', 'Roadmap, Jira, Communication', 'Agile, UX research', employers[2], 'E-commerce'),
    ('UX/UI Designer', 'ManpowerGroup CI', 'Abidjan, Plateau', 'CI', True, 'cdd', 'design', 'Créer des interfaces simples, belles et accessibles pour des solutions B2B et B2C.', 'Concevoir des parcours, produire des maquettes et maintenir un design system.', 'Figma, UX Research, Prototyping', 'Design systems, Accessibility', employers[4], 'RH'),
    ('Ingénieur DevOps', 'DICOM', 'Abidjan, Riviera', 'CI', True, 'cdi', 'it', 'Assurer la stabilité, l’automatisation et la scalabilité des plateformes cloud.', 'Mettre en place des pipelines CI/CD et superviser les environnements de production.', 'Linux, Docker, AWS, Kubernetes', 'Terraform, GitHub Actions', employers[5], 'Fintech'),
    ('Analyste Financier', 'Groupe SETACI', 'Abidjan, Yopougon', 'CI', False, 'cdi', 'finance', 'Animer l’analyse de performance et le reporting financier d’un groupe en croissance.', 'Produire des reports, analyser les écarts et accompagner les décisions.', 'Excel, Power BI, Finance', 'SQL, Modélisation', employers[3], 'BTP'),
    ('Développeur Fullstack React', 'Orange Côte d’Ivoire', 'Abidjan, Marcory', 'CI', True, 'cdi', 'it', 'Construire des interfaces web modernes et des services associés.', 'Développer des composants React, intégrer des API et améliorer l’expérience utilisateur.', 'React, TypeScript, Node.js', 'MongoDB, Testing', employers[0], 'Télécom'),
    ('Community Manager', 'Jumia CI', 'Abidjan, Cocody', 'CI', True, 'cdi', 'marketing', 'Animer les communautés autour des marques et produire du contenu engageant.', 'Gérer les publications, les interactions et l’analyse de la performance social.', 'Meta Ads, Canva, Analytics', 'Community management, SEO', employers[2], 'E-commerce'),
    ('Consultant ERP', 'DICOM', 'Abidjan, Riviera', 'CI', False, 'cdi', 'finance', 'Accompagner la mise en œuvre de solutions ERP et l’adoption par les équipes.', 'Faire l’analyse des processus et accompagner le changement.', 'ERP, Process, Formation', 'Power BI, Excel', employers[5], 'Fintech'),
    ('Chef de Projet IT', 'Orange Côte d’Ivoire', 'Abidjan, Plateau', 'CI', False, 'cdi', 'it', 'Piloter des projets de transformation digitale avec des équipes techniques et métiers.', 'Coordonner les équipes, suivre les délais et gérer le changement.', 'Agile, MS Project, JIRA', 'PMP, Scrum', employers[0], 'Télécom'),
    ('Ingénieur Génie Civil', 'Groupe SETACI', 'Abidjan, Yopougon', 'CI', False, 'cdi', 'btp', 'Superviser des chantiers et garantir la qualité technique des travaux.', 'Coordonner les intervenants et traiter les problématiques de terrain.', 'AutoCAD, Topographie, Gestion chantier', 'QHSE, Planning', employers[3], 'BTP'),
    ('Responsable RH', 'ManpowerGroup CI', 'Abidjan, Plateau', 'CI', False, 'cdi', 'rh', 'Animer la politique RH et le recrutement de talents qualifiés.', 'Conduire le sourcing, les entretiens et le suivi RH.', 'Recrutement, Talent, Sourcing', 'ATS, LinkedIn', employers[4], 'RH'),
    ('Cybersecurity Analyst', 'CinetTech', 'Abidjan, Plateau', 'CI', True, 'cdi', 'it', 'Sécuriser les plateformes et accompagner la gouvernance sécurité.', 'Auditer les systèmes et mettre en place des pratiques de sécurité.', 'Sécurité, SIEM, Audit', 'ISO 27001, SOC', employers[1], 'Technologie'),
    ('Marketing Digital', 'Jumia CI', 'Abidjan, Cocody', 'CI', True, 'cdd', 'marketing', 'Optimiser les campagnes digitales et la conversion.', 'Pilotage des campagnes et analyse des performances.', 'Google Ads, Meta Ads, Analytics', 'SEO, CRM', employers[2], 'E-commerce'),
    ('Data Engineer', 'DICOM', 'Abidjan, Riviera', 'CI', True, 'cdi', 'data', 'Construire des pipelines robustes et des structures de données fiables.', 'Assembler les sources de données et améliorer l’industrialisation.', 'Python, Spark, SQL, Airflow', 'Kafka, dbt', employers[5], 'Fintech'),
    ('Développeur Mobile', 'CinetTech', 'Abidjan, Plateau', 'CI', True, 'cdi', 'it', 'Créer des expériences mobiles fluides et performantes.', 'Développer des fonctionnalités natives et améliorer l’accessibilité.', 'Flutter, React Native, API', 'Firebase, GraphQL', employers[1], 'Technologie'),
    ('Chargé de Recrutement', 'ManpowerGroup CI', 'Abidjan, Plateau', 'CI', False, 'cdd', 'rh', 'Gérer les missions de recrutement et orienter les candidats.', 'Sourcer, qualifier et accompagner les candidats.', 'LinkedIn Recruiter, Entretiens, ATS', 'Droit du travail', employers[4], 'RH'),
    ('Architecte Cloud', 'Orange Côte d’Ivoire', 'Abidjan, Marcory', 'CI', True, 'cdi', 'it', 'Concevoir l’architecture technique et les modèles d’infrastructure cloud.', 'Définir les standards techniques et piloter la modernisation.', 'AWS, Azure, Architecture', 'Terraform, Kubernetes', employers[0], 'Télécom'),
    ('Responsable Marketing Digital', 'Jumia CI', 'Abidjan, Cocody', 'CI', True, 'cdi', 'marketing', 'Piloter la stratégie digitale et le growth sur les marchés locaux.', 'Construire des campagnes, mesurer l’impact et faire évoluer le plan de communication.', 'Google Ads, Meta Ads, SEO', 'CRM, Analytics', employers[2], 'E-commerce'),
]

for idx, (title, company, location, country, is_remote, job_type, domain, description, missions, required_skills, nice_to_have, employer, industry) in enumerate(job_specs, start=1):
    Job.objects.get_or_create(
        title=title,
        company=company,
        defaults={
            'employer': employer,
            'location': location,
            'country': country,
            'is_remote': is_remote,
            'job_type': job_type,
            'domain': domain,
            'description': description,
            'missions': missions,
            'requirements': 'Expérience pertinente, autonomie et sens du service.',
            'required_skills': required_skills,
            'nice_to_have': nice_to_have,
            'salary_min': 300000 + idx * 16000,
            'salary_max': 700000 + idx * 14000,
            'salary_currency': 'XOF',
            'salary_display_text': 'Selon profil',
            'source_type': 'employer',
            'is_active': True,
            'posted_at': timezone.now() - timedelta(days=idx),
            'deadline': date.today() + timedelta(days=30 + idx),
            'company_about': 'Entreprise active en Côte d’Ivoire avec une vraie présence locale et une forte ambition de croissance.',
        },
    )

# Additional jobs (20 more)
extra_job_titles = [
    'Responsable Support N2', 'Lead Data Engineer', 'Consultant UX Research', 'Ingénieur QA Automation',
    'Analyste Business Intelligence', 'Product Owner', 'Développeur Java', 'Ingénieur Cloud AWS',
    'Spécialiste Acquisition', 'Coordinateur RH', 'Développeur Frontend Vue', 'Chef de Produit',
    'Gestionnaire de Projets IT', 'Expert Sécurité Cloud', 'Responsable Marketing Performance', 'Analyste Cybersécurité',
    'Administrateur Bases de Données', 'Consultant SAP', 'Responsable Relations Clients', 'Technicien Support Applicatif'
]
for idx, title in enumerate(extra_job_titles, start=1):
    employer = employers[(idx - 1) % len(employers)]
    employer_profile = EmployerProfile.objects.get(user=employer)
    Job.objects.get_or_create(
        title=title,
        company=employer_profile.company_name,
        defaults={
            'employer': employer,
            'location': employer_profile.location,
            'country': 'CI',
            'is_remote': idx % 2 == 0,
            'job_type': 'cdi' if idx % 3 != 0 else 'cdd',
            'domain': 'it' if idx % 2 == 0 else 'data',
            'description': 'Mission orientée résultats et collaboration avec des équipes techniques et métiers.',
            'missions': 'Piloter la livraison, améliorer les processus et contribuer à l’excellence opérationnelle.',
            'requirements': 'Expérience solide, autonomie et sens du service.',
            'required_skills': 'Python, SQL, Communication',
            'nice_to_have': 'Expérience sur un environnement international',
            'salary_min': 350000 + idx * 18000,
            'salary_max': 800000 + idx * 17000,
            'salary_currency': 'XOF',
            'salary_display_text': 'Selon profil',
            'source_type': 'employer',
            'is_active': True,
            'posted_at': timezone.now() - timedelta(days=idx),
            'deadline': date.today() + timedelta(days=35 + idx),
            'company_about': 'Entreprise locale en pleine évolution avec des besoins de recrutement constants.',
        },
    )

# Applications, notifications, saved jobs, alerts, interactions, messages
jobs = list(Job.objects.order_by('id'))
for idx, candidate in enumerate(candidates[:15], start=1):
    job = jobs[idx % len(jobs)]
    application, _ = Application.objects.get_or_create(
        user=candidate,
        job=job,
        defaults={
            'status': ['sent', 'viewed', 'pending', 'interview', 'offer'][idx % 5],
            'cover_message': 'Je souhaite contribuer à cette mission avec mon expérience, mon sens de l’exécution et mon envie d’apprendre.',
            'applied_at': timezone.now() - timedelta(days=idx),
        },
    )
    Notification.objects.get_or_create(
        user=candidate,
        title=f'Nouvelle mise à jour #{idx}',
        defaults={
            'notif_type': 'app_status',
            'message': 'Une mise à jour a été enregistrée sur votre candidature.',
            'link': '/applications/history/',
        },
    )
    SavedJob.objects.get_or_create(user=candidate, job=jobs[(idx + 2) % len(jobs)])
    SearchAlert.objects.get_or_create(
        user=candidate,
        label=f'Alerte {idx}',
        defaults={
            'keywords': 'python django data',
            'domain': 'it' if idx % 2 == 0 else 'data',
            'job_type': 'cdi',
            'country': 'CI',
            'min_score': 70 + idx,
        },
    )
    JobInteraction.objects.get_or_create(user=candidate, job=job, action='applied')
    Message.objects.get_or_create(application=application, sender=candidate, defaults={'content': f'Message de suivi de {candidate.get_full_name()} concernant la candidature.'})

# Additional applications to reach 20+
for idx, candidate in enumerate(candidates[15:], start=1):
    job = jobs[idx % len(jobs)]
    application, _ = Application.objects.get_or_create(
        user=candidate,
        job=job,
        defaults={
            'status': 'sent',
            'cover_message': 'Très motivé pour rejoindre cette équipe.',
            'applied_at': timezone.now() - timedelta(days=idx),
        },
    )
    if not Message.objects.filter(application=application).exists():
        Message.objects.create(application=application, sender=candidate, content='Bonjour, je souhaite discuter de cette opportunité.')

# Additional applications and activity for the new 20 candidates
for idx, candidate in enumerate(candidates[15:], start=1):
    job = jobs[(idx + 7) % len(jobs)]
    application, _ = Application.objects.get_or_create(
        user=candidate,
        job=job,
        defaults={
            'status': ['viewed', 'pending', 'interview', 'offer'][idx % 4],
            'cover_message': 'Je suis très motivé par cette opportunité et je souhaite apporter de la valeur rapidement.',
            'applied_at': timezone.now() - timedelta(days=idx + 5),
        },
    )
    Notification.objects.get_or_create(
        user=candidate,
        title=f'Nouvelle réponse #{idx + 20}',
        defaults={
            'notif_type': 'app_status',
            'message': 'L’entreprise a mis à jour le statut de votre candidature.',
            'link': '/applications/history/',
        },
    )
    SavedJob.objects.get_or_create(user=candidate, job=jobs[(idx + 3) % len(jobs)])
    SearchAlert.objects.get_or_create(
        user=candidate,
        label=f'Alerte enrichie {idx}',
        defaults={
            'keywords': 'data python react',
            'domain': 'it' if idx % 2 == 0 else 'data',
            'job_type': 'cdi',
            'country': 'CI',
            'min_score': 75 + idx,
        },
    )
    JobInteraction.objects.get_or_create(user=candidate, job=job, action='saved')
    Message.objects.get_or_create(application=application, sender=candidate, defaults={'content': f'Bonjour, je reste disponible pour un échange rapide autour de cette position.'})

print('Seed completed with realistic data')
print('Users:', UserModel.objects.count())
print('Profiles:', UserProfile.objects.count())
print('Skills:', Skill.objects.count())
print('Experiences:', Experience.objects.count())
print('Educations:', Education.objects.count())
print('Employers:', EmployerProfile.objects.count())
print('Jobs:', Job.objects.count())
print('Applications:', Application.objects.count())
print('Notifications:', Notification.objects.count())
print('SavedJobs:', SavedJob.objects.count())
print('SearchAlerts:', SearchAlert.objects.count())
print('JobInteractions:', JobInteraction.objects.count())
print('Messages:', Message.objects.count())
