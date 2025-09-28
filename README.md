# Mini FP&A Assistant

**Mini FP&A Assistant** is a lightweight financial planning & analysis tool that allows finance teams or business users to quickly analyze key metrics such as revenue, gross margin, opex, EBITDA, and cash runway. Built in Python, it leverages Excel inputs and provides visualizations for decision-making.

---

## Features

- **Revenue vs Budget Analysis**  
  Compare actual revenue vs budgeted revenue for any month, in USD.

- **Gross Margin Trend**  
  Track gross margin percentage trends over a specified number of months.

- **Opex Breakdown**  
  Breakdown operating expenses by account category for any month.

- **EBITDA Proxy**  
  Quickly calculate EBITDA using revenue, COGS, and operating expenses.

- **Cash Runway Estimation**  
  Estimate cash runway in months based on average net burn over the last 3 months.

- **Charts & Visualizations**  
  Generate charts for gross margin trends and revenue vs budget comparisons.

---

## Project Structure
FP&A/
├── agent/
│   ├── tools.py        # Core FP&A logic and data handling
│   └── planner.py      # Optional planning & reporting scripts
├── fixtures/
│   └── data.xlsx       # Sample input data
├── tests/
│   └── test_tools.py   # Unit tests for tools.py
├── app.py              # Main application entry point
├── README.md
└── requirements.txt    # Python dependencies


---

## Installation

1. Clone the repository:

```bash
git clone https://github.com/Southen16/Mini-FP-A-Assistant.git
cd Mini-FP-A-Assistant

(Optional) Create a virtual environment:

python3 -m venv venv
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

3.	Install dependencies:

pip install -r requirements.txt


Usage
	1.	Place your financial Excel file in the fixtures/ folder (or update the path in app.py).
	2.	Run the app:

  python app.py

  	3.	Ask finance questions, for example:

	•	What was June 2025 revenue vs budget in USD?
	•	Show Gross Margin % trend for the last 3 months.
	•	Break down Opex by category for June 2025.
	•	What is our cash runway right now?
Dependencies
	•	pandas
	•	numpy
	•	matplotlib
	•	python-dateutil

Install via:pip install pandas numpy matplotlib python-dateutil

Contributing
	1.	Fork the repository.
	2.	Create your feature branch: git checkout -b feature-name
	3.	Commit your changes: git commit -m "Add feature"
	4.	Push to branch: git push origin feature-name
	5.	Open a Pull Request.

⸻

License

This project is licensed under the MIT License.
Author

Southen Kumar Nama
