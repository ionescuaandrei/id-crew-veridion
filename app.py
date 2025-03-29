from flask import Flask, request, jsonify
import requests
import json
import re
from difflib import get_close_matches
import random

app = Flask(__name__)

# Load dataset
with open('word_system_dataset.json') as f:
    WORD_DATA = json.load(f)

# Create lookup dictionaries
WORD_LOOKUP = {word['text'].lower(): word for word in WORD_DATA['training_data']}
VALID_WORDS = {word['text'].lower(): word for word in WORD_DATA['training_data']}

OLLAMA_API_URL = "http://localhost:11434/api/generate"

# Define categorical oppositions
CATEGORY_OPPOSITIONS = {
    'Biological': {'Medical', 'Weapon', 'Fire'},
    'Fire': {'Water', 'Ice', 'Sand'},
    'Water': {'Drought', 'Earth', 'Plant'},
    'Abstract': {'Concrete', 'Logic', 'Reality'},
    'Physical': {'Energy', 'Abstract', 'Deconstruction'},
    'Digital': {'EMP', 'Analog', 'Virus'},
    'Geological': {'Liquid', 'Drill', 'Tectonic'},
    'Energy': {'Insulation', 'Absorption', 'Dispersion'}
}

def build_strategy_prompt(system_word):
    system_info = WORD_LOOKUP.get(system_word.lower(), {})
    
    # Extract critical decision factors
    categories = system_info.get('categories', [])
    weaknesses = system_info.get('weaknesses_against', {})
    materials = system_info.get('material_composition', [])
    
    prompt_template = """Analyze the system word and choose the optimal counter from valid options using this priority:
1. Direct weaknesses from known vulnerabilities
2. Categorical oppositions
3. Material composition advantages
4. Lowest cost valid option

# System Word Analysis
WORD: {system_word}
- CATEGORIES: {categories}
- MATERIALS: {materials}
- WEAKNESSES: {weakness_examples} ({weakness_mechanism})

# Selection Rules
- Biological → Use Weapons/Medicine
- Fire → Counter with Water/Ice
- Digital → Use EMP/Antivirus
- Physical → Use Energy/Deconstruction
- Abstract → Counter with Concrete/Logic

# Examples
- SYSTEM: Lion (Biological) → COUNTER: Gun (Weapon)
- SYSTEM: Flame (Fire) → COUNTER: Water (Liquid)
- SYSTEM: Computer (Digital) → COUNTER: Virus (Antivirus)

# Valid Options
{word_list}

Respond ONLY with: COUNTER: [word] | COST: [$] | LOGIC: [reason]"""

    return prompt_template.format(
        system_word=system_word,
        categories=', '.join(categories),
        materials=', '.join(materials),
        weakness_examples=', '.join(weaknesses.get('examples', [])),
        weakness_mechanism=weaknesses.get('mechanism', 'Unknown'),
        word_list="\n".join([
            f"- {w['text']} ({'/'.join(w['categories'])}) ${w['cost']}"
            for w in WORD_DATA['training_data']
        ])
    )

def is_valid_counter(system_info, counter_word):
    """Check if counter is valid through weaknesses or categorical oppositions"""
    counter_info = WORD_LOOKUP.get(counter_word.lower(), {})
    
    # Direct weakness match
    system_weaknesses = [w.lower() for w in system_info.get('weaknesses_against', {}).get('examples', [])]
    if counter_word.lower() in system_weaknesses:
        return True
    
    # Categorical opposition check
    system_categories = system_info.get('categories', [])
    counter_categories = counter_info.get('categories', [])
    
    for sys_cat in system_categories:
        if sys_cat in CATEGORY_OPPOSITIONS:
            if any(op_cat in counter_categories for op_cat in CATEGORY_OPPOSITIONS[sys_cat]):
                return True
    
    # Material composition advantage
    system_materials = system_info.get('material_composition', [])
    counter_strengths = counter_info.get('strengths_against', {}).get('examples', [])
    if any(mat.lower() in [s.lower() for s in counter_strengths] for mat in system_materials):
        return True
    
    return False

def find_valid_counters(system_word):
    """Find all valid counters sorted by priority"""
    system_info = WORD_LOOKUP.get(system_word.lower(), {})
    valid = []
    
    for word in WORD_DATA['training_data']:
        if is_valid_counter(system_info, word['text']):
            priority = (
                0 if word['text'].lower() in system_info.get('weaknesses_against', {}).get('examples', []) else
                1 if any(cat in CATEGORY_OPPOSITIONS.get(sys_cat, []) 
                        for sys_cat in system_info.get('categories', [])
                        for cat in word['categories']) else
                2
            )
            valid.append((word, priority))
    
    # Sort by: priority → effectiveness → cost
    return sorted(valid, key=lambda x: (
        x[1],
        -x[0]['effectiveness_score'],
        x[0]['cost']
    ))

def extract_counter(response, system_word):
    """Extract and validate counter from AI response"""
    try:
        match = re.search(r"COUNTER:\s*([\w\s]+)\b", response, re.IGNORECASE)
        return match.group(1).strip() if match else None
    except:
        return None

@app.route('/battle', methods=['POST'])
def word_battle():
    system_word = request.json.get('word')
    if not system_word:
        return jsonify({"error": "Missing word parameter"}), 400

    prompt = build_strategy_prompt(system_word)
    
    try:
        response = requests.post(
            OLLAMA_API_URL,
            json={
                "model": "llama3:8b",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "num_predict": 100,
                    "stop": ["\n"]
                }
            }
        )
        response.raise_for_status()
        
        ai_response = response.json()["response"]
        suggested_counter = extract_counter(ai_response, system_word)
        
        # Find best valid counter
        valid_counters = find_valid_counters(system_word)
        
        if valid_counters:
            # Get top valid counter
            best_counter = valid_counters[0][0]
            if suggested_counter and suggested_counter.lower() == best_counter['text'].lower():
                final_counter = suggested_counter
            else:
                final_counter = best_counter['text']
                ai_response += f" (Corrected to {final_counter})"
        else:
            final_counter = random.choice(WORD_DATA['training_data'])['text']
            ai_response += f" (Random fallback: {final_counter})"

        counter_info = WORD_LOOKUP.get(final_counter.lower(), {})
        return jsonify({
            "system_word": system_word,
            "counter": final_counter,
            "cost": counter_info.get('cost', 'unknown'),
            "logic": counter_info.get('strengths_against', {}).get('mechanism', 'Categorical opposition'),
            "response": ai_response
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)