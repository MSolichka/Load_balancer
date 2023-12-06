from flask import Flask, request, jsonify
from googletrans import Translator
import time
import threading
import psycopg2

app1 = Flask(__name__)
lock = threading.Lock()
busy_event = threading.Event()

def get_request_from_database():
    connection = None
    try:
        connection = psycopg2.connect(
            dbname='translator',
            user='postgres',
            password='Solomia04.',
            host='localhost',
            port=5432
        )
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, text FROM requests WHERE status='queued' ORDER BY id LIMIT 1 FOR UPDATE SKIP LOCKED;")
            row = cursor.fetchone()
            if row:
                request_id, text = row
                cursor.execute("UPDATE requests SET status='processing' WHERE id = %s;", (request_id,))
                connection.commit()
                return request_id, text
    except Exception as e:
        print(f"Error retrieving request from the database: {e}")
        return None
    finally:
        if connection:
            connection.close()

def translate_text(text, target_language='uk'):
    translator = Translator()
    translated_text = translator.translate(text, dest=target_language)
    return translated_text.text

def process_request(request_id, text, connection):
    with lock:
        busy_event.set()

    try:
        time.sleep(10)

        result = translate_text(text)

        # Оновлення статусу на 'completed' після успішного виконання
        with connection.cursor() as cursor:
            cursor.execute("UPDATE requests SET status='completed' WHERE id = %s;", (request_id,))
            connection.commit()

        return result
    except Exception as e:
        print(f"Error processing request: {e}")
        return None
    finally:
        with lock:
            busy_event.clear()

def handle_queue():
    while True:
        connection = None
        if not busy_event.is_set():
            request_info = get_request_from_database()
            if request_info:
                request_id, text_to_translate = request_info
                try:
                    connection = psycopg2.connect(
                        dbname='translator',
                        user='postgres',
                        password='Solomia04.',
                        host='localhost',
                        port=5432
                    )
                    process_request(request_id, text_to_translate, connection)
                finally:
                    if connection:
                        connection.close()
        time.sleep(1)

@app1.route('/check_availability', methods=['GET'])
def check_availability():
    return {'available': not busy_event.is_set()}

@app1.route('/translate', methods=['POST'])
def translate():
    if busy_event.is_set():
        return {'status': 'queued'}
   
    data = request.get_json()
    text_to_translate = data.get('text')
    request_id = data.get('request_id')

    connection = None
    try:
        connection = psycopg2.connect(
            dbname='translator',
            user='postgres',
            password='Solomia04.',
            host='localhost',
            port=5432
        )
        response = process_request(request_id, text_to_translate, connection)
    finally:
        if connection:
            connection.close()

    return {'translated_text': response}

if __name__ == '__main__':
    threading.Thread(target=handle_queue, daemon=True).start()
    print("Starting the Flask app for server1...")
    app1.run(port=5001, debug=True)
    print("Flask app for server1 started.")
