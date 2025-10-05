# backend/app.py
import os
from flask import Flask, jsonify, request, abort
from flask_cors import CORS
import pandas as pd

app = Flask(__name__)
CORS(app)

# Determine dataset path relative to this file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, 'dataset', '608publications.csv')

# Load CSV into DataFrame once on startup
if not os.path.exists(DATA_PATH):
    raise FileNotFoundError(
        f"Dataset not found at {DATA_PATH}. Place 608publications.csv in backend/dataset/"
    )

df = pd.read_csv(DATA_PATH, dtype=str, encoding='latin1').fillna('')

# Convert to list of dicts and add index id
records = df.to_dict(orient='records')
for i, r in enumerate(records):
    r['_id'] = i

# Home route
@app.route('/')
def home():
    return jsonify({"message": "Welcome to BioSpace Explorer API!"})

# All experiments route
@app.route('/api/experiments')
def get_experiments():
    data = df.to_dict(orient='records')
    return jsonify(data)

# Publications route with filters and pagination
@app.route('/api/publications', methods=['GET'])
def get_publications():
    q = request.args.get('q', '').strip().lower()
    category = request.args.get('category', '').strip().lower()
    organism = request.args.get('organism', '').strip().lower()
    impact = request.args.get('impact', '').strip().lower()
    offset = int(request.args.get('offset', 0))
    limit = int(request.args.get('limit', 50))
    sort_by = request.args.get('sort_by', '')

    filtered = records

    if q:
        filtered = [
            r for r in filtered
            if q in (r.get('Title','').lower() + ' ' + r.get('Summary','').lower())
        ]

    if category:
        cats = [c.strip() for c in category.split(',') if c.strip()]
        filtered = [r for r in filtered if any(c in r.get('Category','').lower() for c in cats)]

    if organism:
        filtered = [r for r in filtered if organism in r.get('Organism','').lower()]

    if impact:
        filtered = [r for r in filtered if impact in r.get('Impact','').lower()]

    total = len(filtered)

    if sort_by:
        filtered = sorted(filtered, key=lambda x: x.get(sort_by, '').lower())

    sliced = filtered[offset: offset + limit]

    return jsonify({
        "total": total,
        "offset": offset,
        "limit": limit,
        "results": sliced
    })

# Single publication by ID
@app.route('/api/publications/<int:pub_id>', methods=['GET'])
def get_publication(pub_id):
    if pub_id < 0 or pub_id >= len(records):
        abort(404)
    return jsonify(records[pub_id])

# Basic stats route
@app.route('/api/publications/stats', methods=['GET'])
def publications_stats():
    df_local = pd.DataFrame(records)
    by_category = df_local['Category'].value_counts().to_dict()
    by_organism = df_local['Organism'].value_counts().to_dict()
    by_impact = df_local['Impact'].value_counts().to_dict()
    return jsonify({
        "by_category": by_category,
        "by_organism": by_organism,
        "by_impact": by_impact,
        "total_publications": len(records)
    })

# Run app
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
