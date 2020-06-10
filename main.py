from flask import Flask
from views import blueprints



def create_app():

    app = Flask(__name__)
    app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024

    for bp in blueprints:
        app.register_blueprint(bp)
        bp.app = app

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, use_reloader=False)
