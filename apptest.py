from flask import Flask, render_template_string
import pandas as pd

app = Flask(__name__)

@app.route("/")
def elo_table():
    df = pd.read_csv('elo_rankings_2025_2026.csv')
    html_table = df.to_html(index=False, classes='elo-table')

    return render_template_string(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>College Hockey Elo Rankings</title>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 2em; }}
            h1 {{ text-align: center; }}
            .elo-table {{
                width: 60%;
                margin: auto;
                border-collapse: collapse;
            }}
            .elo-table th, .elo-table td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: center;
            }}
            .elo-table th {{
                background-color: #f2f2f2;
            }}
        </style>
    </head>
    <body>
        <h1>College Hockey Elo Rankings</h1>
        {html_table}
    </body>
    </html>
    """)

if __name__ == "__main__":
    app.run(debug=True)