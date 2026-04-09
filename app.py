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
            'Scrambled',
            'Over Easy',
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
            'Crispy Home Fries',
            'Hash Browns',
            'No Potatoes',
        ],
    },
    {
        'key': 'beans',
        'title': 'Beans',
        'subtitle': "Bean's beans (obviously)",
        'emoji': '\U0001FAD8',  # beans
        'type': 'single',
        'required': False,
        'options': [
            'Black Beans',
            'Pinto Beans',
            'Refried Beans',
            'No Beans',
        ],
    },
    {
        'key': 'veggies',
        'title': 'Fajita Veggies',
        'subtitle': 'Grilled peppers & onions',
        'emoji': '\U0001FAD1',  # bell pepper
        'type': 'single',
        'required': False,
        'options': ['Yes, add veggies', 'No veggies'],
    },
    {
        'key': 'salsa',
        'title': 'Salsas',
        'subtitle': 'Choose your spice level — pick as many as you dare',
        'emoji': '\U0001F336',  # hot pepper
        'type': 'multiple',
        'required': False,
        'options': [
            'Mild Pico de Gallo',
            'Roasted Corn Salsa',
            'Medium Tomatillo Green',
            'Hot Red Chili',
            'No Salsa',
        ],
    },
    {
        'key': 'cheese',
        'title': 'Cheese',
        'subtitle': 'Melty or shredded, the people decide',
        'emoji': '\U0001F9C0',  # cheese wedge
        'type': 'single',
        'required': False,
        'options': [
            'Shredded Cheese',
            'Queso Blanco (Melty)',
            'Both!',
            'No Cheese',
        ],
    },
    {
        'key': 'toppings',
        'title': 'Toppings',
        'subtitle': 'The finishing touches',
        'emoji': '\U0001F951',  # avocado
        'type': 'multiple',
        'required': False,
        'options': [
            'Sour Cream',
            'Guacamole',
            'Jalapeños',
            'Cilantro',
        ],
    },
    {
        'key': 'drink',
        'title': 'Drink',
        'subtitle': 'Quench thy thirst, adventurer',
        'emoji': '\u2615',  # hot beverage
        'type': 'single',
        'required': False,
        'options': [
            'Coffee',
            'Orange Juice',
            'Water',
            'Bringing my own',
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
            selections[key] = val or '—'
        else:
            vals = [v for v in request.form.getlist(key) if v]
            selections[key] = vals or ['—']

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
    return render_template(
        'confirmation.html', order=order, order_id=order_id, menu=MENU
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
