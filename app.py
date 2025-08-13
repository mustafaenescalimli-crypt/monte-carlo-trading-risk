from flask import Flask, render_template, request
import io
import base64
import matplotlib.pyplot as plt
import numpy as np

app = Flask(__name__)

def max_drawdown(equity_curve):
    peak = equity_curve[0]
    max_dd = 0
    for x in equity_curve:
        if x > peak:
            peak = x
        dd = peak - x
        if dd > max_dd:
            max_dd = dd
    return max_dd

def max_loss_streak(trades):
    max_streak = 0
    current_streak = 0
    for t in trades:
        if t < 0:
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 0
    return max_streak

def monte_carlo_simulation(wr, rr, n_trades, n_sim=10000):
    max_dds = []
    max_streaks = []
    total_profits = []
    avg_winners = []
    avg_losers = []

    for _ in range(n_sim):
        trades = np.random.choice([rr, -1], size=n_trades, p=[wr, 1 - wr])
        equity_curve = np.cumsum(trades)

        max_dds.append(max_drawdown(equity_curve))
        max_streaks.append(max_loss_streak(trades))
        total_profits.append(equity_curve[-1])

        winners = trades[trades > 0]
        losers = trades[trades < 0]
        avg_winners.append(np.mean(winners) if len(winners) > 0 else 0)
        avg_losers.append(np.mean(losers) if len(losers) > 0 else 0)

    return {
        "max_dds": np.array(max_dds),
        "max_streaks": np.array(max_streaks),
        "total_profits": np.array(total_profits),
        "avg_winners": np.array(avg_winners),
        "avg_losers": np.array(avg_losers)
    }

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    plot_url = None

    if request.method == 'POST':
        wr_pct = float(request.form['wr'])
        wr = wr_pct / 100
        rr = float(request.form['rr'])
        n_trades = int(request.form['n_trades'])
        n_sim = int(request.form['n_sim'])
        max_dd_limit_pct = float(request.form['max_dd_limit'])
        max_dd_limit = max_dd_limit_pct / 100

        results = monte_carlo_simulation(wr, rr, n_trades, n_sim)
        max_dds = results["max_dds"]

        perc95_max_dd = np.percentile(max_dds, 95)
        max_dd_max = np.max(max_dds)
        risk_suggestion = max_dd_limit / perc95_max_dd
        risk_suggestion_worst = max_dd_limit / max_dd_max

        result = {
            "perc95_max_dd": perc95_max_dd,
            "max_dd_max": max_dd_max,
            "risk_suggestion": risk_suggestion * 100,
            "risk_suggestion_worst": risk_suggestion_worst * 100,
        }

        plt.figure(figsize=(6,4))
        plt.hist(max_dds, bins=50, alpha=0.7, color='red')
        plt.title("Max Drawdown Histogram")
        plt.xlabel("Max Drawdown (R)")
        plt.ylabel("Frequency")

        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode()

    return render_template('index.html', result=result, plot_url=plot_url)

if __name__ == '__main__':
    app.run(debug=True)
