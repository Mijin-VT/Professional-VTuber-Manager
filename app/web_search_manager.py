"""Web Search Manager for VT Manager.
Queries DuckDuckGo for VTuber success stories and growth strategies, with a local fallback cache for popular VTubers.
"""
import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("VTManager.Search")

FAMOUS_VTUBERS_CASE_STUDIES = {
    "ironmouse": {
        "name": "Ironmouse",
        "highlights": [
            "Colaboraciones cruzadas masivas: Rompió la barrera del VTubing colaborando constantemente con streamers de cámara real (OTK, CDawgVA, Ludwig).",
            "Conexión emocional y vulnerabilidad: Compartir abiertamente su historia de salud (CVID) creó una comunidad leal y protectora (la 'Mouse Family').",
            "Eventos benéficos de largo formato: Su subathon récord recaudó millones y la posicionó en el top global de Twitch.",
            "Talento musical y versatilidad: Transiciones constantes entre ópera, canto y debates de cultura pop."
        ],
        "strategy_adaptation": "Adapta su enfoque colaborando fuera del nicho VTuber convencional y diversificando tu contenido con música o eventos de caridad."
    },
    "pekora": {
        "name": "Usada Pekora",
        "highlights": [
            "Programación estructurada: Diseña transmisiones con dinámicas similares a un show de televisión (juegos competitivos, castigos humorísticos).",
            "Mascota de marca ('peko'): Su muletilla vocal e identidad visual son fácilmente reconocibles y memeables.",
            "Liderazgo en servidores grupales: Crea narrativas y eventos dentro de servidores comunitarios (Minecraft Hololive) actuando como antagonista cómica.",
            "Reacciones exageradas y humor slapstick: Su audiencia adora verla fallar debido a su actitud presumida que termina en comedia."
        ],
        "strategy_adaptation": "Adapta su enfoque estructurando tus streams con objetivos claros, creando una muletilla o chiste interno y organizando eventos comunitarios multijugador."
    },
    "gura": {
        "name": "Gawr Gura",
        "highlights": [
            "Marketing viral y memes cortos: Su debut con el meme 'a' se viralizó en segundos en TikTok, Shorts y Twitter.",
            "Voz melódica y karaoke: Su talento natural para el canto atrajo a una audiencia masiva que no consume anime.",
            "Química de grupo (Hololive EN): Interacciones fluidas que potenciaron su crecimiento mutuo.",
            "Estética accesible y tierna (Kawaii): Diseño de personaje extremadamente limpio y magnético para audiencias occidentales."
        ],
        "strategy_adaptation": "Adapta su enfoque enfocándote en clips ultra-cortos para TikTok/Shorts y organizando transmisiones de karaoke o canto si tienes talento musical."
    },
    "shylily": {
        "name": "Shylily",
        "highlights": [
            "Diseño de audio premium: Su tono de voz y ecualización de micrófono crean una atmósfera íntima y relajante, similar al ASMR.",
            "Live2D ultra-expresivo: Invirtió en un rigging facial avanzado que transmite micro-expresiones de forma excepcional.",
            "Humor pícaro y doble sentido: Construyó una identidad basada en banter divertido y provocativo con su chat.",
            "Distribución activa en plataformas externas: Clips altamente editados distribuidos de forma constante en YouTube y TikTok por editores de su comunidad."
        ],
        "strategy_adaptation": "Adapta su enfoque mejorando tu calidad de audio (compresor/ecualizador) y promoviendo que tu chat cree clips cortos para redes externas."
    },
    "kuzuha": {
        "name": "Kuzuha",
        "highlights": [
            "Habilidad en juegos competitivos: Atrae a la audiencia mediante gameplays de alto nivel en Apex Legends y Valorant.",
            "Organización de torneos masivos: Fundador y líder en eventos de Nijisanji (como Nijisanji Koshien) que atraen cientos de miles de espectadores.",
            "Carisma casual y estilo de conversación relajado: Conexión genuina que atrae fuertemente tanto a hombres como a mujeres.",
            "Música y streams grupales: Lanzamientos de covers musicales y streams de juegos de mesa virtuales con su grupo."
        ],
        "strategy_adaptation": "Adapta su enfoque participando u organizando mini-torneos competitivos de juegos populares y manteniendo un tono de conversación sincero."
    },
    "filian": {
        "name": "Filian",
        "highlights": [
            "Comedia física extrema en VR Chat: Saltos, volteretas y caídas físicas reales en su habitación adaptadas al tracking del modelo virtual.",
            "Formato de shows interactivos: Conduce programas de concurso con otros creadores ('V-Tubers Got Talent', etc.).",
            "Auto-derisión y humor tonto: No tiene miedo de hacer el ridículo para entretener a su audiencia.",
            "Estrategia agresiva de Shorts: Su contenido hiperactivo está perfectamente optimizado para el algoritmo de formato corto."
        ],
        "strategy_adaptation": "Adapta su enfoque introduciendo elementos de comedia interactiva/física en tu stream y optimizando tus directos para convertirlos en Shorts de humor rápido."
    }
}

class WebSearchManager:
    """Manages searching for VTuber growth case studies and adapting them to the user's needs."""

    def __init__(self, config):
        self.config = config

    def search_vtuber_growth(self, user_message: str) -> Optional[str]:
        """Scans the user message for a VTuber name, searches DuckDuckGo, and returns a compiled summary."""
        # 1. Extract subject / name of the VTuber
        subject = self._extract_vtuber_name(user_message)
        if not subject:
            return None

        logger.info(f"Detected VTuber analysis request for: {subject}")
        
        # 2. Query DuckDuckGo text search
        snippets = []
        try:
            from duckduckgo_search import DDGS
            query = f"{subject} vtuber growth strategy success tips"
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=3))
                for r in results:
                    snippets.append(f"- {r.get('title')}: {r.get('body')}")
        except Exception as e:
            logger.warning(f"Web search for '{subject}' failed: {e}. Utilizing fallback local case studies.")

        # 3. Check if we have a high-quality local fallback for this specific VTuber
        fallback_data = self._get_local_case_study(subject)
        
        # 4. Compile the context injection for Astra
        context = f"\n\n[INFORMACIÓN DE BÚSQUEDA EN INTERNET: CASO DE ÉXITO DE {subject.upper()}]\n"
        if snippets:
            context += "Resultados reales encontrados en la web:\n" + "\n".join(snippets) + "\n\n"
        
        if fallback_data:
            context += (
                f"Puntos clave de éxito documentados para {fallback_data['name']}:\n"
                + "\n".join([f"• {h}" for h in fallback_data["highlights"]])
                + f"\n\nAdaptación estratégica recomendada para el usuario:\n{fallback_data['strategy_adaptation']}\n"
            )
        elif not snippets:
            # General fallback if search failed and not a famous VTuber
            context += (
                f"No pudimos acceder a resultados recientes en vivo para '{subject}' debido a limitaciones de red, "
                f"pero como manager sugiero que analicemos su caso buscando:\n"
                f"- Cuál es su gancho principal (comedia física, talento artístico, o gaming competitivo).\n"
                f"- De qué manera interactúa con su chat y si usa recompensas personalizadas.\n"
                f"- Cómo edita y distribuye sus clips en redes verticales como TikTok y YouTube Shorts."
            )

        context += (
            "\n[Instrucción para Astra Valeria]: Usa esta información para responder al usuario. "
            "Explícale qué hizo bien esta VTuber para crecer y dale consejos prácticos de cómo "
            "puede aplicar estas mismas técnicas en su propio canal de forma realista según su nicho."
        )
        return context

    def _extract_vtuber_name(self, text: str) -> Optional[str]:
        """Extracts a VTuber name from the message using pattern matching and catalogs."""
        t = text.lower()
        
        # Check famous names directly first
        for name in FAMOUS_VTUBERS_CASE_STUDIES.keys():
            if name in t:
                return FAMOUS_VTUBERS_CASE_STUDIES[name]["name"]

        # Regex to capture subject after keywords
        patterns = [
            r'(?:investiga sobre|busca sobre|quien es|como crecio|historia de|analiza a|estrategia de)\s+([a-zA-Z0-9_\s]{3,30})',
            r'(?:sobre|de)\s+([a-zA-Z0-9_\s]{3,20})\s+(?:para crecer|como vtuber|en twitch|en kick)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, t)
            if match:
                subject = match.group(1).strip()
                # Split at common transition words
                for stop in [" y ", " como ", " para ", " en ", " o ", " que "]:
                    if stop in f" {subject} ":
                        # Re-add space to subject to split exactly at boundaries
                        subject = f" {subject} ".split(stop)[0].strip()
                # Remove common small words
                subject_clean = re.sub(r'\b(la|el|los|un|una|de|sobre)\b', '', subject).strip()
                if len(subject_clean) >= 3:
                    return subject_clean.title()
                    
        return None

    def _get_local_case_study(self, subject: str) -> Optional[Dict[str, Any]]:
        """Retrieve local fallback data for famous VTubers."""
        s = subject.lower().strip()
        for name, data in FAMOUS_VTUBERS_CASE_STUDIES.items():
            if name in s or s in name:
                return data
        return None
