from pathlib import Path

content = '''{% extends 'base.html' %}
{% block title %}JobFinder AI — Emplois en Côte d'Ivoire{% endblock %}

{% block content %}
<section style="background:linear-gradient(135deg,var(--cream-2),var(--white));border-bottom:1px solid var(--border);padding:clamp(44px,8vw,90px) 28px clamp(44px,8vw,80px)">
  <div class="container">
    <div class="hero-grid">
      <div>
        <div class="section-tag" style="margin-bottom:20px">
          <i data-lucide="map-pin" style="width:13px;height:13px"></i> Plateforme emploi N°1 en Côte d'Ivoire
        </div>
        <h1 class="display-1" style="margin-bottom:16px">
          Trouvez votre<br/>prochain emploi<br/><em style="color:var(--gold-dark)">en Côte d'Ivoire</em>
        </h1>
        <p class="body-lg" style="color:var(--text-2);margin-bottom:28px;max-width:520px;line-height:1.75">
          Des milliers d'offres vérifiées, un matching IA intelligent et des outils pour maximiser vos candidatures. 100% gratuit.
        </p>

        <form action="{% url 'jobs:list' %}" method="get" style="background:var(--white);border:2px solid var(--border-2);border-radius:16px;padding:6px;display:flex;gap:6px;max-width:560px;box-shadow:var(--shadow-md);margin-bottom:32px">
          <div style="flex:1;display:flex;align-items:center;gap:8px;padding:0 12px">
            <i data-lucide="search" style="width:18px;height:18px;color:var(--text-3);flex-shrink:0"></i>
            <input name="q" style="border:none;outline:none;font-size:16px;background:transparent;width:100%;color:var(--text)" placeholder="Titre, compétence, entreprise…"/>
          </div>
          <input type="hidden" name="country" value="CI"/>
          <button type="submit" class="btn btn-primary" style="white-space:nowrap">Rechercher</button>
        </form>

        <div style="display:flex;gap:24px;flex-wrap:wrap">
          <div>
            <div class="stat-number">{{ total_jobs }}</div>
            <div class="body-sm" style="color:var(--text-3)">Offres actives CI</div>
          </div>
          <div>
            <div class="stat-number">{{ total_companies }}</div>
            <div class="body-sm" style="color:var(--text-3)">Entreprises</div>
          </div>
          <div>
            <div class="stat-number">100%</div>
            <div class="body-sm" style="color:var(--text-3)">Gratuit</div>
          </div>
        </div>
      </div>

      <div class="card" style="padding:24px;position:relative">
        <div class="body-sm" style="font-weight:700;color:var(--text-3);margin-bottom:14px;text-transform:uppercase;letter-spacing:0.8px;display:flex;align-items:center;gap:6px">
          <i data-lucide="clock" style="width:13px;height:13px"></i> Offres récentes — 🇨🇮 CI
        </div>
        {% for job in recent|slice:":5" %}
        <a href="{% url 'jobs:detail' job.pk %}" style="display:flex;align-items:center;gap:12px;padding:12px 0;border-bottom:1px solid var(--border);text-decoration:none;transition:all 0.2s" onmouseover="this.style.paddingLeft='6px'" onmouseout="this.style.paddingLeft='0'">
          <div style="width:40px;height:40px;border-radius:10px;background:var(--gold-bg);border:1px solid var(--gold-border);display:flex;align-items:center;justify-content:center;flex-shrink:0">
            <i data-lucide="{{ job.domain_icon }}" style="width:18px;height:18px;color:var(--gold-dark)"></i>
          </div>
          <div style="flex:1;min-width:0">
            <div style="font-weight:600;font-size:14px;color:var(--text);overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{ job.title }}</div>
            <div style="font-size:13px;color:var(--text-3)">{{ job.company }} · {{ job.location }}</div>
          </div>
          <div style="font-size:12px;color:var(--text-3);flex-shrink:0">{{ job.days_ago }}</div>
        </a>
        {% empty %}
        <div style="text-align:center;color:var(--text-3);padding:24px">Aucune offre pour le moment.</div>
        {% endfor %}
        <a href="{% url 'jobs:list' %}?country=CI" style="display:block;text-align:center;margin-top:14px;font-size:14px;font-weight:700;color:var(--gold-dark);text-decoration:none">
          Voir toutes les offres CI <i data-lucide="arrow-right" style="width:14px;height:14px"></i>
        </a>
        <div style="position:absolute;top:-14px;right:16px;background:linear-gradient(135deg,var(--gold),var(--gold-dark));color:white;border-radius:10px;padding:8px 14px;font-size:12px;font-weight:700;box-shadow:0 4px 14px var(--gold-glow)">
          <i data-lucide="target" style="width:13px;height:13px"></i> Score IA de matching
        </div>
      </div>
    </div>
  </div>
</section>

{% if domains %}
<section style="padding:64px 28px;background:var(--cream-2);border-bottom:1px solid var(--border)">
  <div class="container">
    <div style="text-align:center;margin-bottom:36px">
      <h2 class="h1">Explorer par domaine</h2>
      <p class="body" style="color:var(--text-2);margin-top:8px">{{ domains|length }} domaine{{ domains|length|pluralize }} avec des offres actives en Côte d'Ivoire</p>
    </div>
    <div style="display:flex;flex-wrap:wrap;gap:12px;justify-content:center">
      {% for code, name in domains %}
      <a href="{% url 'jobs:list' %}?domain={{ code }}&country=CI"
        style="background:var(--white);border:1px solid var(--border);border-radius:14px;padding:16px 22px;text-align:center;text-decoration:none;transition:all 0.2s;display:flex;align-items:center;gap:10px;min-width:160px"
        onmouseover="this.style.borderColor='var(--gold)';this.style.background='#FEFDF8';this.style.transform='translateY(-2px)'"
        onmouseout="this.style.borderColor='var(--border)';this.style.background='white';this.style.transform='translateY(0)'">
        <i data-lucide="{% if code == 'it' %}monitor{% elif code == 'data' %}bar-chart-2{% elif code == 'finance' %}banknote{% elif code == 'marketing' %}megaphone{% elif code == 'design' %}palette{% elif code == 'rh' %}users{% elif code == 'sante' %}cross{% elif code == 'btp' %}hammer{% elif code == 'commerce' %}handshake{% elif code == 'juridique' %}scale{% elif code == 'education' %}book-open{% else %}briefcase{% endif %}" style="width:20px;height:20px;color:var(--gold-dark);flex-shrink:0"></i>
        <span style="font-size:14px;font-weight:600;color:var(--text)">{{ name }}</span>
      </a>
      {% endfor %}
    </div>
  </div>
</section>
{% endif %}

{% if featured %}
<section style="padding:64px 28px;background:var(--white);border-bottom:1px solid var(--border)">
  <div class="container">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:28px;flex-wrap:wrap;gap:14px">
      <div>
        <div class="section-tag"><i data-lucide="star" style="width:13px;height:13px"></i> Offres à la une — 🇨🇮 CI</div>
        <h2 class="h1" style="margin-top:8px">Opportunités sélectionnées</h2>
      </div>
      <a href="{% url 'jobs:list' %}?country=CI" class="btn btn-secondary">Toutes les offres <i data-lucide="arrow-right" style="width:15px;height:15px"></i></a>
    </div>
    <div class="grid-2">
      {% for job in featured %}
      <a href="{% url 'jobs:detail' job.pk %}" class="job-card" style="text-decoration:none">
        <div class="job-card-logo">
          {% if job.company_logo %}<img src="{{ job.company_logo.url }}" alt="{{ job.company }}"/>
          {% else %}<i data-lucide="{{ job.domain_icon }}" style="width:26px;height:26px;color:var(--gold-dark)"></i>{% endif %}
        </div>
        <div class="job-card-body">
          <div class="job-card-title">{{ job.title }}</div>
          <div class="job-card-company">{{ job.company }}</div>
          <div class="job-card-meta">
            <span class="badge badge-gray"><i data-lucide="map-pin" style="width:12px;height:12px"></i> {{ job.location }}</span>
            <span class="badge badge-gray">{{ job.get_job_type_display }}</span>
            {% if job.salary_min %}<span class="badge badge-gold">{{ job.salary_text }}</span>{% endif %}
            <span style="margin-left:auto;font-size:12px;color:var(--text-3)">{{ job.days_ago }}</span>
          </div>
        </div>
      </a>
      {% endfor %}
    </div>
  </div>
</section>
{% endif %}

<section style="padding:64px 28px;background:var(--cream-2);border-bottom:1px solid var(--border)">
  <div class="container">
    <div style="text-align:center;margin-bottom:44px">
      <div class="section-tag"><i data-lucide="sparkles" style="width:13px;height:13px"></i> Pourquoi nous choisir</div>
      <h2 class="h1" style="margin-top:8px">La plateforme la plus complète</h2>
    </div>
    <div class="grid-3">
      {% for icon, title, desc in features_why %}
      <div class="card card-p fade-up" style="transition-delay:{{ forloop.counter0 }}00ms">
        <div style="width:52px;height:52px;border-radius:14px;background:var(--gold-bg);border:1px solid var(--gold-border);display:flex;align-items:center;justify-content:center;margin-bottom:18px">
          <i data-lucide="{{ icon }}" style="width:24px;height:24px;color:var(--gold-dark)"></i>
        </div>
        <div class="h3" style="margin-bottom:10px">{{ title }}</div>
        <p class="body" style="color:var(--text-2)">{{ desc }}</p>
      </div>
      {% empty %}
      <div class="card card-p fade-up"><div style="width:52px;height:52px;border-radius:14px;background:var(--gold-bg);border:1px solid var(--gold-border);display:flex;align-items:center;justify-content:center;margin-bottom:18px"><i data-lucide="target" style="width:24px;height:24px;color:var(--gold-dark)"></i></div><div class="h3" style="margin-bottom:10px">Matching IA</div><p class="body" style="color:var(--text-2)">Notre algorithme NLP analyse votre profil et présente les offres les plus compatibles.</p></div>
      <div class="card card-p fade-up" style="transition-delay:100ms"><div style="width:52px;height:52px;border-radius:14px;background:var(--gold-bg);border:1px solid var(--gold-border);display:flex;align-items:center;justify-content:center;margin-bottom:18px"><i data-lucide="check-circle" style="width:24px;height:24px;color:var(--gold-dark)"></i></div><div class="h3" style="margin-bottom:10px">Offres vérifiées</div><p class="body" style="color:var(--text-2)">Chaque offre est contrôlée. Fini les annonces frauduleuses ou expirées.</p></div>
      <div class="card card-p fade-up" style="transition-delay:200ms"><div style="width:52px;height:52px;border-radius:14px;background:var(--gold-bg);border:1px solid var(--gold-border);display:flex;align-items:center;justify-content:center;margin-bottom:18px"><i data-lucide="sparkles" style="width:24px;height:24px;color:var(--gold-dark)"></i></div><div class="h3" style="margin-bottom:10px">Outils IA gratuits</div><p class="body" style="color:var(--text-2)">Analysez votre CV, préparez vos entretiens et générez des candidatures personnalisées.</p></div>
      {% endfor %}
    </div>
  </div>
</section>

<section style="padding:64px 28px;background:var(--white)">
  <div class="container">
    <div style="background:linear-gradient(135deg,#1A1408,#0F0C04);border-radius:24px;overflow:hidden">
      <div class="recruiter-grid">
        <div style="padding:56px 48px">
          <div style="font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:1.2px;color:var(--gold-2);margin-bottom:16px;display:flex;align-items:center;gap:6px">
            <i data-lucide="building-2" style="width:14px;height:14px"></i> Pour les recruteurs
          </div>
          <h2 style="font-family:'Playfair Display',serif;font-size:clamp(26px,3vw,36px);font-weight:700;color:white;margin-bottom:16px;line-height:1.2">
            Publiez vos offres,<br/>trouvez les meilleurs<br/>talents ivoiriens
          </h2>
          <p style="font-size:16px;color:rgba(255,255,255,0.6);line-height:1.75;margin-bottom:32px">
            Accédez à des milliers de candidats qualifiés. Publiez en 5 minutes, gérez vos candidatures depuis un tableau de bord dédié. Workflow complet : candidature → entretien → offre, avec notifications automatiques.
          </p>
          <div style="display:flex;gap:14px;flex-wrap:wrap">
            <a href="{% url 'accounts:auth' %}?tab=signup" class="btn btn-primary btn-lg">Recruter maintenant</a>
            <a href="{% url 'employers:post_job' %}" class="btn" style="background:rgba(255,255,255,0.1);color:white;border:1.5px solid rgba(255,255,255,0.2);padding:16px 32px;font-size:16px;border-radius:18px">Publier une offre</a>
          </div>
        </div>
        <div style="padding:56px 48px;display:grid;grid-template-columns:1fr 1fr;gap:16px;align-content:center">
          <div style="background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.1);border-radius:16px;padding:22px">
            <div style="font-family:'Playfair Display',serif;font-size:32px;font-weight:700;color:var(--gold-2)">100%</div>
            <div style="font-size:14px;color:rgba(255,255,255,0.5);margin-top:4px">Gratuit pour recruter</div>
          </div>
          <div style="background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.1);border-radius:16px;padding:22px">
            <div style="font-family:'Playfair Display',serif;font-size:32px;font-weight:700;color:var(--gold-2)">5 min</div>
            <div style="font-size:14px;color:rgba(255,255,255,0.5);margin-top:4px">Pour publier une offre</div>
          </div>
          <div style="background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.1);border-radius:16px;padding:22px">
            <div style="font-family:'Playfair Display',serif;font-size:32px;font-weight:700;color:var(--gold-2)">IA</div>
            <div style="font-size:14px;color:rgba(255,255,255,0.5);margin-top:4px">Matching candidats auto</div>
          </div>
          <div style="background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.1);border-radius:16px;padding:22px">
            <div style="font-family:'Playfair Display',serif;font-size:32px;font-weight:700;color:var(--gold-2)">24/7</div>
            <div style="font-size:14px;color:rgba(255,255,255,0.5);margin-top:4px">Visibilité continue</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>

{% endblock %}

{% block extra_js %}
<script>
document.addEventListener('DOMContentLoaded', function() {
  if (window.lucide) lucide.createIcons();
  var obs = new IntersectionObserver(function(es) { es.forEach(function(e) { if(e.isIntersecting) e.target.classList.add('visible'); }); }, {threshold:0.1});
  document.querySelectorAll('.fade-up').forEach(function(el) { obs.observe(el); });
});
</script>
{% endblock %}
'''

path = Path('jobfinder2/templates/core/home.html')
path.write_text(content, encoding='utf-8')
print(path)
