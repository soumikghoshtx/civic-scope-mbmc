<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MBMC CivicScope | Live Tracker</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        :root { --mbmc-blue: #2c3e50; --bg-light: #f4f6f9; --status-green: #27ae60; }
        body { font-family: 'Segoe UI', sans-serif; margin: 0; background-color: var(--bg-light); color: #333; }
        
        .header { background-color: var(--mbmc-blue); color: white; padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center; }
        .header h1 { margin: 0; font-size: 1.5rem; }
        
        .container { max-width: 1000px; margin: 2rem auto; padding: 0 1rem; }
        
        .status-bar { background: white; padding: 1rem; border-radius: 8px; margin-bottom: 2rem; display: flex; justify-content: space-around; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
        .stat-item { text-align: center; }
        .stat-val { font-size: 1.5rem; font-weight: bold; color: var(--mbmc-blue); }
        .stat-lbl { font-size: 0.85rem; color: #666; }

        .project-list { background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
        .project-item { padding: 1.2rem; border-bottom: 1px solid #eee; transition: 0.2s; }
        .project-item:hover { background-color: #f8f9fa; }
        
        .project-title { font-weight: bold; font-size: 1.1rem; color: var(--mbmc-blue); margin-bottom: 5px; }
        .project-meta { display: flex; gap: 15px; font-size: 0.85rem; color: #666; flex-wrap: wrap; }
        .badge { background: #e8f8f0; color: var(--status-green); padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 0.75rem; }
        
        .loading { text-align: center; padding: 3rem; color: #666; }
        .error { text-align: center; padding: 2rem; color: #c0392b; background: #fadbd8; border-radius: 8px; }
    </style>
</head>
<body>

    <div class="header">
        <h1><i class="fas fa-city"></i> MBMC CivicScope</h1>
        <div style="font-size: 0.8rem; opacity: 0.8;">Live Data</div>
    </div>

    <div class="container">
        
        <div class="status-bar">
            <div class="stat-item">
                <div class="stat-val" id="count-total">-</div>
                <div class="stat-lbl">Active Tenders</div>
            </div>
            <div class="stat-item">
                <div class="stat-val" id="last-scan">-</div>
                <div class="stat-lbl">Last Robot Scan</div>
            </div>
        </div>

        <div class="project-list" id="project-list">
            <div class="loading">
                <i class="fas fa-circle-notch fa-spin fa-2x"></i><br><br>
                Connecting to MBMC Data Stream...
            </div>
        </div>
    </div>

    <script>
        // Use relative path so it works on both localhost and cloud
        const API_URL = "/api/projects";

        async function loadData() {
            const listEl = document.getElementById('project-list');
            const countEl = document.getElementById('count-total');
            const scanEl = document.getElementById('last-scan');

            try {
                const response = await fetch(API_URL);
                if (!response.ok) throw new Error("Server Error");
                
                const data = await response.json();
                
                if (data.length === 0) {
                    listEl.innerHTML = '<div class="loading">No projects found in database yet. The robot is working. Try refreshing in 1 minute.</div>';
                    return;
                }

                // Update Stats
                countEl.innerText = data.length;
                if(data[0].last_checked) {
                    scanEl.innerText = data[0].last_checked.split(' ')[1]; // Show time only
                }

                // Render List
                listEl.innerHTML = '';
                data.forEach(p => {
                    const html = `
                        <div class="project-item">
                            <div class="project-title">
                                ${p.title} <span class="badge">${p.status}</span>
                            </div>
                            <div class="project-meta">
                                <span><i class="fas fa-building"></i> ${p.department}</span>
                                <span><i class="fas fa-calendar-alt"></i> Date: ${p.publish_date}</span>
                                <span><i class="fas fa-hashtag"></i> ID: ${p.id}</span>
                            </div>
                        </div>
                    `;
                    listEl.innerHTML += html;
                });

            } catch (error) {
                console.error(error);
                listEl.innerHTML = `
                    <div class="error">
                        <strong>Connection Failed</strong><br>
                        Could not reach the server.
                    </div>
                `;
            }
        }

        window.onload = loadData;
    </script>
</body>
</html>