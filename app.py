from src.ui import build_app


if __name__ == "__main__":
    demo = build_app()
    demo.launch(server_name="0.0.0.0")
