## Words of Power Battle System

A strategic word combat API developed for the [Words of Power Hackathon](https://www.notion.so/Hackathon-Challenge-Words-of-Power-1c5a368b7e0c803ab3c0c3865cf1eb12). Implements rock-paper-scissors mechanics with cost optimization and categorical relationships.

## This project uses Ollama:8b locally
## Please install the AI.
## Installation

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Run the specific model from [Ollama Models](https://ollama.com/search)
ollama run ollama:8b 
```

## Game Rules

### Core Mechanics
- **60 Unique Words** with costs ranging from $1 to $45
- **5 Round Matches** with cumulative scoring
- **Victory Conditions**:
  - Success: Deduct word cost only
  - Failure: Deduct cost + $30 penalty
  - Lowest total cost after 5 rounds wins

### Battle Logic Hierarchy
1. Direct weaknesses (predefined vulnerabilities)
2. Categorical opposition:
   - 🧬 Biological → 🔫 Weapon/💊 Medicine
   - 🔥 Fire → 💧 Water/❄️ Ice
   - 🏗 Physical → ⚡ Energy/🤔 Abstract
   - 💻 Digital → 🛡 EMP/🦠 Antivirus
3. Material composition advantages
4. Cost optimization (cheapest valid option)

## Dataset Structure

`word_system_dataset.json` contains:

```json
{
  "training_data": [
    {
      "word_id": 7,
      "text": "Water",
      "cost": 3,
      "categories": ["Elemental", "Liquid"],
      "weaknesses_against": {
        "examples": ["Ice", "Drought"],
        "mechanism": "Frozen or evaporated"
      },
      "strengths_against": {
        "examples": ["Fire", "Magma"],
        "mechanism": "Extinguishes flames"
      },
      "effectiveness_score": 95,
      "material_composition": ["H₂O"],
      "synergy_with": ["Container", "Pipe"]
    }
  ]
}
```

## API Usage

### Request

```bash
POST /battle
Content-Type: application/json

{"word": "Fire"}
```

### Response

```json
{
  "system_word": "Fire",
  "counter": "Water",
  "cost": 3,
  "logic": "Elemental opposition (Extinguishes flames)",
  "response": "COUNTER: Water | COST: 3 | LOGIC: Fire weakness"
}
```

## Installation

```bash
# Clone repository
git clone https://github.com/yourusername/words-of-power.git
cd words-of-power

# Install dependencies
pip install flask requests

# Start server (requires Ollama running)
python app.py
```

## Code Structure

### Key components in `app.py`:

```python
# Categorical opposition matrix
CATEGORY_OPPOSITIONS = {
    'Biological': {'Medical', 'Weapon', 'Fire'},
    'Fire': {'Water', 'Ice', 'Sand'},
    'Abstract': {'Logic', 'Reality'}
}

def find_valid_counters(system_word):
    """Priority-based counter selection"""
    valid = []
    system_info = WORD_LOOKUP.get(system_word.lower(), {})
    
    for word in WORD_DATA['training_data']:
        if is_valid_counter(system_info, word['text']):
            priority = (
                0 if word['text'] in system_info['weaknesses'] else
                1 if categorical_match else
                2
            )
            valid.append((word, priority))
    
    return sorted(valid, key=lambda x: (
        x[1], 
        -x[0]['effectiveness_score'], 
        x[0]['cost']
    ))
