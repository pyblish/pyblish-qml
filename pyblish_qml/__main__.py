import app

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="Python")
    parser.add_argument("--port", type=int, default=6000)

    kwargs = parser.parse_args()

    if kwargs.port is not 6000:
        app.run_production_app(kwargs.port)
    else:
        app.run_debug_app()
