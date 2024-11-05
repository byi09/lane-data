from flask import Flask, jsonify, request, render_template
import mysql.connector
import json
import os
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Verify template directory exists
template_dir = Path(__file__).parent / 'templates'
static_dir = Path(__file__).parent / 'static'

app = Flask(__name__, 
           template_folder=str(template_dir),
           static_folder=str(static_dir))

# Database configuration with validation
def get_db_config():
    required_vars = ['DB_HOST', 'DB_NAME', 'DB_USERNAME', 'DB_PASSWORD']
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    return {
        'host': os.environ['DB_HOST'],
        'database': os.environ['DB_NAME'],
        'user': os.environ['DB_USERNAME'],
        'password': os.environ['DB_PASSWORD'],
        'port': os.environ.get('DB_PORT', '3306')
    }

def get_db_connection():
    try:
        config = get_db_config()
        logger.info(f"Connecting to database at {config['host']}:{config['port']}")
        return mysql.connector.connect(**config)
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        raise

@app.route('/')
def index():
    try:
        logger.info(f"Template folder path: {app.template_folder}")
        logger.info(f"Templates available: {os.listdir(app.template_folder)}")
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error rendering index: {str(e)}")
        return f"Error: {str(e)}", 500

@app.route('/api/lanes', methods=['GET'])
def get_lanes():
    conn = None
    cursor = None
    try:
        type_names = request.args.get('type_names')
        semantic_description = request.args.get('semantic_description')
        
        logger.info(f"Received request - type_names: {type_names}, semantic_description: {semantic_description}")
        
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
        
        logger.info(f"Executing query: {sql} with params: {params}")
        
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        
        features = []
        for row in rows:
            if row['geometry_geojson']:
                try:
                    geometry = json.loads(row['geometry_geojson'])
                    properties = {
                        'id': row['id'],
                        'type_names': row['type_names'],
                        'semantic_description': row['semantic_description']
                    }
                    features.append({
                        "type": "Feature",
                        "geometry": geometry,
                        "properties": properties
                    })
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid GeoJSON for row {row['id']}: {str(e)}")
                    continue
        
        response = {
            "type": "FeatureCollection",
            "features": features
        }
        
        logger.info(f"Returning {len(features)} features")
        return jsonify(response)
        
    except mysql.connector.Error as e:
        logger.error(f"Database error: {str(e)}")
        return jsonify({'error': 'Database error', 'details': str(e)}), 500
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({'error': 'Unexpected error', 'details': str(e)}), 500
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
