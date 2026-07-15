"""
Client IA — JobFinder AI (Côte d'Ivoire)
API Groq gratuite : https://console.groq.com

Modèle rapide : llama-3.1-8b-instant      → chat, emails, réponses courtes
Modèle smart  : llama-3.3-70b-versatile   → analyses profondes, JSON, scoring
"""
import time
import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)
GROQ_URL = 'https://api.groq.com/openai/v1/chat/completions'

# Ordre de fallback : si un modèle est indisponible, on essaie le suivant
_FALLBACK_CHAIN = [
    'llama-3.3-70b-versatile',
    'llama-3.1-70b-versatile',
    'llama3-70b-8192',
    'llama-3.1-8b-instant',
    'llama3-8b-8192',
]


def _call_groq(api_key: str, model: str, system_prompt: str,
               user_message: str, max_tokens: int, temperature: float):
    """Appel HTTP brut à Groq — lève une exception en cas d'erreur."""
    r = requests.post(
        GROQ_URL,
        headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
        json={
            'model': model,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user',   'content': user_message},
            ],
            'max_tokens':  max_tokens,
            'temperature': temperature,
        },
        timeout=50,
    )
    r.raise_for_status()
    return r.json()['choices'][0]['message']['content']


def ask_groq(
    system_prompt: str,
    user_message: str,
    model: str = None,
    max_tokens: int = 1000,
    temperature: float = 0.35,
    use_smart_model: bool = False,
) -> str:
    """
    Appelle l'API Groq avec retry automatique + fallback de modèle.
    - 503 / 529 (surcharge) → 1 retry après 2s sur le même modèle
    - Si toujours en échec → fallback sur le modèle suivant dans la chaîne
    use_smart_model=True  → commence par 70b
    use_smart_model=False → commence par 8b
    """
    api_key = settings.GROQ_API_KEY
    if not api_key:
        return _no_key_message()

    # Modèle de départ
    if model is None:
        model = (
            getattr(settings, 'GROQ_MODEL_SMART', 'llama-3.3-70b-versatile')
            if use_smart_model
            else getattr(settings, 'GROQ_MODEL', 'llama-3.1-8b-instant')
        )

    # Construire la liste de tentatives : modèle demandé en premier, puis fallbacks
    candidates = [model]
    for m in _FALLBACK_CHAIN:
        if m != model and m not in candidates:
            candidates.append(m)

    last_error = None
    for attempt_model in candidates:
        for retry in range(2):  # 2 essais par modèle
            try:
                result = _call_groq(api_key, attempt_model, system_prompt,
                                    user_message, max_tokens, temperature)
                if attempt_model != model:
                    logger.warning('Groq fallback utilisé : %s → %s', model, attempt_model)
                return result

            except requests.exceptions.Timeout:
                logger.warning('Groq timeout (model=%s, retry=%d)', attempt_model, retry)
                last_error = 'timeout'
                if retry == 0:
                    time.sleep(1)

            except requests.exceptions.HTTPError as e:
                code = e.response.status_code if e.response is not None else 0
                if code == 401:
                    return "Clé API Groq invalide. Vérifiez GROQ_API_KEY dans votre fichier .env"
                if code == 429:
                    logger.warning('Groq rate limit (model=%s)', attempt_model)
                    if retry == 0:
                        time.sleep(3)
                    last_error = '429'
                    continue
                if code in (503, 529, 500, 502):
                    # Serveur surchargé — retry puis fallback
                    logger.warning('Groq %d (model=%s, retry=%d)', code, attempt_model, retry)
                    last_error = str(code)
                    if retry == 0:
                        time.sleep(2)
                    continue
                logger.error('Groq HTTP %s (model=%s)', code, attempt_model)
                last_error = str(code)
                break  # Erreur non récupérable sur ce modèle

            except Exception as e:
                logger.error('Groq error (model=%s): %s', attempt_model, e)
                last_error = str(e)
                break

    # Tous les modèles ont échoué
    logger.error('Groq : tous les modèles ont échoué. Dernière erreur : %s', last_error)
    if last_error in ('503', '529', '502'):
        return "Le service IA est temporairement surchargé. Réessayez dans quelques secondes."
    if last_error == '429':
        return "Limite de requêtes atteinte. Attendez quelques secondes et réessayez."
    if last_error == 'timeout':
        return "L'IA met trop de temps à répondre. Réessayez dans un instant."
    return "Erreur de connexion à l'IA. Vérifiez votre connexion et réessayez."


def ask_groq_chat(messages: list, model: str = None, max_tokens: int = 500) -> str:
    """Mode multi-tours pour le chat assistant."""
    api_key = settings.GROQ_API_KEY
    if not api_key:
        return _no_key_message()

    model = model or getattr(settings, 'GROQ_MODEL', 'llama-3.1-8b-instant')
    try:
        r = requests.post(
            GROQ_URL,
            headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
            json={'model': model, 'messages': messages, 'max_tokens': max_tokens, 'temperature': 0.6},
            timeout=30,
        )
        r.raise_for_status()
        return r.json()['choices'][0]['message']['content']
    except Exception as e:
        logger.error('Groq chat: %s', e)
        return "Erreur de connexion à l'IA."


def _no_key_message() -> str:
    return (
        "Clé API Groq non configurée.\n\n"
        "Pour activer l'IA gratuitement :\n"
        "1. Créez un compte sur https://console.groq.com (100% gratuit)\n"
        "2. Générez une clé API\n"
        "3. Ajoutez  GROQ_API_KEY=gsk_...  dans votre fichier .env\n"
        "4. Redémarrez le serveur"
    )