from datetime import datetime
import sqlite3
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI(title="Mobile Utility Suite")

# --- DATABASE SETUP ---
DB_FILE = "history.db"


def init_db():
  conn = sqlite3.connect(DB_FILE)
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS calculations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            expression TEXT,
            result TEXT,
            timestamp TEXT
        )
    """)
  conn.commit()
  conn.close()


init_db()


def log_calculation(category: str, expression: str, result: str):
  conn = sqlite3.connect(DB_FILE)
  cursor = conn.cursor()
  cursor.execute(
      "INSERT INTO calculations (category, expression, result, timestamp) VALUES"
      " (?, ?, ?, ?)",
      (category, expression, result, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
  )
  conn.commit()
  conn.close()


# --- HTML FRONTEND (Embedded for Mobile Ease) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mobile Utility Suite</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f4f4f9; color: #333; margin: 0; padding: 15px; }
        .container { max-width: 400px; margin: auto; background: #fff; padding: 20px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
        h2 { text-align: center; color: #4f46e5; }
        .section { margin-bottom: 20px; padding-bottom: 15px; border-bottom: 1px solid #eee; }
        label { display: block; margin-top: 8px; font-weight: bold; font-size: 14px; }
        input, select { width: 100%; padding: 8px; margin-top: 4px; box-sizing: border-box; border: 1px solid #ccc; border-radius: 5px; }
        button { width: 100%; background: #4f46e5; color: white; border: none; padding: 10px; margin-top: 10px; border-radius: 5px; font-size: 16px; cursor: pointer; }
        button:hover { background: #4338ca; }
        .result { margin-top: 10px; font-weight: bold; color: #16a34a; text-align: center; }
    </style>
</head>
<body>
<div class="container">
    <h2>Utility Suite</h2>

    <!-- Calculator -->
    <div class="section">
        <h3>Simple Calculator</h3>
        <form action="/calculate" method="post">
            <input type="hidden" name="action_type" value="calc">
            <label>First Number:</label>
            <input type="number" step="any" name="num1" required>
            <label>Operation:</label>
            <select name="op">
                <option value="add">+</option>
                <option value="sub">-</option>
                <option value="mul">*</option>
                <option value="div">/</option>
            </select>
            <label>Second Number:</label>
            <input type="number" step="any" name="num2" required>
            <button type="submit">Calculate</button>
        </form>
    </div>

    <!-- Weight Converter -->
    <div class="section">
        <h3>Weight Converter</h3>
        <form action="/calculate" method="post">
            <input type="hidden" name="action_type" value="weight">
            <label>Value:</label>
            <input type="number" step="any" name="val" required>
            <label>Conversion:</label>
            <select name="w_dir">
                <option value="kg_to_lbs">Kg to Lbs</option>
                <option value="lbs_to_kg">Lbs to Kg</option>
            </select>
            <button type="submit">Convert Weight</button>
        </form>
    </div>

    <!-- Temperature Converter -->
    <div class="section">
        <h3>Temperature Converter</h3>
        <form action="/calculate" method="post">
            <input type="hidden" name="action_type" value="temp">
            <label>Value:</label>
            <input type="number" step="any" name="val" required>
            <label>Conversion:</label>
            <select name="t_dir">
                <option value="c_to_f">Celsius to Fahrenheit</option>
                <option value="f_to_c">Fahrenheit to Celsius</option>
            </select>
            <button type="submit">Convert Temp</button>
        </form>
    </div>

    {% if result %}
    <div class="result">
        Result: {{ result }}
    </div>
    {% endif %}
</div>
</body>
</html>
"""

# Simple template rendering helper without needing external Jinja file files
from fastapi.templating import Jinja2Templates  # If using jinja, or string replace:
# To keep it ultra-simple for a single file on mobile without extra setup, we can use string formatting or Jinja.
# Let's use clean Jinja rendering or simple HTML response substitution.


@app.get("/", response_class=HTMLResponse)
def home():
  # Render basic page without result initially
  rendered = HTML_TEMPLATE.replace("{% if result %}", "<!--").replace(
      "{% endif %}", "-->"
  )
  return rendered


@app.post("/calculate", response_class=HTMLResponse)
def handle_calculation(
    action_type: str = Form(...),
    num1: float = Form(None),
    num2: float = Form(None),
    op: str = Form(None),
    val: float = Form(None),
    w_dir: str = Form(None),
    t_dir: str = Form(None),
):
  result_str = ""
  category = ""

  if action_type == "calc":
    category = "Calculator"
    if op == "add":
      res = num1 + num2
    elif op == "sub":
      res = num1 - num2
    elif op == "mul":
      res = num1 * num2
    elif op == "div":
      if num2 == 0:
        raise HTTPException(
            status_code=400, detail="Division by zero not allowed"
        )
      res = num1 / num2
    expression = f"{num1} {op} {num2}"
    result_str = f"{res}"

  elif action_type == "weight":
    category = "Weight"
    if w_dir == "kg_to_lbs":
      res = val * 2.20462
      expression = f"{val} kg"
      result_str = f"{res:.2f} lbs"
    else:
      res = val / 2.20462
      expression = f"{val} lbs"
      result_str = f"{res:.2f} kg"

  elif action_type == "temp":
    category = "Temperature"
    if t_dir == "c_to_f":
      res = (val * 9 / 5) + 32
      expression = f"{val} °C"
      result_str = f"{res:.2f} °F"
    else:
      res = (val - 32) * 5 / 9
      expression = f"{val} °F"
      result_str = f"{res:.2f} °C"

  # Log to SQLite
  log_calculation(category, expression, result_str)

  # Inject result into HTML template
  response_html = (
      HTML_TEMPLATE.replace("{% if result %}", "")
      .replace("{% endif %}", "")
      .replace("{{ result }}", f"{expression} = {result_str}")
  )
  return response_html


# Embedded runner for single-tap execution on mobile IDE
if __name__ == "__main__":
  uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)