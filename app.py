from flask import Flask, request, jsonify
from db import get_db_connection
from identity import identify_contact

app = Flask(__name__)

@app.route('/identify', methods=['POST'])
def identify():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    email = data.get('email')
    phone_number = data.get('phoneNumber')

    if not email and not phone_number:
        return jsonify({"error": "At least one of email or phoneNumber is required"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        result = identify_contact(conn, email, str(phone_number) if phone_number else None)
        return jsonify({"contact": result}), 200
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(debug=True, port=3000)
