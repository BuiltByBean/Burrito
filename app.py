from flask import Flask, render_template, request, redirect, url_for
import json
import os
from datetime import datetime

app = Flask(__name__)

ORDERS_FILE = os.environ.get(
    'ORDERS_FILE',
    os.path.join(os.path.dirname(__file__), 'orders.json'),
)

# Menu sections — order matters, this is the flow guests walk through.
# Breakfast burrito edition.
MENU = [
    {
        'key': 'base',
        'title': 'Choose Your Vessel',
        'subtitle': 'The foundation of your feast',
        'emoji': '\U0001F32F',  # burrito
        'type': 'single',
        'required': True,
        'options': [
            'Flour Tortilla (Burrito)',
            'Burrito Bowl (No Tortilla)',
        ],
    },
    {
        'key': 'eggs',
        'title': 'Eggs',
        'subtitle': 'The first rule of breakfast burritos',
        'emoji': '\U0001F373',  # fried egg
        'type': 'single',
        'required': True,
        'options': [
            'Eggs',
            'No Eggs',
        ],
    },
    {
        'key': 'protein',
        'title': 'Meat',
        'subtitle': 'Pick your fighter — multi-select welcome',
        'emoji': '\U0001F953',  # bacon
        'type': 'multiple',
        'required': False,
        'options': [
            'Bacon',
            'Breakfast Sausage',
            'Chorizo',
            'Ham',
            'No Meat',
        ],
    },
    {
        'key': 'potatoes',
        'title': 'Potatoes',
        'subtitle': 'Crispy carbs of champions',
        'emoji': '\U0001F954',  # potato
        'type': 'single',
        'required': False,
        'options': [
            'Potatoes',
            'No Potatoes',
        ],
    },
    {
        'key': 'grilled_veggies',
        'title': 'Grilled Veggies',
        'subtitle': 'Fire-kissed and ready for battle',
        'emoji': '\U0001FAD1',  # bell pepper
        'type': 'multiple',
        'required': False,
        'options': [
            'Jalapeños',
            'Bell Pepper',
            'Onion',
        ],
    },
    {
        'key': 'cheese',
        'title': 'Cheese',
        'subtitle': 'Choose your sharpness',
        'emoji': '\U0001F9C0',  # cheese wedge
        'type': 'single',
        'required': False,
        'options': [
            'Cheddar',
            'Pepper Jack',
        ],
    },
    {
        'key': 'finish',
        'title': 'The Final Touch',
        'subtitle': 'How shall we send thee forth?',
        'emoji': '\U0001F525',  # fire
        'type': 'single',
        'required': True,
        'options': [
            'Seared Burrito',
            'Just Wrapped in a Fresh Tortilla',
        ],
    },
]


def load_orders():
    if os.path.exists(ORDERS_FILE):
        try:
            with open(ORDERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []


def save_orders(orders):
    with open(ORDERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(orders, f, indent=2)


# D&D-style stat bonuses for each ingredient.
# Format: ingredient -> list of (stat, bonus, flavor reason)
STAT_BONUSES = {
    # Vessel
    'Flour Tortilla (Burrito)':       [('CON', 1, 'Wrapped in the armor of ancient grains')],
    'Burrito Bowl (No Tortilla)':     [('DEX', 2, 'Lean and unencumbered by wrapping')],
    # Eggs
    'Eggs':                           [('WIS', 1, 'Balanced start to the journey')],
    'No Eggs':                        [('CHA', 1, 'Boldly unconventional')],
    # Meat
    'Bacon':                          [('CHA', 1, 'Universal appeal of the pig')],
    'Breakfast Sausage':              [('CON', 1, "The bards' breakfast classic")],
    'Chorizo':                        [('STR', 2, 'Fire-born warrior spice')],
    'Ham':                            [('STR', 1, 'Simple, honorable power')],
    'No Meat':                        [('WIS', 2, 'A druid walks among us')],
    # Potatoes
    'Potatoes':                       [('CON', 2, 'Hearty carbs of the realm')],
    'No Potatoes':                    [('DEX', 1, 'Unburdened by tubers')],
    # Grilled Veggies
    'Jalapeños':                      [('CON', 2, 'Forged in the fires of Mt. Doom')],
    'Bell Pepper':                    [('DEX', 1, 'Quick-striking crunch')],
    'Onion':                          [('INT', 1, 'Layers within layers, like a true strategist')],
    # Cheese
    'Cheddar':                        [('CON', 1, 'Sharp and unyielding')],
    'Pepper Jack':                    [('CHA', 2, 'The cheese of kings and dragons')],
    # Finish
    'Seared Burrito':                 [('STR', 2, 'Battle-hardened exterior')],
    'Just Wrapped in a Fresh Tortilla':[('DEX', 1, 'Pristine and agile')],
}

# Highest-stat -> D&D class mapping for the character sheet flavor
CLASS_BY_STAT = {
    'STR': ('Breakfast Barbarian',  'Raw tortilla-shredding power'),
    'DEX': ('Tortilla Rogue',       'Agile, nimble, sauce-silent'),
    'CON': ('Hash-Brown Paladin',   'A bulwark of fiber and fat'),
    'INT': ('Onion Wizard',         'Layered, scholarly, tear-inducing'),
    'WIS': ('Druid of the Feast',   'One with the crops and herds'),
    'CHA': ('Queso Bard',           'Silver-tongued and melty'),
}


def compute_stats(selections):
    """Compute D&D-style stats from a burrito's selections.
    Returns (stats_dict, applied_bonuses_list, class_tuple).
    """
    stats = {'STR': 10, 'DEX': 10, 'CON': 10, 'INT': 10, 'WIS': 10, 'CHA': 10}
    applied = []
    for _, val in selections.items():
        if not val:
            continue
        items = val if isinstance(val, list) else [val]
        for item in items:
            for stat, bonus, reason in STAT_BONUSES.get(item, []):
                stats[stat] += bonus
                applied.append({
                    'stat':   stat,
                    'bonus':  bonus,
                    'reason': reason,
                    'source': item,
                })
    # Determine class from the highest stat (stable tie-breaker)
    stat_order = ['STR', 'DEX', 'CON', 'INT', 'WIS', 'CHA']
    top_stat = max(stat_order, key=lambda s: (stats[s], -stat_order.index(s)))
    class_name, class_blurb = CLASS_BY_STAT[top_stat]
    return stats, applied, {'stat': top_stat, 'name': class_name, 'blurb': class_blurb}


def stat_modifier(score):
    return (score - 10) // 2


@app.route('/')
def index():
    return render_template('index.html', menu=MENU)


@app.route('/submit', methods=['POST'])
def submit():
    name = request.form.get('name', '').strip() or 'Anonymous Adventurer'
    notes = request.form.get('notes', '').strip()

    selections = {}
    for section in MENU:
        key = section['key']
        if section['type'] == 'single':
            val = request.form.get(key, '').strip()
            selections[key] = val or None
        else:
            vals = [v for v in request.form.getlist(key) if v]
            selections[key] = vals

    order = {
        'name': name,
        'notes': notes,
        'selections': selections,
        'timestamp': datetime.now().isoformat(timespec='seconds'),
    }

    orders = load_orders()
    orders.append(order)
    save_orders(orders)

    return redirect(url_for('confirmation', order_id=len(orders)))


@app.route('/confirmation/<int:order_id>')
def confirmation(order_id):
    orders = load_orders()
    if order_id < 1 or order_id > len(orders):
        return redirect(url_for('index'))
    order = orders[order_id - 1]
    stats, applied, char_class = compute_stats(order['selections'])
    modifiers = {k: stat_modifier(v) for k, v in stats.items()}
    return render_template(
        'confirmation.html',
        order=order,
        order_id=order_id,
        menu=MENU,
        stats=stats,
        modifiers=modifiers,
        applied=applied,
        char_class=char_class,
    )


@app.route('/orders')
def orders_view():
    orders = load_orders()

    # Build an ingredient tally so you know how much of each thing to prep
    tally = {}
    for section in MENU:
        tally[section['key']] = {
            'title': section['title'],
            'counts': {},
        }
        for opt in section['options']:
            tally[section['key']]['counts'][opt] = 0

    for order in orders:
        for key, val in order['selections'].items():
            if key not in tally:
                continue
            if isinstance(val, list):
                for v in val:
                    if v in tally[key]['counts']:
                        tally[key]['counts'][v] += 1
            else:
                if val in tally[key]['counts']:
                    tally[key]['counts'][val] += 1

    return render_template(
        'orders.html', orders=orders, menu=MENU, tally=tally
    )


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
