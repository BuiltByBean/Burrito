from flask import Flask, render_template, request, redirect, url_for
import json
import os
from datetime import datetime

app = Flask(__name__)

ORDERS_FILE = os.environ.get(
    'ORDERS_FILE',
    os.path.join(os.path.dirname(__file__), 'orders.json'),
)

# Menu sections — order matters, this is the flow guests walk through
MENU = [
    {
        'key': 'base',
        'title': 'Choose Your Vessel',
        'subtitle': 'The foundation of your feast',
        'type': 'single',
        'required': True,
        'options': [
            'Flour Tortilla (Burrito)',
            'Burrito Bowl (No Tortilla)',
            'Crispy Tacos',
            'Soft Tacos',
            'Quesadilla',
        ],
    },
    {
        'key': 'rice',
        'title': 'Rice',
        'subtitle': 'Grains of glory',
        'type': 'single',
        'required': False,
        'options': [
            'White Cilantro-Lime Rice',
            'Brown Cilantro-Lime Rice',
            'No Rice',
        ],
    },
    {
        'key': 'beans',
        'title': 'Beans',
        'subtitle': "Bean's beans (obviously)",
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
        'key': 'protein',
        'title': 'Protein',
        'subtitle': 'Pick your fighter (multi-select okay, meat lovers welcome)',
        'type': 'multiple',
        'required': True,
        'options': [
            'Grilled Chicken',
            'Steak',
            'Carnitas (Pulled Pork)',
            'Barbacoa (Shredded Beef)',
            'Sofritas (Spicy Tofu)',
            'No Meat',
        ],
    },
    {
        'key': 'veggies',
        'title': 'Fajita Veggies',
        'subtitle': 'Grilled peppers & onions',
        'type': 'single',
        'required': False,
        'options': ['Yes, add veggies', 'No veggies'],
    },
    {
        'key': 'salsa',
        'title': 'Salsas',
        'subtitle': 'Choose your spice level — pick as many as you dare',
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
        'subtitle': '',
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
        'type': 'multiple',
        'required': False,
        'options': [
            'Lettuce',
            'Sour Cream',
            'Guacamole',
            'Jalapeños',
            'Cilantro',
        ],
    },
    {
        'key': 'sides',
        'title': 'Sides',
        'subtitle': 'Because one burrito is never enough',
        'type': 'multiple',
        'required': False,
        'options': [
            'Tortilla Chips',
            'Chips & Guac',
            'Chips & Salsa',
            'No Sides',
        ],
    },
    {
        'key': 'drink',
        'title': 'Drink',
        'subtitle': 'Quench thy thirst, adventurer',
        'type': 'single',
        'required': False,
        'options': [
            'Water',
            'Soda',
            'Beer',
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
