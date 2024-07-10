#!/usr/bin/env python3
from models import db, Restaurant, RestaurantPizza, Pizza
from flask_migrate import Migrate
from flask import Flask, request, make_response, jsonify
from flask_restful import Api, Resource
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

migrate = Migrate(app, db)

db.init_app(app)

api = Api(app)

@app.route("/")
def index():
    return "<h1>Code challenge</h1>"

@app.route("/restaurants", methods=['GET'])
def get_restaurants():
    restaurants = Restaurant.query.all()
    return jsonify([restaurant.to_dict(only=("address", "id", "name")) for restaurant in restaurants]), 200

@app.route('/restaurants/<int:id>', methods=['GET'])
def get_single_restaurant(id):
    restaurant = Restaurant.query.get(id)
    if not restaurant:
        return jsonify({"error": "Restaurant not found"}), 404
    return jsonify(restaurant.to_dict(only=("address", "id", "name", "restaurant_pizzas"))), 200

@app.route('/restaurants/<int:id>', methods=['DELETE'])
def delete_restaurant(id):
    restaurant = Restaurant.query.get(id)
    if not restaurant:
        return jsonify({"error": "Restaurant not found"}), 404

    RestaurantPizza.query.filter_by(restaurant_id=id).delete()
    db.session.delete(restaurant)
    db.session.commit()
    return '', 204

@app.route('/pizzas', methods=['GET'])
def get_pizzas():
    pizzas = Pizza.query.all()
    return jsonify([pizza.to_dict(only=("id", "ingredients", "name")) for pizza in pizzas]), 200

@app.route('/restaurant_pizzas', methods=['POST'])
def create_restaurant_pizza():
    data = request.get_json()
    
    if not all(key in data for key in ('price', 'pizza_id', 'restaurant_id')):
        return jsonify({"errors": ["Missing required fields"]}), 400
    
    price = data['price']
    pizza_id = data['pizza_id']
    restaurant_id = data['restaurant_id']
    
    if not isinstance(price, (int, float)) or price < 1 or price > 30:
        return jsonify({"errors": ["Price must be between 1 and 30"]}), 400
    
    pizza = Pizza.query.get(pizza_id)
    restaurant = Restaurant.query.get(restaurant_id)
    
    if not pizza or not restaurant:
        return jsonify({"errors": ["Pizza or Restaurant not found"]}), 404
    
    try:
        new_restaurant_pizza = RestaurantPizza(price=price, pizza_id=pizza_id, restaurant_id=restaurant_id)
        db.session.add(new_restaurant_pizza)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"errors": ["Failed to create RestaurantPizza", str(e)]}), 400
    
    response = {
        "id": new_restaurant_pizza.id,
        "pizza": pizza.to_dict(),
        "pizza_id": pizza_id,
        "price": price,
        "restaurant": restaurant.to_dict(),
        "restaurant_id": restaurant_id
    }
    
    return jsonify(response), 201

if __name__ == "__main__":
    app.run(port=5555, debug=True)