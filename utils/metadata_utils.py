import spacy
from keybert import KeyBERT
from langdetect import detect
from nltk.tokenize import sent_tokenize
import re
from utils.extract_text import extract_title_by_font_block



nlp = spacy.load("en_core_web_sm")
kw_model = KeyBERT()

def detect_language(text):
    try:
        return detect(text)
    except:
        return "unknown"

def extract_section(text, section_name):

    pattern = rf"{section_name}[:\n]+(.+?)(?=\n[A-Z][^\n]*?:|\n\n|\Z)"
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else None

#title
def extract_title(text):
    lines = text.strip().split("\n")
    lines = [line.strip() for line in lines if line.strip()]

    title_lines = []
    collecting = False

    for i in range(len(lines[:15])):
        line = lines[i]
        line_lower = line.lower()

        # Hard stop if we hit abstract/intro/university
        if any(x in line_lower for x in ["abstract", "introduction", "email", "doi", "journal", "university", "institute", "department", "International", "2016","2017"]):
            break

        # Skip unnecessary lines
        if re.search(r"[@\[\]{}<>]", line):
            continue

        # start when line looks like a good title
        if not collecting and 8 < len(line) < 150 and line[0].isupper():
            title_lines.append(line)
            collecting = True
            continue

        if collecting:
            # Check if line looks like authors
            # Case 1: 2+ commas, typical for author lists
            if line.count(",") >= 2:
                break
            # Case 2: Line contains initials
            if re.search(r"\b[A-Z]\.\s?[A-Z][a-z]+", line):
                break
           # Case 3: Stop if line contains a year (likely metadata or reference)
            if re.search(r"\b(19|20)\d{2}\b", line):
               break


 
            # Else
            title_lines.append(line)
            break  

    return " ".join(title_lines).strip() if title_lines else "N/A"



def extract_all_sections(text):
    section_headers = [
        "Abstract", "Introduction", "Background", "Objective", "Methodology",
        "Model", "Approach", "Case Study", "Experiment", "Results", "Discussion",
        "Conclusion", "Summary", "References", "Acknowledgement"
    ]
    sections = {}
    for header in section_headers:
        pattern = re.compile(rf"{header}[:\s]*\n(.+?)(?=\n[A-Z][^\n]{{2,}}:|\n\n|\Z)", re.IGNORECASE | re.DOTALL)
        match = pattern.search(text)
        if match:
            sections[header.lower()] = match.group(1).strip()
    return sections


ALGORITHM_KEYWORDS = [
    "milp", "lp", "linear programming", "mixed-integer", "metaheuristic",
    "genetic algorithm", "ga", "simulated annealing", "particle swarm optimization",
    "pso", "tabu search", "ant colony", "svm", "random forest", "xgboost",
    "cnn", "lstm", "regression", "clustering", "k-means", "gradient descent","python", "matlab", "gurobi", "cplex", "anylogic", "excel", "r", "pytorch", "tensorflow",
    "scikit-learn", "simulink", "keras"
]



def generate_metadata(text, pdf_path=None):
    doc = nlp(text)
    sentences = list(doc.sents)
      
      # Semantic section mapping
    sections = extract_all_sections(text)

    abstract = sections.get("abstract", "")
    introduction = sections.get("introduction", "")
    methodology = (
       sections.get("methodology")
        or sections.get("model")
       or sections.get("approach")
      or "N/A"
)
    results = sections.get("results") or sections.get("discussion", "")
    conclusion = sections.get("conclusion") or sections.get("summary", "")
    objectives = sections.get("objective", "")
    
    # 1. Title
    title = extract_title_by_font_block(pdf_path) if pdf_path else extract_title(text)
    
    # 2. Abstract
    abstract = extract_section(text, "Abstract")
    if not abstract and len(sentences) > 5:
        abstract = " ".join([s.text for s in sentences[1:6]])

    # 3. Keywords
    raw_keywords = extract_section(text, "Keywords")
    if raw_keywords:
        keyword_list = [kw.strip() for kw in raw_keywords.split(",")]
    else:
        keyword_list = [kw[0] for kw in kw_model.extract_keywords(text, top_n=10)]
    # 5. algorithms
    algorithms = list({
    word.upper() if word.isupper() else word.title()
    for word in ALGORITHM_KEYWORDS
    if re.search(rf"\b{re.escape(word)}\b", text.lower())
    })   

    # 4. Authors and organizations
    people = list(set(ent.text for ent in doc.ents if ent.label_ == "PERSON"))
    orgs = list(set(ent.text for ent in doc.ents if ent.label_ == "ORG"))
    
    word_count = len(text.split())
    read_time = round(word_count / 200)  # average reading speed


    return {
        "title": title,
        "abstract": abstract or "N/A",
        "keywords": keyword_list,
        "authors": people,
        "affiliations": orgs[:5],
        "organizations": orgs,
        "introduction": introduction,
        "methodology": methodology,
        "results": results[:500],
        "conclusion": conclusion,
        "language": detect_language(text),
        "objectives": objectives,
        "word_count": word_count,
        "algorithms": algorithms,
        "read_time": f"{read_time} min read",
        "summary": " ".join(sent_tokenize(text)[:3])
     

    }
