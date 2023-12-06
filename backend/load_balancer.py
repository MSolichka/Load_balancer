from flask import Flask, request, jsonify
import requests
import psycopg2
import traceback
from flask_cors import CORS

app = Flask(__name__)
server1_url = "http://localhost:5001"
server2_url = "http://localhost:5002"
CORS(app)

def store_request_in_database(text):
    try:
        connection = psycopg2.connect(
            dbname='translator',
            user='postgres',
            password='Solomia04.',
            host='localhost',
            port=5432
        )
        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO requests (text, status) VALUES (%s, 'queued') RETURNING id;", (text,))
            request_id = cursor.fetchone()[0]
            print(f"Request stored in the database. Request ID: {request_id}")
            connection.commit()
            return request_id
    except Exception as e:
        print(f"Error storing request in the database: {e}")
        print(traceback.format_exc())
        return None
    finally:
        if connection:
            connection.close()

def check_server_availability(server_url):
    try:
        response = requests.get(f"{server_url}/check_availability")
        return response.json().get('available', False)
    except requests.RequestException as e:
        print(f"Error checking server availability: {e}")
        return False

def load_balancer(text):
    request_id = store_request_in_database(text)

    for server_url in [server1_url, server2_url]:
        if check_server_availability(server_url):
            print(f"Selected {server_url} for '{text}'")
            return server_url, request_id

    print(f"Both servers busy. Added '{text}' to the translation queue with request_id: {request_id}")
    return None, request_id

@app.route('/translate', methods=['POST'])
def translate():
    data = request.get_json()
    text_to_translate = data.get('text')

    selected_server, request_id = load_balancer(text_to_translate)

    if selected_server:
        try:
            response = requests.post(selected_server + "/translate", json={'text': text_to_translate, 'request_id': request_id})
            return jsonify(response.json())
        except requests.RequestException as e:
            # Handle network or server errors
            print(f"Error communicating with server: {e}")
            return jsonify({'status': 'error', 'error_message': str(e)})
    else:
        print(f"Both servers busy. Request '{text_to_translate}' queued with request_id: {request_id}")
        return jsonify({'status': 'queued', 'request_id': request_id})

if __name__ == '__main__':
    app.run(port=5000, debug=True)
