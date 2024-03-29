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
    print(data, file=open("./tmp.log", "a"))
    with psycopg2.connect(os.environ.get('DATABASE_URL')) as conn:
        is_exists = False
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM votes WHERE kanji = %s", (data["kanji"],))
            is_exists = bool(cur.fetchall())

        with conn.cursor() as cur:
            if is_exists:
                cur.execute(
                    "UPDATE votes SET count = count + 1 WHERE kanji = %s", (data["kanji"], )
                )
            else:
                # 乱数でを位置を決める    
                data["x"] = random.randint(*X_RANGE)
                data["y"] = random.randint(*Y_RANGE)
                cur.execute(
                    "INSERT INTO votes (kanji, count, x, y) VALUES(%s, %s, %s, %s)"
                    ,(data["kanji"], 1, data["x"], data["y"])
                )
        
        if data["prev_kanji"]:
            is_exists = False
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM votes WHERE kanji = %s AND count > 0", (data["prev_kanji"],))
                is_exists = bool(cur.fetchall())
            if is_exists:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE votes SET count = count - 1 WHERE kanji = %s", (data["prev_kanji"], )
                    )

        conn.commit()
        return True


def get_all_votes():
    with psycopg2.connect(os.environ.get('DATABASE_URL')) as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("SELECT * FROM votes WHERE count > 0")
            votes = cur.fetchall()
            votes_list = []
            for vote in votes:
                votes_list.append(dict(vote))
    return votes_list

def delete_all_votes():
    with psycopg2.connect(os.environ.get('DATABASE_URL')) as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("DELETE FROM votes")
    return

def get_all_texts():
    with psycopg2.connect(os.environ.get('DATABASE_URL')) as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("SELECT * FROM fixed_texts")
            texts = cur.fetchall()
            texts_dict = dict()
            for text in texts:
                texts_dict[text["key"]] = text["fixed_text"]
    return texts_dict

def edit_texts(texts):
    with psycopg2.connect(os.environ.get('DATABASE_URL')) as conn:
        for key, text in texts.items():
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE fixed_texts SET fixed_text = %s WHERE key = %s", (text, key)
                )
        conn.commit()
    return


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

    data = {
        "kanji": kanji
        ,"prev_kanji": prev_kanji
    }
    if not insert_vote(data):
        return jsonify({
            "message": "invalid data"
        }), 400

    return jsonify({
        "message": "OK"
    })

@app.route('/kanjis', methods=['POST'])
def delete():
    payload = request.json
    if not payload:
        return jsonify({
            "message": "parameters are needed"
        }), 400
    is_delete = payload.get("delete")

    if is_delete == 1:
        delete_all_votes()
    else:
        return jsonify({
            "message": "invalid parameter"
        }), 400

    return jsonify({
        "message": "OK"
    })

@app.route('/texts', methods=['GET'])
def get_texts():
    return jsonify({
        "message": "OK"
        ,"texts": get_all_texts()
    })

@app.route('/texts', methods=['POST'])
def post_texts():
    payload = request.json
    edit_texts(payload)

    return jsonify({
        "message": "OK"
        ,"texts": get_all_texts()
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)