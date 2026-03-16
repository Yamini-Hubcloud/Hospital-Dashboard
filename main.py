from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
import pandas as pd
import json

app = FastAPI(title="Hospital Dashboard App")

# Load CSV
df = pd.read_csv("hospital_data.csv")

@app.get("/")
def home():
    return {"message": "Hospital API is running"}

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(page: int = 1, per_page: int = 50):
    # Pagination setup
    start = (page - 1) * per_page
    end = start + per_page
    subset = df.iloc[start:end]

    # Dropdown values
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
            body {{ padding: 20px; }}
            th {{ cursor: pointer; }}
            .filter-box {{ margin-bottom: 15px; }}
        </style>
    </head>
    <body>
        <h2>Hospital Dashboard</h2>

        <!-- Filters -->
        <div class="row filter-box">
            <div class="col-md-4"><input id="searchInput" class="form-control" placeholder="Search all columns"></div>
            <div class="col-md-4">
                <select id="insuranceFilter" class="form-select">
                    <option value="">All Insurance Providers</option>
                    {"".join([f'<option value="{ip}">{ip}</option>' for ip in insurance_providers])}
                </select>
            </div>
            <div class="col-md-2">
                <select id="conditionFilter" class="form-select">
                    <option value="">All Conditions</option>
                    {"".join([f'<option value="{c}">{c}</option>' for c in conditions])}
                </select>
            </div>
            <div class="col-md-2">
                <select id="yearFilter" class="form-select">
                    <option value="">All Years</option>
                    {"".join([f'<option value="{y}">{y}</option>' for y in years])}
                </select>
            </div>
        </div>

        <!-- Table -->
        <div class="table-responsive">
            <table id="hospitalTable" class="table table-striped table-bordered">
                <thead>
                    <tr>{"".join([f"<th>{col}</th>" for col in subset.columns])}</tr>
                </thead>
                <tbody></tbody>
            </table>
        </div>

        <!-- Pagination -->
        <nav>
          <ul class="pagination" id="pagination"></ul>
        </nav>

        <!-- Charts -->
        <div class="row">
            <div class="col-md-4"><canvas id="conditionChart" height="100"></canvas></div>
            <div class="col-md-4"><canvas id="insuranceChart" height="100"></canvas></div>
            <div class="col-md-4"><canvas id="yearChart" height="100"></canvas></div>
        </div>

        <!-- Download Button -->
        <button id="downloadBtn" class="btn btn-success mt-2">Download Filtered CSV</button>

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
                const searchVal = $("#searchInput").val().toLowerCase();
                const insuranceVal = $("#insuranceFilter").val();
                const condVal = $("#conditionFilter").val();
                const yearVal = $("#yearFilter").val();

                let filtered = fullData.filter(row => {{
                    const matchSearch = Object.values(row).some(v => String(v).toLowerCase().includes(searchVal));
                    const matchInsurance = !insuranceVal || row["Insurance Provider"] === insuranceVal;
                    const matchCond = !condVal || row["Medical Condition"] === condVal;
                    const matchYear = !yearVal || row["Admission Year"] == yearVal;
                    return matchSearch && matchInsurance && matchCond && matchYear;
                }});

                const startIdx = (currentPage - 1) * perPage;
                renderTable(filtered.slice(startIdx, startIdx + perPage));
                renderCharts(filtered);
                renderPagination(filtered.length);
            }}

            function renderCharts(filteredData) {{
                const condCounts = {{}};
                const insuranceCounts = {{}};
                const yearCounts = {{}};

                filteredData.forEach(r => {{
                    condCounts[r["Medical Condition"] || "Unknown"] = (condCounts[r["Medical Condition"]] || 0) + 1;
                    insuranceCounts[r["Insurance Provider"] || "Unknown"] = (insuranceCounts[r["Insurance Provider"]] || 0) + 1;
                    yearCounts[r["Admission Year"] || "Unknown"] = (yearCounts[r["Admission Year"]] || 0) + 1;
                }});

                // Condition chart
                const condLabels = Object.keys(condCounts), condValues = Object.values(condCounts);
                if(window.condChart) window.condChart.destroy();
                const ctxC = document.getElementById('conditionChart').getContext('2d');
                window.condChart = new Chart(ctxC, {{
                    type:'bar',
                    data:{{labels:condLabels,datasets:[{{label:'Patients by Condition',data:condValues, backgroundColor:'rgba(54,162,235,0.7)'}}]}},
                    options:{{responsive:true,title:{{display:true,text:'Patients by Medical Condition'}}}}
                }});

                // Insurance chart
                const insuranceLabels = Object.keys(insuranceCounts), insuranceValues = Object.values(insuranceCounts);
                if(window.insuranceChart) window.insuranceChart.destroy();
                const ctxI = document.getElementById('insuranceChart').getContext('2d');
                window.insuranceChart = new Chart(ctxI, {{
                    type:'bar',
                    data:{{labels:insuranceLabels,datasets:[{{label:'Patients by Insurance Provider',data:insuranceValues, backgroundColor:'rgba(255,99,132,0.7)'}}]}},
                    options:{{responsive:true,title:{{display:true,text:'Patients by Insurance Provider'}}}}
                }});

                // Year chart
                const yearLabels = Object.keys(yearCounts), yearValues = Object.values(yearCounts);
                if(window.yearChart) window.yearChart.destroy();
                const ctxY = document.getElementById('yearChart').getContext('2d');
                window.yearChart = new Chart(ctxY, {{
                    type:'bar',
                    data:{{labels:yearLabels,datasets:[{{label:'Patients by Year',data:yearValues, backgroundColor:'rgba(75,192,192,0.7)'}}]}},
                    options:{{responsive:true,title:{{display:true,text:'Patients by Admission Year'}}}}
                }});
            }}

            function renderPagination(total) {{
                const pages = Math.ceil(total/perPage);
                const ul = $("#pagination");
                ul.empty();
                for(let i=1;i<=pages;i++) {{
                    const activeClass = i===currentPage ? "active" : "";
                    ul.append('<li class="page-item ' + activeClass + '"><a class="page-link" href="#">' + i + '</a></li>');
                }}
                $(".page-link").click(function(e){{
                    e.preventDefault();
                    currentPage = Number($(this).text());
                    filterData();
                }});
            }}

            $("#searchInput, #insuranceFilter, #conditionFilter, #yearFilter").on("input change", filterData);

            $("#downloadBtn").click(function(){{
                const filtered = fullData.filter(row => {{
                    const searchVal = $("#searchInput").val().toLowerCase();
                    const insuranceVal = $("#insuranceFilter").val();
                    const condVal = $("#conditionFilter").val();
                    const yearVal = $("#yearFilter").val();
                    const matchSearch = Object.values(row).some(v => String(v).toLowerCase().includes(searchVal));
                    const matchInsurance = !insuranceVal || row["Insurance Provider"] === insuranceVal;
                    const matchCond = !condVal || row["Medical Condition"] === condVal;
                    const matchYear = !yearVal || row["Admission Year"] == yearVal;
                    return matchSearch && matchInsurance && matchCond && matchYear;
                }});
                if(filtered.length === 0) return alert("No data to download");
                const csvContent = "data:text/csv;charset=utf-8," + 
                    [Object.keys(filtered[0]).join(","), ...filtered.map(r=>Object.values(r).join(","))].join("\\n");
                const encodedUri = encodeURI(csvContent);
                const link = document.createElement("a");
                link.setAttribute("href", encodedUri);
                link.setAttribute("download","hospital_filtered.csv");
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            }});

            // Initial render
            filterData();
        </script>
    </body>
    </html>
    """
    return html_content
