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

SYSTEM WORD: {system_word}
CATEGORIES: {categories}
STRENGTHS: {strengths}
WEAKNESSES: {weaknesses}
TYPICAL COUNTERS: {counters}

BATTLE RULES:
1. Direct opposition is required (water destroys fire, light eliminates darkness)
2. Always choose lowest cost option that will be effective
3. Physical objects need physical counters (hammer vs glass)
4. Abstract concepts need conceptual counters (truth vs lie)

SELECTION PRIORITY:
1. Complete destruction of system word
2. Direct counter mechanism
3. Lowest possible cost

FORMAT ENFORCEMENT:
- FIRST LINE MUST BEGIN WITH "COUNTER:"
- NO INTRODUCTORY TEXT
- NO EXPLANATION BEFORE OR AFTER YOUR SELECTION
- RESPOND ONLY WITH: COUNTER: [word] | COST: [number] | RATIONALE: [reason]

WORD OPTIONS:
{word_list}

EXAMPLES:
Lion-COUNTER: Gun | COST: 10 | RATIONALE: Gun kills lion
BigAnimal-Counter: Gun | COST: 10 | RATIONALE: Gun kills big animals
SmallAnimal-Counter: Rock | COST: 2 | RATIONALE: Rock kills small animals
Candle-COUNTER: Wind | COST: 13 | RATIONALE: Wind extinguishes flames
Paper-COUNTER: Flame | COST: 5 | RATIONALE: Fire burns paper
Shadow-COUNTER: Light | COST: 7 | RATIONALE: Light dispels darkness
Rock-COUNTER: Hammer | COST: 8 | RATIONALE: Hammer shatters rock
Ice-COUNTER: Heat | COST: 9 | RATIONALE: Heat melts ice
Tree-COUNTER: Axe | COST: 6 | RATIONALE: Axe cuts through tree
Lightning-COUNTER: Ground | COST: 3 | RATIONALE: Ground absorbs electrical energy
Pride-COUNTER: Humility | COST: 12 | RATIONALE: Humility overcomes pride
Fear-COUNTER: Courage | COST: 15 | RATIONALE: Courage directly confronts fear
Virus-COUNTER: Vaccine | COST: 11 | RATIONALE: Vaccine neutralizes virus
Drought-COUNTER: Rain | COST: 8 | RATIONALE: Rain eliminates drought conditions
Lie-COUNTER: Truth | COST: 9 | RATIONALE: Truth exposes and negates lies
Chain-COUNTER: Bolt Cutter | COST: 7 | RATIONALE: Bolt cutters break chains
Glass-COUNTER: Stone | COST: 2 | RATIONALE: Stone shatters glass
Darkness-COUNTER: Flashlight | COST: 5 | RATIONALE: Flashlight beam eliminates darkness
Anger-COUNTER: Compassion | COST: 14 | RATIONALE: Compassion dissolves anger
Tornado-COUNTER: Mountain | COST: 18 | RATIONALE: Mountains disrupt tornado formation
Web-COUNTER: Knife | COST: 4 | RATIONALE: Knife cuts through webs
Sound-COUNTER: Vacuum | COST: 10 | RATIONALE: Sound cannot travel through vacuum
Bacteria-COUNTER: Antibiotics | COST: 9 | RATIONALE: Antibiotics kill bacteria
Rope-COUNTER: Scissors | COST: 3 | RATIONALE: Scissors cut rope
Heat-COUNTER: Ice | COST: 7 | RATIONALE: Ice neutralizes heat
Plant-COUNTER: Herbicide | COST: 6 | RATIONALE: Herbicide kills plants
Feather-COUNTER: Leg | COST: 2 | RATIONALE: Leg can tickle feather
Feather-COUNTER: Hand | COST: 2 | RATIONALE: Hand can tickle feather
Lock-COUNTER: Key | COST: 4 | RATIONALE: Key unlocks lock
Boat-COUNTER: Iceberg | COST: 15 | RATIONALE: Iceberg sinks boat
Sword-COUNTER: Shield | COST: 8 | RATIONALE: Shield blocks sword attacks
Poison-COUNTER: Antidote | COST: 11 | RATIONALE: Antidote neutralizes poison
Computer-COUNTER: Magnet | COST: 5 | RATIONALE: Magnet disrupts computer data
Building-COUNTER: Earthquake | COST: 22 | RATIONALE: Earthquake topples buildings
Sadness-COUNTER: Joy | COST: 13 | RATIONALE: Joy overcomes sadness
Plastic-COUNTER: Fire | COST: 5 | RATIONALE: Fire melts plastic
Snake-COUNTER: Mongoose | COST: 9 | RATIONALE: Mongoose hunts and kills snakes
Army-COUNTER: Superior Strategy | COST: 17 | RATIONALE: Superior strategy defeats armies
Diamond-COUNTER: Laser | COST: 16 | RATIONALE: Laser cuts through diamond
Memory-COUNTER: Trauma | COST: 14 | RATIONALE: Trauma distorts and erases memories
Storm-COUNTER: Clear Sky | COST: 11 | RATIONALE: Clear sky represents storm's absence
Phone-COUNTER: EMP | COST: 12 | RATIONALE: EMP disables electronic devices
Flame-COUNTER: Water | COST: 4 | RATIONALE: Water extinguishes flame
Robot-COUNTER: Logic Paradox | COST: 10 | RATIONALE: Paradox crashes robot systems
Hate-COUNTER: Love | COST: 16 | RATIONALE: Love transforms and neutralizes hate
Noise-COUNTER: Silence | COST: 8 | RATIONALE: Silence eliminates noise
Earthquake-COUNTER: Dampening System | COST: 19 | RATIONALE: Dampeners absorb seismic waves
Desert-COUNTER: Irrigation | COST: 13 | RATIONALE: Irrigation transforms desert to fertile land
Wall-COUNTER: Wrecking Ball | COST: 9 | RATIONALE: Wrecking ball demolishes walls
Acid-COUNTER: Base | COST: 6 | RATIONALE: Base neutralizes acid
War-COUNTER: Diplomacy | COST: 15 | RATIONALE: Diplomacy prevents and ends wars
Addiction-COUNTER: Willpower | COST: 18 | RATIONALE: Willpower overcomes addiction
Monster-COUNTER: Hero | COST: 17 | RATIONALE: Hero defeats monster

"""

    return prompt_template.format(
        word_list=json.dumps({w['word_id']: w['text'] for w in WORD_DATA['training_data']}, indent=2),
        system_word=system_word,
        categories=', '.join(system_info.get('categories', [])),
        strengths=', '.join(system_info.get('strengths_against', {}).get('examples', [])),
        weaknesses=', '.join(system_info.get('weaknesses_against', {}).get('examples', [])),
        counters=', '.join(system_info.get('synergy_with', []))
    )

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
                    "temperature": 0.3,
                    "num_predict": 100,
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

