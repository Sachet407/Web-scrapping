from flask import Flask, render_template, request, jsonify, Response, stream_with_context
import json
import time
from main import scrape_google_maps

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/scrape')
def scrape():
    keyword = request.args.get('keyword')
    total = int(request.args.get('total', 10))
    
    def generate():
        # Yield an initial message to confirm connection
        yield f"data: {json.dumps({'status': 'start', 'message': f'Starting scrape for {keyword}'})}\n\n"
        
        try:
            # Call the generator function from main.py
            for result in scrape_google_maps(keyword, total):
                yield f"data: {json.dumps({'status': 'data', 'data': result})}\n\n"
            
            yield f"data: {json.dumps({'status': 'complete', 'message': 'Scraping completed'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'status': 'error', 'message': str(e)})}\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
