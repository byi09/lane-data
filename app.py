from flask import Flask, jsonify, request, render_template
import mysql.connector
import json
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static', template_folder='templates')

# Database connection parameters
DB_HOST = os.environ.get('DB_HOST')
DB_NAME = os.environ.get('DB_NAME')
DB_USER = os.environ.get('DB_USERNAME')
DB_PASS = os.environ.get('DB_PASSWORD')
DB_PORT = os.environ.get('DB_PORT', '3306')

def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            port=DB_PORT
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/lanes', methods=['GET'])
def get_lanes():
    try:
        type_names = request.args.get('type_names')
        semantic_description = request.args.get('semantic_description')
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        sql = """
            SELECT
                id,
                type_names,
                semantic_description,
                ST_AsGeoJSON(geometry) AS geometry_geojson
            FROM lanes
            WHERE 1=1
        """
        params = []
        
        if type_names:
            sql += " AND type_names = %s"
            params.append(type_names)
            
            if type_names == 'Lane Nominal' and semantic_description:
                sql += " AND semantic_description = %s"
                params.append(semantic_description)
        
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        
        features = []
        for row in rows:
            if row['geometry_geojson']:
                properties = {
                    'id': row['id'],
                    'type_names': row['type_names'],
                    'semantic_description': row['semantic_description']
                }
                geometry = json.loads(row['geometry_geojson'])
                features.append({
                    "type": "Feature",
                    "geometry": geometry,
                    "properties": properties
                })
        
        geojson = {
            "type": "FeatureCollection",
            "features": features
        }
        
        return jsonify(geojson)
    
    except mysql.connector.Error as err:
        logger.error(f"Database error: {err}")
        return jsonify({'error': str(err)}), 500
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return jsonify({'error': 'An unexpected error occurred'}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)