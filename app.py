# backend/app.py
import os
from flask import Flask, jsonify, request, abort
from flask_cors import CORS
import pandas as pd

app = Flask(__name__)
CORS(app)

# Determine dataset path relative to this file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, '..', 'dataset', '608publications.csv')

# Load CSV into DataFrame once on startup
if not os.path.exists(DATA_PATH):
    raise FileNotFoundError(f"Dataset not found at {DATA_PATH}. Place 608publications.csv in ../dataset/")
df = pd.read_csv(DATA_PATH, dtype=str, encoding='latin1').fillna('')



# convert to list of dicts for stable ordering/ids
records = df.to_dict(orient='records')

# add index id to each record (so frontend can request /api/publications/<id>)
for i, r in enumerate(records):
    r['_id'] = i

@app.route('/')
def home():
    return jsonify({"message": "Welcome to BioSpace Explorer API!"})
@app.route('/api/experiments')
def get_experiments():
    data = df.to_dict(orient='records')
    return jsonify(data)

@app.route('/api/publications', methods=['GET'])
def get_publications():
    """
    Query params:
      q - search string (title or summary)
      category - filter by Category (exact or comma-separated)
      organism - filter by Organism (substring)
      impact - filter by Impact (substring)
      offset - pagination offset (int)
      limit - pagination limit (int)
      sort_by - column name to sort by (Title, Impact)
    """
    q = request.args.get('q', '').strip().lower()
    category = request.args.get('category', '').strip().lower()
    organism = request.args.get('organism', '').strip().lower()
    impact = request.args.get('impact', '').strip().lower()
    offset = int(request.args.get('offset', 0))
    limit = int(request.args.get('limit', 50))
    sort_by = request.args.get('sort_by', '')

    filtered = records

    # textual search on title and summary
    if q:
        filtered = [r for r in filtered if q in (r.get('Title','').lower() + ' ' + r.get('Summary','').lower())]

    if category:
        # allow multiple categories separated by comma
        cats = [c.strip() for c in category.split(',') if c.strip()]
        filtered = [r for r in filtered if any(c in r.get('Category','').lower() for c in cats)]

    if organism:
        filtered = [r for r in filtered if organism in r.get('Organism','').lower()]

    if impact:
        filtered = [r for r in filtered if impact in r.get('Impact','').lower()]

    total = len(filtered)

    # sort if requested
    if sort_by:
        filtered = sorted(filtered, key=lambda x: x.get(sort_by, '').lower())

    # pagination
    sliced = filtered[offset: offset + limit]

    return jsonify({
        "total": total,
        "offset": offset,
        "limit": limit,
        "results": sliced
    })

@app.route('/api/publications/<int:pub_id>', methods=['GET'])
def get_publication(pub_id):
    if pub_id < 0 or pub_id >= len(records):
        abort(404)
    return jsonify(records[pub_id])

@app.route('/api/publications/stats', methods=['GET'])
def publications_stats():
    df_local = pd.DataFrame(records)
    # basic aggregations
    by_category = df_local['Category'].value_counts().to_dict()
    by_organism = df_local['Organism'].value_counts().to_dict()
    by_impact = df_local['Impact'].value_counts().to_dict()
    return jsonify({
        "by_category": by_category,
        "by_organism": by_organism,
        "by_impact": by_impact,
        "total_publications": len(records)
    })

if __name__ == '__main__':
    app.run(debug=True)
