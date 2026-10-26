from flask import Flask, render_template, request, jsonify

app = Flask(__name__)


def trimf(x, a, b, c):
    if x <= a or x >= c:
        return 1.0 if x == b else 0.0
    if x == b:
        return 1.0
    return (x - a) / (b - a) if x < b else (c - x) / (c - b)


def trapmf(x, a, b, c, d):
    if b <= x <= c:
        return 1.0
    if x < a or x > d:
        return 0.0
    if x < b:
        return (x - a) / (b - a) if b != a else 1.0
    return (d - x) / (d - c) if d != c else 1.0


class FuzzySet:
    def __init__(self, name, kind, params):
        self.name = name
        self.kind = kind
        self.params = params

    def mu(self, x):
        return trimf(x, *self.params) if self.kind == "tri" else trapmf(x, *self.params)


class LinguisticVariable:
    def __init__(self, name, unit, lo, hi, sets):
        self.name = name
        self.unit = unit
        self.lo = lo
        self.hi = hi
        self.sets = {s.name: s for s in sets}

    def fuzzify(self, x):
        return {n: s.mu(x) for n, s in self.sets.items()}


TEMPERATURE = LinguisticVariable("Temperature", "°C", 0, 50, [
    FuzzySet("Cold", "trap", (0, 0, 10, 20)),
    FuzzySet("Warm", "tri", (15, 25, 35)),
    FuzzySet("Hot", "trap", (30, 40, 50, 50)),
])

HUMIDITY = LinguisticVariable("Humidity", "%", 0, 100, [
    FuzzySet("Low", "trap", (0, 0, 20, 40)),
    FuzzySet("Medium", "tri", (30, 50, 70)),
    FuzzySet("High", "trap", (60, 80, 100, 100)),
])

FAN_SPEED = LinguisticVariable("Fan Speed", "%", 0, 100, [
    FuzzySet("Slow", "trap", (0, 0, 20, 40)),
    FuzzySet("Medium", "tri", (30, 50, 70)),
    FuzzySet("Fast", "trap", (60, 80, 100, 100)),
])

RULES = [
    ("Cold", "Low", "Slow"),
    ("Cold", "Medium", "Slow"),
    ("Cold", "High", "Medium"),
    ("Warm", "Low", "Slow"),
    ("Warm", "Medium", "Medium"),
    ("Warm", "High", "Fast"),
    ("Hot", "Low", "Medium"),
    ("Hot", "Medium", "Fast"),
    ("Hot", "High", "Fast"),
]


def rule_text(rule):
    return f"IF Temperature is {rule[0]} AND Humidity is {rule[1]} THEN Fan is {rule[2]}"


def infer(temp, hum, step=0.5):
    t_mu = TEMPERATURE.fuzzify(temp)
    h_mu = HUMIDITY.fuzzify(hum)

    fired = []
    out_strength = {n: 0.0 for n in FAN_SPEED.sets}

    for i, (t, h, f) in enumerate(RULES, 1):
        strength = min(t_mu[t], h_mu[h])
        fired.append({
            "id": i,
            "text": rule_text((t, h, f)),
            "strength": strength,
            "fan": f,
            "fired": strength > 0,
        })
        out_strength[f] = max(out_strength[f], strength)

    xs = []
    agg = []
    x = FAN_SPEED.lo
    while x <= FAN_SPEED.hi + 1e-9:
        mu = max(
            min(out_strength[n], s.mu(x))
            for n, s in FAN_SPEED.sets.items()
        )
        xs.append(round(x, 2))
        agg.append(mu)
        x += step

    area = sum(agg)
    crisp = sum(x * m for x, m in zip(xs, agg)) / area if area > 0 else 0.0

    return {
        "temperature": temp,
        "humidity": hum,
        "temperature_membership": t_mu,
        "humidity_membership": h_mu,
        "rules": fired,
        "output_strength": out_strength,
        "fan_speed": crisp,
        "fan_label": "Slow" if crisp < 40 else ("Medium" if crisp < 70 else "Fast"),
        "aggregation_x": xs,
        "aggregation_y": agg,
    }


@app.route("/")
def home():
    return render_template("index.html")


@app.post("/predict")
def predict():
    try:
        data = request.get_json(force=True)
        temp = float(data.get("temperature"))
        hum = float(data.get("humidity"))

        if not 0 <= temp <= 50:
            return jsonify({"error": "Temperature must be between 0 and 50 °C."}), 400
        if not 0 <= hum <= 100:
            return jsonify({"error": "Humidity must be between 0 and 100 %."}), 400

        return jsonify(infer(temp, hum))
    except (TypeError, ValueError):
        return jsonify({"error": "Please enter valid numeric values."}), 400


if __name__ == "__main__":
    app.run(debug=True)
