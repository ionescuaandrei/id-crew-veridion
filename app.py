from flask import Flask, request, jsonify
import requests
import json

app = Flask(__name__)

# Load enhanced dataset
with open('word_system_dataset.json') as f:
    WORD_DATA = json.load(f)

# Create quick lookup dictionaries
WORD_LOOKUP = {word['text'].lower(): word for word in WORD_DATA['training_data']}
CATEGORY_MAP = {
    "combustibles": [
        "Feather",
        "Coal",
        "Leaf",
        "Paper",
        "Twig"
    ],
    "organic_materials": [
        "Feather",
        "Leaf",
        "Twig",
        "Whale"
    ],
    "lightweight_objects": [
        "Feather",
        "Leaf",
        "Paper"
    ],
    "fire_heat": [
        "Coal",
        "Flame",
        "Laser",
        "Magma",
        "Explosion",
        "Volcano"
    ],
    "earth_geology": [
        "Pebble",
        "Rock",
        "Earthquake",
        "Stone",
        "Sandstorm",
        "Earth",
        "Tectonic Shift"
    ],
    "water_cold": [
        "Water",
        "Ice",
        "Tsunami"
    ],
    "physical_weapons": [
        "Sword",
        "Gun",
        "Laser",
        "Explosion",
        "Nuclear Bomb"
    ],
    "defensive_tools": [
        "Shield",
        "Rope",
        "Peace"
    ],
    "biological_threats": [
        "Disease",
        "Bacteria",
        "Virus",
        "Plague"
    ],
    "biological_defenses": [
        "Cure",
        "Vaccine",
        "Antimatter",
        "Rebirth"
    ],
    "metaphysical": [
        "Shadow",
        "Light",
        "Fate",
        "Karma",
        "Enlightenment",
        "Human Spirit"
    ],
    "air_wind": [
        "Sound",
        "Storm",
        "Echo",
        "Thunder",
        "Wind"
    ],
    "abstract_concepts": [
        "Time",
        "Fate",
        "Logic",
        "Gravity",
        "Karma",
        "Enlightenment",
        "Human Spirit",
        "Entropy"
    ],
    "technology": [
        "Robots",
        "Laser",
        "Nuclear Bomb",
        "Antimatter"
    ],
    "cosmic_phenomena": [
        "Earth",
        "Moon",
        "Star",
        "Supernova",
        "Gamma-Ray Burst",
        "Apocalyptic Meteor",
        "Neutron Star",
        "Supermassive Black Hole"
    ]
}
for word in WORD_DATA['training_data']:
    for category in word['categories']:
        CATEGORY_MAP.setdefault(category, []).append(word['text'])

OLLAMA_API_URL = "http://localhost:11434/api/generate"

def build_strategy_prompt(system_word):
    # Get system word analysis from dataset
    system_info = WORD_LOOKUP.get(system_word.lower(), {})
    
    prompt_template = """You are an automated word battle system that MUST follow this exact response format:
COUNTER: [word] | COST: [number] | RATIONALE: [brief reason]

Your task: Find the most effective and cheapest counter to defeat {system_word}.

SYSTEM WORD ANALYSIS:
- Text: {system_word}
- Description: {description}
- Categories: {categories}
- Physical Properties: {physical_props}
- Power Level: {power_level}/100
- Strengths Against: {strengths}
- Vulnerabilities: {weaknesses}
- Known Synergies: {synergies}
- Historical Counters: {historical_counters}

BATTLE RULES:
1. Direct counter-mechanism required (water > fire, truth > lie)
2. Lower cost always preferred if equally effective
3. Consider physical properties ({physical_props})
4. Account for power levels (counter should have ≥70% of target's power)
5. Prefer solutions from historical counters when applicable

SELECTION PRIORITY:
1. Complete neutralization of {system_word}
2. Matching vulnerability exploitation
3. Direct category opposition
4. Lowest feasible cost

FORMAT ENFORCEMENT:
- RESPOND ONLY WITH: COUNTER: [word] | COST: [number] | RATIONALE: [reason]
- First line must begin with "COUNTER:"
- No markdown or extra formatting

WORD DATABASE:
{enhanced_word_list}

EXAMPLE COUNTERS FROM DATASET:
{example_counters}"""

    # Enhanced word list with more properties
    word_list = []
    for word in WORD_DATA['training_data']:
        word_list.append(
            f"{word['text']} (ID: {word['word_id']}) - "
            f"Categories: {', '.join(word.get('categories', []))} | "
            f"Power: {word.get('power_level', 50)} | "
            f"Props: {word.get('physical_properties', 'N/A')} | "
            f"Weaknesses: {', '.join(word.get('weaknesses_against', {}).get('examples', []))}"
        )

    # Generate examples from historical data
    example_counters = []
    for example in WORD_DATA.get('historical_interactions', [])[:5]:
        example_counters.append(
            f"{example['challenge']}-COUNTER: {example['response']} | "
            f"COST: {example['cost']} | RATIONALE: {example['reason']}"
        )

    return prompt_template.format(
        system_word=system_word,
        description=system_info.get('description', 'No description available'),
        categories=', '.join(system_info.get('categories', []) or 'None',
        physical_props=system_info.get('physical_properties', 'N/A'),
        power_level=system_info.get('power_level', 50),
        strengths=', '.join(system_info.get('strengths_against', {}).get('examples', [])) or 'None',
        weaknesses=', '.join(system_info.get('weaknesses_against', {}).get('examples', [])) or 'None',
        synergies=', '.join(system_info.get('synergy_with', [])) or 'None',
        historical_counters=', '.join(system_info.get('historical_defeats', [])) or 'None',
        enhanced_word_list='\n'.join(word_list),
        example_counters='\n'.join(example_counters) or 'No historical examples'
    ))

def extract_counter(response):
    try:
        lines = [line.strip() for line in response.split('\n')]
        for line in lines:
            if line.startswith('COUNTER:'):
                return line.split('|')[0].split(':')[1].strip()
        return None
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
                    "temperature": 0.1,
                    "num_predict": 50,
                    "stop": ["\n"]
                }
            }
        )
        response.raise_for_status()
        
        ai_response = response.json()["response"]
        counter_word = extract_counter(ai_response)
        
        if counter_word:
            return jsonify({
                "system_word": system_word,
                "ai_counter": counter_word,
                "full_response": ai_response
            })
        return jsonify({"error": "Invalid response format", "response": ai_response}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True, use_reloader=False)