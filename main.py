from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
import pandas as pd
import json
import os

# ------------------------------
# FastAPI App
# ------------------------------
app = FastAPI(title="Hospital Dashboard App")

# ------------------------------
# File paths (Docker / Render safe)
# ------------------------------
BASE_DIR = os.path.dirname(__file__)
CSV_PATH = os.path.join(BASE_DIR, "hospital_data.csv")

# Global dataframe (loaded at startup)
df = None

# ------------------------------
# Load CSV safely AFTER app starts
# ------------------------------
@app.on_event("startup")
def load_csv_data():
    global df
    if not os.path.exists(CSV_PATH):
        raise RuntimeError(f"CSV file not found: {CSV_PATH}")
    df = pd.read_csv(CSV_PATH)

# ------------------------------
# Health check / Home
# ------------------------------
@app.get("/")
def home():
    return {"message": "Hospital API is running"}

# ------------------------------
# Dashboard endpoint
# ------------------------------
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(page: int = 1, per_page: int = 50):

    if df is None:
        return HTMLResponse("<h3>Data not loaded</h3>", status_code=500)

    # Pagination
    start = (page - 1) * per_page
    end = start + per_page
    subset = df.iloc[start:end]

    # Dropdown filter options
    insurance_providers = df['Insurance Provider'].dropna().unique().tolist() if 'Insurance Provider' in df.columns else []
    conditions = df['Medical Condition'].dropna().unique().tolist() if 'Medical Condition' in df.columns else []
    years = df['Admission Year'].dropna().unique().tolist() if 'Admission Year' in df.columns else []

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Hospital Dashboard</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body {{ padding: 20px; background-color: #f8f9fa; }}
            th {{ cursor: pointer; }}
            .filter-box {{ margin-bottom: 15px; }}
            h2 {{ margin-bottom: 30px; color: #0d6efd; }}
            #hospitalTable {{ background-color: #fff; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Hospital Dashboard</h2>

            <div class="row filter-box">
                <div class="col-md-3"><input id="searchInput" class="form-control" placeholder="Search"></div>
                <div class="col-md-3">
                    <select id="insuranceFilter" class="form-select">
                        <option value="">All Insurance Providers</option>
                        {"".join([f'<option value="{ip}">{ip}</option>' for ip in insurance_providers])}
                    </select>
                </div>
                <div class="col-md-3">
                    <select id="conditionFilter" class="form-select">
                        <option value="">All Conditions</option>
                        {"".join([f'<option value="{c}">{c}</option>' for c in conditions])}
                    </select>
                </div>
                <div class="col-md-3">
                    <select id="yearFilter" class="form-select">
                        <option value="">All Years</option>
                        {"".join([f'<option value="{y}">{y}</option>' for y in years])}
                    </select>
                </div>
            </div>

            <div class="table-responsive mb-3">
                <table id="hospitalTable" class="table table-striped table-bordered">
                    <thead>
                        <tr>{"".join([f"<th>{col}</th>" for col in subset.columns])}</tr>
                    </thead>
                    <tbody></tbody>
                </table>
            </div>

            <nav><ul class="pagination" id="pagination"></ul></nav>

            <div class="row mb-3">
                <div class="col-md-4"><canvas id="conditionChart"></canvas></div>
                <div class="col-md-4"><canvas id="insuranceChart"></canvas></div>
                <div class="col-md-4"><canvas id="yearChart"></canvas></div>
            </div>

            <button id="downloadBtn" class="btn btn-success">Download Filtered CSV</button>
        </div>

        <script>
            const fullData = {json.dumps(df.to_dict(orient="records"))};
            let currentPage = {page};
            const perPage = {per_page};

            function renderTable(data) {{
                const tbody = $("#hospitalTable tbody");
                tbody.empty();
                data.forEach(row => {{
                    const tr = $("<tr></tr>");
                    for (const key in row) tr.append("<td>" + row[key] + "</td>");
                    tbody.append(tr);
                }});
            }}

            function filterData() {{
                const search = $("#searchInput").val().toLowerCase();
                const insurance = $("#insuranceFilter").val();
                const condition = $("#conditionFilter").val();
                const year = $("#yearFilter").val();

                let filtered = fullData.filter(row =>
                    Object.values(row).some(v => String(v).toLowerCase().includes(search)) &&
                    (!insurance || row["Insurance Provider"] === insurance) &&
                    (!condition || row["Medical Condition"] === condition) &&
                    (!year || row["Admission Year"] == year)
                );

                renderTable(filtered.slice((currentPage-1)*perPage, currentPage*perPage));
            }}

            $("#searchInput, #insuranceFilter, #conditionFilter, #yearFilter")
                .on("input change", filterData);

            filterData();
        </script>
    </body>
    </html>
    """

    return HTMLResponse(html_content)
