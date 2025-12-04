import json
import re
import pdfplumber
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify
from flask_cors import CORS
import os

from datetime import datetime
import dateutil.parser
import spacy
import requests

############################################################
# GLOBAL CONFIG
############################################################

SEM_SIM_THRESHOLD = 0.82
nlp = spacy.load("en_core_web_lg")

MODEL = "llama-3.3-70b-versatile"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
MAX_TOKENS = 1800


############################################################
#groq CALL
############################################################

def groq_call(prompt):
    try:
        response = requests.post(
            GROQ_API_URL,
            headers={
                "Authorization": f"Bearer {os.environ.get('GROQ_API_KEY')}",
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.6,
                "max_tokens": MAX_TOKENS
            },
            timeout=60
        )
        data = response.json()

        if "choices" in data:
            return data["choices"][0]["message"]["content"].strip()
        if "error" in data:
            msg = data["error"].get("message", "Ukjent Groq-feil")
            return f"[Groq ERROR] {msg}"

        return f"[Groq ERROR] Uventet respons: {data}"

    except Exception as e:
        return f"[Groq ERROR] {str(e)}"




############################################################
# groq REWRITE
############################################################

def refine_with_groq(text, style="experienced"):
    prompt = f"""
    Forbedre teksten til et profesjonelt, tydelig og muntlig intervjusvar på norsk.
    Bruk en {style}-tone.
    - ingen punktlister
    - ingen nye teknologier
    - ingen engelsk
    - behold fakta, forbedre flyt og selvtillit

    Tekst:
    {text}
    """

    try:
        resp = requests.post(
            GROQ_API_URL,
            headers={
                "Authorization": f"Bearer {os.environ.get('GROQ_API_KEY')}",
                "Content-Type": "application/json"
            },
            json={
                "model": MODEL,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.6,
                "max_tokens": MAX_TOKENS
            },
            timeout=60
        )

        return resp.json()["choices"][0]["message"]["content"].strip()

    except Exception:
        return text


############################################################
# PROSJEKT SOM MATCHER SKILL
############################################################

def pick_project_for_skill(skill, projects):
    s = skill.lower()

    #Direkte substring match
    for p in projects:
        if s in p.lower():
            return p

    #Smarte Java-relaterte matches
    java_tags = ["spring boot", "spring", "jpa", "maven", "gradle"]
    python_tags = ["python", "flask"]
    sql_tags = ["postgres", "postgresql", "sql", "database"]
    cloud_tags = ["aws", "azure", "gcp", "cloud"]
    devops_tags = ["docker", "kubernetes", "k8s", "ci/cd", "terraform"]

    #Match roller via tags
    tag_map = {
        "java": java_tags,
        "python": python_tags,
        "sql": sql_tags,
        "aws": cloud_tags,
        "azure": cloud_tags,
        "gcp": cloud_tags,
        "cloud": cloud_tags,
        "k8s": devops_tags,
        "kubernetes": devops_tags,
        "ci/cd": devops_tags,
        "terraform": devops_tags,
        "go": ["api", "microservice"],
        "kotlin": java_tags,
    }

    tags = tag_map.get(s, [])

    for p in projects:
        text = p.lower()
        if any(tag in text for tag in tags):
            return p

    #Semantic fallback
    try:
        doc_s = nlp(s)
        best = None
        best_score = 0
        for p in projects:
            score = doc_s.similarity(nlp(p))
            if score > best_score:
                best_score = score
                best = p
        if best:
            return best
    except:
        pass

    # 4. fallback: første prosjekt
    return projects[0] if projects else ""

############################################################
# PROJECT STORY ENGINE (MATCHED SKILLS)
############################################################

def combine_and_refine_projects(skill, projects, level, used_projects):
    project = pick_project_for_skill(skill, projects)

    prompt = f"""
    Du er en norsk intervjumentor.
    Lag et konkret intervjusvar på 7–10 setninger.
    Svar som om jeg sier dette muntlig.

    KRAV:
    - Start svaret på forskjellige måter — ikke alltid "I et prosjekt". Variér åpningen med setninger som "En situasjon hvor jeg brukte dette var …", "Et konkret tilfelle er …" eller "Et godt eksempel er …".
    - Velg én tydelig situasjon fra prosjektet.
    - Beskriv hva jeg gjorde i praksis.
    - Forklar hvorfor det var viktig.
    - Forklar resultat/effekt.
    - Ingen engelsk.
    - Ingen punktlister.
    - Ingen fiktive teknologier.
    - Ingen repetisjon.

    Skill: {skill}

    Prosjektbeskrivelse (kun fakta, ikke kopier tekst):
    {project}
    """

    return groq_call(prompt)


############################################################
# STORY FALLBACK
############################################################

def craft_story_answer(skill, bullet):
    if bullet:
        return (
            f"Jeg har brukt {skill} aktivt i et tidligere prosjekt. "
            f"Ett konkret eksempel er: {bullet}. "
            f"Jeg tok ansvar for å drive oppgaven fremover, håndtere praktiske utfordringer "
            f"og sikre at løsningen ble levert stabilt og ryddig. "
            f"Dette ga meg solid erfaring med {skill} i reelle situasjoner."
        )

    return (
        f"Jeg har erfaring med {skill} fra flere oppgaver og prosjekter. "
        f"Jeg bruker teknologien naturlig i arbeidshverdagen og er trygg på å levere kvalitet "
        f"når {skill} er en del av stakken."
    )


############################################################
# CLEANERS
############################################################

def strip_contact_info(text):
    if not text:
        return ""
    t = re.sub(r"\+?\d[\d\s\-]{6,}", "", text)
    t = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "", t)
    return t

def clean_cv_text(raw):
    if not raw:
        return ""
    t = strip_contact_info(raw)
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"Side \d+ av \d+", "", t)

    noisy = [
        "FØDSELSDATO","Adresse","Address","Språk","Languages",
        "Kontakt","Contact","Profil","Profile","Referanser"
    ]

    for sec in noisy:
        t = re.sub(sec + r".*?(?=[A-ZÆØÅ])", " ", t, flags=re.DOTALL)

    return t.strip()

############################################################
# BULLETS
############################################################

def extract_bullets(text):
    bullets = []
    for line in text.split("\n"):
        l = line.strip()
        if re.match(r"^[-•*·→►▪■–]\s+", l):
            bullets.append(l)
        elif re.match(r"^[A-ZÆØÅ].{0,10}:\s", l):
            bullets.append(l)
        elif 10 < len(l) < 200 and l[0].islower():
            bullets.append(l)

    cleaned = []
    for b in bullets:
        b = re.sub(r"^[^A-Za-z0-9]+", "", b)
        b = b.strip()
        if 10 < len(b) < 250:
            cleaned.append(b)

    return list(dict.fromkeys(cleaned))

def find_relevant_bullet(bullets, skill):
    s = skill.lower()
    for b in bullets:
        words = re.findall(r"\b[a-zA-Z0-9+.#]+\b", b.lower())
        if s in words:
            return b
        if s in ("c","go") and any(w == s for w in words):
            return b
    return None

############################################################
# SPACY SKILL EXTRACTOR
############################################################

TECH_SKILLS = [
    # programming
    "java","kotlin","go","python","c#",".net","javascript","typescript",
    "sql","scala","rust","c++","c","php","ruby",

    # java ecosystem
    "spring","spring boot","spring framework","hibernate","jpa",
    "maven","gradle",

    # api
    "rest","rest api","restful api","graphql","soap",
    "microservices","microservice","event driven","kafka","rabbitmq",

    # cloud
    "azure","microsoft azure","aws","amazon web services",
    "gcp","google cloud","cloud",

    # devops
    "docker","kubernetes","k8s","helm","terraform","ci/cd","github actions",
    "gitlab ci","jenkins","azure devops","ansible",

    # db
    "postgres","postgresql","mysql","mariadb","oracle","mongodb",
    "redis","elasticsearch",

    # frontend
    "react","reactjs","react.js","angular","vue","html","css","tailwind",

    # test
    "junit","jest","cypress","playwright","selenium",

    # data
    "pandas","spark","databricks","power bi",

    # norwegian variants
    "mikrotjenester","integrasjoner","rest-tjenester"
]

from spacy.matcher import PhraseMatcher

matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
matcher.add("SKILLS", [nlp.make_doc(s) for s in TECH_SKILLS])

def extract_skills_from_text(text):
    if not text.strip():
        return []
    doc = nlp(text.lower())
    result = set()
    for _, start, end in matcher(doc):
        result.add(doc[start:end].text)
    return list(result)

############################################################
# CANONICAL SKILLS
############################################################

CANONICAL = {
    "rest":"rest api",
    "rest api":"rest api",
    "restful api":"rest api",
    "api":"rest api",

    "spring":"spring boot",
    "spring framework":"spring boot",

    "microsoft azure":"azure",
    "amazon web services":"aws",

    "postgresql":"postgres",
}

def normalise_skill(s):
    s = s.lower().strip()
    return CANONICAL.get(s, s)

############################################################
# SEMANTIC SIMILARITY
############################################################

def semantic_match(a, b):
    doc_a, doc_b = nlp(a), nlp(b)
    if not doc_a.vector_norm or not doc_b.vector_norm:
        return False
    return doc_a.similarity(doc_b) >= SEM_SIM_THRESHOLD


############################################################
# EXPERIENCE EXTRACTION
############################################################

def normalize_broken_dates(text):
    def jsl(m): return m.group(0).replace(" ", "")
    text = re.sub(r"(?:[A-Za-z]\s){2,}[A-Za-z]", jsl, text)

    def jsd(m): return m.group(0).replace(" ", "")
    text = re.sub(r"(?:\d\s){3}\d", jsd, text)

    text = re.sub(r"D\s*A\s*G\s*S\s*D\s*A\s*T\s*O","nå", text, flags=re.I)
    return text

def extract_periods_from_cv(cv_raw):
    if not cv_raw:
        return []
    t = normalize_broken_dates(cv_raw).replace("–","-").replace("—","-")
    pattern = r"""
        (\b(?:\d{4}|\d{1,2}/\d{4}|[A-Za-z]{3,9}\s?\d{4})\b)
        \s*-\s*
        (\b(?:\d{4}|nå|nu|present|current|\d{1,2}/\d{4}|[A-Za-z]{3,9}\s?\d{4})\b)
    """
    matches = re.findall(pattern, t, flags=re.I|re.VERBOSE)
    out=[]
    for s,e in matches:
        try: sd = dateutil.parser.parse(s, default=datetime(1900,1,1))
        except Exception: continue
        if e.lower() in ("nå","present","current","nu"):
            ed = datetime.now()
        else:
            try: ed = dateutil.parser.parse(e, default=datetime(1900,1,1))
            except Exception: continue
        if ed>=sd:
            out.append((sd,ed))
    return out

def extract_roles_near_periods(cv_raw, periods):
    lines = cv_raw.split("\n")
    roles=[]
    for s,e in periods:
        ys,ye=str(s.year),str(e.year)
        role=None
        for i,line in enumerate(lines):
            if ys in line or ye in line:
                neigh=lines[max(0,i-3):min(len(lines),i+4)]
                for n in neigh:
                    nl=n.lower()
                    if any(k in nl for k in [
                        "developer","utvikler","engineer","konsulent",
                        "software","backend","fullstack","system"
                    ]):
                        role=n
                        break
                break
        roles.append({"start":s,"end":e,"role":role})
    return roles

def calculate_developer_experience(periods_with_roles):
    dev=["developer","utvikler","engineer","konsulent","software",
         "backend","fullstack","system"]
    days=0
    for p in periods_with_roles:
        r=(p["role"] or "").lower()
        if any(k in r for k in dev):
            days+=(p["end"]-p["start"]).days
    return round(days/365,2)

def extract_total_experience(cv_raw):
    p = extract_periods_from_cv(cv_raw)
    wr = extract_roles_near_periods(cv_raw,p)
    return calculate_developer_experience(wr)

############################################################
# JOB CLASSIFIER + MATCH SCORE  (FULL)
############################################################

def classify_job_sentences(job_text):
    t = job_text.lower()
    sents = re.split(r"[.!?\n]", t)
    sents = [s.strip() for s in sents if len(s.strip())>5]

    krav_kw=[
        "må ha","må kunne","vi ser etter","vi søker","vi ønsker",
        "bør ha","du bør ha","vi forventer","krav","forventes",
        "du har erfaring","erfaring med er nødvendig","må beherske"
    ]
    bonus_kw=[
        "det er en fordel","kjekt om","gjerne erfaring",
        "bonus om","fint om","nyttig med","helst erfaring"
    ]
    miljø_kw=[
        "vi jobber med","hos oss bruker vi","stacken vår",
        "miljøet vårt","teknologistack","teamet bruker"
    ]
    oppgaver_kw=[
        "arbeidsoppgaver","dine oppgaver","ansvarsområder",
        "i denne rollen","du vil ha ansvar"
    ]
    rolle_kw=["som utvikler","i rollen","rollen innebærer"]
    disclaim_kw=[
        "ikke et krav","ikke nødvendig","trenger ikke","fleksibel"
    ]

    res={
        "krav":[],"bonus":[],"miljø":[],"oppgaver":[],"rolle":[],
        "disclaimers":[],"annet":[]
    }

    for s in sents:
        if any(k in s for k in disclaim_kw): res["disclaimers"].append(s)
        elif any(k in s for k in krav_kw): res["krav"].append(s)
        elif any(k in s for k in bonus_kw): res["bonus"].append(s)
        elif any(k in s for k in miljø_kw): res["miljø"].append(s)
        elif any(k in s for k in oppgaver_kw): res["oppgaver"].append(s)
        elif any(k in s for k in rolle_kw): res["rolle"].append(s)
        else: res["annet"].append(s)

    return res

def detect_role(job_text):
    t=job_text.lower()
    if any(k in t for k in ["devops","platform engineer","sre"]): return "devops"
    if any(k in t for k in ["data scientist","data engineer","machine learning","ml "]): return "data"
    if any(k in t for k in ["fullstack","full stack"]): return "fullstack"
    if any(k in t for k in ["frontend","ui-utvikler","react developer"]): return "frontend"
    if any(k in t for k in ["backend","api-utvikler","integrasjonsutvikler"]): return "backend"
    return "generic"

def detect_required_experience_years(job_text):
    t=job_text.lower()
    m=re.search(r"(?:mer enn\s+)?(\d+)\s*(?:\+)?\s*(?:år|års)\s+erfaring", t)
    if m:
        try: return int(m.group(1))
        except Exception: return None
    return None

def is_experience_flexible(job_text):
    t=job_text.lower()
    return any(k in t for k in ["fleksibel","kortere erfaring","kompenseres"])

def experience_factor(required, actual, flexible):
    if not required or required<=0:
        return 1.0
    if actual<=0:
        return 0.0

    ratio = actual/float(required)

    if flexible:
        if ratio>=1: return 1.0
        if ratio>=0.8: return 0.9
        if ratio>=0.6: return 0.75
        if ratio>=0.4: return 0.5
        if ratio>=0.25: return 0.3
        return 0.15

    else:
        if ratio>=1: return 1.0
        if ratio>=0.9: return 0.85
        if ratio>=0.7: return 0.65
        if ratio>=0.5: return 0.45
        if ratio>=0.3: return 0.25
        return 0.1

def classify_skill_for_role(role, skill):
    s=skill.lower()

    cloud=["azure","aws","gcp","cloud"]
    db=["sql","postgres","mysql","oracle","database"]
    devops=["docker","kubernetes","k8s","ci/cd","github actions",
            "azure devops","jenkins","terraform"]

    frontend=["react","angular","vue","javascript","typescript","html","css"]

    if role in ("backend","fullstack","generic"):
        core=["java","kotlin","go",".net","c#","spring boot","rest api",
              "microservices"] + db
        secondary = cloud + devops + ["git","linux"]
        bonus = frontend
    elif role=="frontend":
        core=frontend
        secondary=["api","graphql","testing"]
        bonus=cloud+devops
    elif role=="devops":
        core=devops+cloud
        secondary=["linux","bash","python"]
        bonus=db+["java","kotlin"]
    elif role=="data":
        core=["python","pandas","spark","sql","databricks"]
        secondary=cloud+["etl","data pipeline"]
        bonus=devops+frontend
    else:
        core=[]; secondary=[]; bonus=[]

    if any(k in s for k in core): return "core"
    if any(k in s for k in secondary): return "secondary"
    if any(k in s for k in bonus): return "bonus"
    return "secondary"

def compute_match_score(job_text, job_skills, skills_match, missing, cv_skills, experience_years):
    role = detect_role(job_text)
    segs = classify_job_sentences(job_text)

    krav = segs["krav"]
    bonus_sents = segs["bonus"]
    miljø = segs["miljø"]
    rolle_sents = segs["rolle"]
    oppgaver = segs["oppgaver"]
    disclaimers = segs["disclaimers"]

    weights={"core":3.0,"secondary":1.5,"bonus":0.5,"environment":0.0}

    backend_langs=["java","kotlin","go","c#",".net","python"]

    def is_backend_lang(x):
        x=x.lower()
        return any(k in x for k in backend_langs)

    job_lang=[s for s in job_skills if is_backend_lang(s)]
    cv_lang=[s for s in cv_skills if is_backend_lang(s)]

    def in_sents(skill, sents):
        sl=skill.lower()
        return any(sl in s for s in sents)

    total_possible=0.0
    total_achieved=0.0
    minus=0.0
    cat={}

    if role in ("backend","fullstack","generic") and job_lang:
        total_possible += weights["core"]
        if cv_lang:
            total_achieved += weights["core"]
        else:
            minus += weights["core"] * 0.5

    for skill in job_skills:
        if is_backend_lang(skill) and role in ("backend","fullstack","generic"):
            cat[skill]="environment"
            continue

        if in_sents(skill,disclaimers):
            final="bonus"
        elif in_sents(skill,miljø):
            final="environment"
        elif in_sents(skill,bonus_sents):
            final="bonus"
        elif in_sents(skill,krav) or in_sents(skill,rolle_sents) or in_sents(skill,oppgaver):
            final=classify_skill_for_role(role, skill)
        else:
            final="environment"

        cat[skill]=final
        w=weights[final]
        total_possible+=w
        if skill in skills_match:
            total_achieved+=w

    for skill in missing:
        if is_backend_lang(skill) and role in ("backend","fullstack","generic"):
            continue
        if cat.get(skill)=="core":
            minus += weights["core"]*0.5

    skill_ratio = max(0.0, (total_achieved - minus) / total_possible) if total_possible>0 else 0.0

    required = detect_required_experience_years(job_text)
    flex = is_experience_flexible(job_text)
    exp_factor = experience_factor(required, experience_years, flex)

    overall = 0.6*skill_ratio + 0.4*exp_factor
    overall = max(0.0, min(overall, 1.0))

    return round(overall*100, 1)

############################################################
# FLASK APP
############################################################

app = Flask(__name__)
CORS(app)

############################################################
# FILE READERS
############################################################

def extract_cv_text(cv_file):
    try:
        text=""
        with pdfplumber.open(cv_file) as pdf:
            for p in pdf.pages:
                t=p.extract_text()
                if t:
                    text+=t+"\n"
        return text
    except Exception:
        return ""

def extract_job_text(url, manual):
    full=""
    if url:
        try:
            html=requests.get(url,timeout=5).text
            soup=BeautifulSoup(html,"html.parser")
            full=soup.get_text(" ",strip=True)
        except Exception:
            pass
    if manual:
        full+=" "+manual
    return re.sub(r"\s+"," ",full).strip()

############################################################
# ANALYZE
############################################################

@app.route("/analyze", methods=["POST"])
def analyze():
    cv_file = request.files.get("cv")
    cv_raw = extract_cv_text(cv_file) if cv_file else ""
    cv_text = clean_cv_text(cv_raw)

    job_url = request.form.get("jobUrl","")
    job_text_input = request.form.get("jobText","")
    job_text = extract_job_text(job_url, job_text_input)

    cv_skills_raw = extract_skills_from_text(cv_text)
    job_skills_raw = extract_skills_from_text(job_text)

    cv_skills = [normalise_skill(s) for s in cv_skills_raw]
    job_skills = [normalise_skill(s) for s in job_skills_raw]

    skills_match=[]
    missing=[]

    for js in job_skills:
        matched=False
        for cs in cv_skills:
            if js == cs or semantic_match(js, cs):
                matched=True
                break
        if matched:
            skills_match.append(js)
        else:
            missing.append(js)

    skills_match = sorted(set(skills_match))
    missing = sorted(set(missing))

    experience_years = extract_total_experience(cv_raw)

    match_score = compute_match_score(
        job_text, job_skills, skills_match, missing, cv_skills, experience_years
    )

    return jsonify({
        "skills_cv":cv_skills,
        "skills_job":job_skills,
        "skillsMatch":skills_match,
        "missingSkills":missing,
        "matchScore":match_score,
        "experienceYears":experience_years
    })

############################################################
# PROJECT SKILL CHECK
############################################################

def appears_in_projects(skill, projects):
    s = normalise_skill(skill).lower()
    doc_s = nlp(s)

    for p in projects:
        p_text = p.lower()

        if s in p_text:
            return True

        try:
            if doc_s.similarity(nlp(p_text)) >= 0.80:
                return True
        except Exception:
            pass

        if any(w in p_text for w in s.split()):
            return True

    return False

############################################################
# MISSING SKILLS – GRUPPERING + LÆRINGS-SVAR
############################################################

CLOUD_SKILLS = {"aws", "azure", "gcp", "google cloud", "cloud"}
DEVOPS_SKILLS = {"docker", "kubernetes", "k8s", "terraform", "ci/cd"}
LANG_SKILLS = {"kotlin", "go"}

def select_missing_skill_representatives(missing):
    """
    Velg maks 3 representative missing skills:
    - 1 fra cloud
    - 1 fra devops
    - 1 fra språk (go/kotlin)
    Ignorerer f.eks. pandas.
    """
    remaining = list(dict.fromkeys(missing))  # unike, behold rekkefølge
    reps = []

    def pick(group_set):
        nonlocal remaining, reps
        for s in remaining:
            if s in group_set:
                reps.append(s)
                remaining = [x for x in remaining if x not in group_set]
                return

    pick(CLOUD_SKILLS)
    pick(DEVOPS_SKILLS)
    pick(LANG_SKILLS)

    return reps[:3]

#--------------------------------------------

def generate_interview_answer(skill, project_text):
    prompt = f"""
    Du er en norsk intervjumentor.
    Lag et profesjonelt læringssvar på 7–10 setninger.
    Skriv som om jeg forklarer muntlig i et ekte intervju.
    
    KRAV:
    - Start svaret på forskjellige måter — ikke alltid "I et prosjekt". Variér åpningen med setninger som "En situasjon hvor jeg brukte dette var …", "Et konkret tilfelle er …" eller "Et godt eksempel er …".
    - Forklar hvordan jeg realistisk ville lært {skill}, knyttet til arbeidshverdagen.
    - Velg én strategi: strukturert plan, hands-on prototype, eller “learn by fixing” (debug-drevet).
    - Svar personlig, tydelig og praktisk.
    - Ingen punktlister.
    - Ingen engelsk.
    - Ingen fiktive teknologier.
    
    Prosjektbakgrunn (kun kontekst – ikke kopier tekst):
    {project_text}
    """

    return groq_call(prompt)

#------------------------------------------------

def refine_answers_batch(questions, answers, level):
    if not questions or not answers or len(questions) != len(answers):
        return answers

    items = [{"q": q, "a": a} for q, a in zip(questions, answers)]

    prompt = f"""
    Du er en norsk intervjumentor. Forbedre svarene uten å endre fakta.

    STILKRAV:
    - 6–10 setninger
    - muntlig og profesjonelt
    - hvert svar SKAL åpne forskjellig (varier starter: hendelse, kontekst, refleksjon, læring, resultat, “en gang”, “jeg husker særlig da…” etc.)
    - ingen felles tekstblokker mellom svar
    - ingen punktlister
    - ingen engelske ord
    - ingen repetitiv setningsstruktur
    - hvert svar skal ha unik rytme og fortellerstil


    Returner KUN en JSON-liste.
    
    DATA:
    {json.dumps(items, ensure_ascii=False)}
    """

    try:
        resp = requests.post(
            GROQ_API_URL,
            headers={
                "Authorization": f"Bearer {os.environ.get('GROQ_API_KEY')}",
                "Content-Type": "application/json"
            },
            json={
                "model": MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.6,
                "max_tokens": MAX_TOKENS
            },
            timeout=60
        )

        data = resp.json()
        if "choices" not in data:
            if "error" in data:
                return [f"[Groq ERROR] {data['error'].get('message', 'Ukjent feil')}"]
            return answers

        raw = data["choices"][0]["message"]["content"].strip()
        start = raw.find("[")
        end = raw.rfind("]")

        if start != -1 and end != -1:
            parsed = json.loads(raw[start:end+1])
            if isinstance(parsed, list) and len(parsed) == len(answers):
                return parsed

    except Exception:
        pass

    #Alltid returner kun strenger — aldri objekter
    safe = []
    for a in answers:
        safe.append(a if isinstance(a, str) else str(a))

    return safe



############################################################
# INTERVIEW
############################################################
@app.route("/interview", methods=["POST"])
def interview():
    skills_match_raw = json.loads(request.form.get("skillsMatch","[]"))
    missing_skills_raw = json.loads(request.form.get("missingSkills","[]"))

    skills_match_raw = [normalise_skill(s) for s in skills_match_raw]
    missing_skills_raw = [normalise_skill(s) for s in missing_skills_raw]

    projects_raw = request.form.get("projects","[]")
    try:
        projects=json.loads(projects_raw)
        if isinstance(projects,str):
            projects=[projects]
    except Exception:
        projects=[projects_raw] if projects_raw.strip() else []

    level = request.form.get("level","experienced").lower()

    lang_black = ["norsk","norwegian","engelsk","english","språk: norsk"]

    # -------- Matchede skills (filtrert på prosjekter) --------
    skills_match=[]
    for s in skills_match_raw:
        if s in lang_black or s.startswith("språk"):
            continue
        if appears_in_projects(s, projects):
            skills_match.append(s)

    skills_match = list(dict.fromkeys(skills_match))[:5]

    #Missing skills
    missing = [
        s for s in missing_skills_raw
        if s not in lang_black
           and not s.startswith("språk")
           and s != "pandas"
    ]

    #velg representative missing skills
    selected_missing = select_missing_skill_representatives(missing)

    # bullets fra CV
    cv_file = request.files.get("cv")
    cv_raw = extract_cv_text(cv_file) if cv_file else ""
    bullets = extract_bullets(cv_raw)

    questions = []
    draft_answers = []
    used_projects = []

    #MATCHED SKILLS → prosjektbaserte STAR-utkast
    for skill in skills_match:
        q = f"Kan du beskrive et konkret eksempel der du brukte {skill}?"
        combined = combine_and_refine_projects(skill, projects, level, used_projects)
        if combined:
            a = combined
        else:
            b = find_relevant_bullet(bullets, skill)
            a = craft_story_answer(skill, b)

        questions.append(q)
        draft_answers.append(a)

    #MISSING SKILLS → lærings-utkast
    for skill in selected_missing:
        q = f"Hvordan vil du lære deg {skill} hvis rollen krever det?"
        a = generate_interview_answer(skill, " ".join(projects))
        questions.append(q)
        draft_answers.append(a)

    #Ett samlet kall til Ollama for å gjøre svarene skarpe
    final_answers = refine_answers_batch(questions, draft_answers, level)

    return jsonify({
        "questions": questions,
        "answers": [a["a"] if isinstance(a, dict) else a for a in final_answers],
        "skillsMatch": skills_match,
        "missingSkills": missing,
        "projects": projects
    })

############################################################
# RUN
############################################################

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=2000)
