"""Compatibilité historique pour les imports anciens.

Le moteur de scoring unique et officiel est jobs.matching.
"""

from jobs.matching import compute_match_score

__all__ = ['compute_match_score']


def get_profile_strength(user) -> Dict:
    """
    Analyse la force du profil candidat pour le matching.
    Retourne des recommandations précises.
    """
    tips = []
    strong_points = []
    score = 0

    try:
        profile = user.profile
        skills_count = profile.skills.count()
        exp_count = profile.experiences.count()
        edu_count = profile.educations.count()

        # Titre souhaité
        if profile.desired_title:
            score += 15
            strong_points.append('Titre de poste défini')
        else:
            tips.append({'priority': 'high', 'field': 'Titre souhaité',
                        'action': 'Ajoutez un titre souhaité précis (ex: "Data Analyst Senior") — c\'est le premier critère de matching'})

        # Compétences
        if skills_count >= 8:
            score += 25
            strong_points.append('%d compétences renseignées' % skills_count)
        elif skills_count >= 4:
            score += 15
            tips.append({'priority': 'high', 'field': 'Compétences',
                        'action': 'Ajoutez %d compétences supplémentaires pour améliorer votre matching' % (8 - skills_count)})
        else:
            tips.append({'priority': 'critical', 'field': 'Compétences',
                        'action': 'Vous avez seulement %d compétence(s). Ajoutez-en au moins 6 pour un matching efficace' % skills_count})

        # Résumé
        if profile.summary and len(profile.summary) > 100:
            score += 20
            strong_points.append('Résumé professionnel complet')
        elif profile.summary:
            score += 10
            tips.append({'priority': 'medium', 'field': 'Résumé professionnel',
                        'action': 'Étoffez votre résumé (minimum 150 mots) avec vos spécialités et vos réalisations clés'})
        else:
            tips.append({'priority': 'high', 'field': 'Résumé professionnel',
                        'action': 'Ajoutez un résumé professionnel — l\'IA l\'utilise pour calculer votre compatibilité'})

        # Expériences
        if exp_count >= 2:
            score += 20
            strong_points.append('%d expérience(s) avec technologies' % exp_count)
        elif exp_count == 1:
            score += 10
            tips.append({'priority': 'medium', 'field': 'Expériences',
                        'action': 'Ajoutez les technologies utilisées dans votre expérience — elles boostent le matching'})
        else:
            tips.append({'priority': 'high', 'field': 'Expériences',
                        'action': 'Ajoutez vos expériences professionnelles même courtes (stages, freelance, projets perso)'})

        # Formation
        if edu_count >= 1:
            score += 10
            strong_points.append('Formation renseignée')
        else:
            tips.append({'priority': 'low', 'field': 'Formation',
                        'action': 'Ajoutez votre formation — certains recruteurs filtrent par niveau d\'études'})

        # CV uploadé
        if profile.cv_file:
            score += 10
            strong_points.append('CV uploadé')
        else:
            tips.append({'priority': 'medium', 'field': 'CV',
                        'action': 'Uploadez votre CV — il sera analysé par l\'IA pour les candidatures'})

    except Exception as e:
        logger.warning("get_profile_strength error: %s", e)

    return {
        'score': min(score, 100),
        'tips': sorted(tips, key=lambda x: {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}[x['priority']]),
        'strong_points': strong_points,
    }
