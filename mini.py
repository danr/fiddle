from flask import Flask, jsonify
from datetime import datetime

start = datetime.now()

def main():
    app = Flask(__name__)
    @app.route('/')
    def root():
        return jsonify(
            start=start.isoformat(),
            now=datetime.now().isoformat(),
            z=2,
        )
    app.run(port=5001)

if __name__ == '__main__':
    main()
