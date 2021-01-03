from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import psycopg2
from psycopg2.extras import DictCursor
import random

app = Flask(__name__)
CORS(app, resources={r"/*": { "origins": ["https://kanji-cloud.netlify.app", "http://localhost:8080"] }})

app.config['CORS_HEADERS'] = 'Content-Type'

CANVAS_SIZE = (400, 1200)
PADDING = 40
X_RANGE = (-CANVAS_SIZE[0]/2 + PADDING, CANVAS_SIZE[0]/2 - PADDING)
Y_RANGE = (-CANVAS_SIZE[1]/2 + PADDING, CANVAS_SIZE[1]/2 - PADDING)

def insert_vote(data):
    with psycopg2.connect(os.environ.get('DATABASE_URL')) as conn:
        if_exists = False
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM votes WHERE kanji = %s AND count > 0", (data["kanji"],))
            is_exists = bool(cur.fetchall())

        with conn.cursor() as cur:
            if is_exists:
                cur.execute(
                    "UPDATE votes SET count = count + 1 WHERE kanji = %s", (data["kanji"], )
                )
            else:
                cur.execute(
                    "INSERT INTO votes (kanji, count, x, y) VALUES(%s, %s, %s, %s)"
                    ,(data["kanji"], 1, data["x"], data["y"])
                )
        
        if data["prev_kanji"]:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM votes WHERE kanji = %s AND count > 0", (data["prev_kanji"],))
                is_exists = bool(cur.fetchall())
            if is_exists:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE votes SET count = count - 1 WHERE kanji = %s", (data["prev_kanji"], )
                    )

        conn.commit()


def get_all_votes():
    with psycopg2.connect(os.environ.get('DATABASE_URL')) as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("SELECT * FROM votes WHERE count > 0")
            votes = cur.fetchall()
            votes_list = []
            for vote in votes:
                votes_list.append(dict(vote))
    return votes_list


@app.route('/count', methods=['GET'])
def get_count():
    with psycopg2.connect(os.environ.get('DATABASE_URL')) as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("SELECT COALESCE(SUM(count), 0) AS count FROM votes")
            count = cur.fetchone()["count"]
    return jsonify({
        "message": "OK"
        ,"count": count
    })


@app.route('/', methods=['GET'])
def get():
    return jsonify({
        "message": "OK"
        ,"data": get_all_votes()
    })


@app.route('/', methods=['POST'])
def post():
    payload = request.json
    kanji = payload.get("kanji")
    prev_kanji = payload.get("prevKanji")

    # 乱数でを位置を決める    
    x = random.randint(*X_RANGE)
    y = random.randint(*Y_RANGE)

    data = {
        "kanji": kanji
        ,"prev_kanji": prev_kanji
        ,"x": x
        ,"y": y
    }
    insert_vote(data)

    app.logger.debug("INSERT\n", data)

    return jsonify({
        "message": "OK"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
