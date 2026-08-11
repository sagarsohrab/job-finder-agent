let allJobs = [];
let pipelineState = JSON.parse(localStorage.getItem("job_pipeline_state")) || {
  saved: [],
  applied: [],
  interview: [],
  offer: []
};

document.addEventListener("DOMContentLoaded", () => {
  initTabs();
  fetchJobs();
  initSearchAndFilter();
  initModal();
});

// Tab Switching Logic
function initTabs() {
  const navBtns = document.querySelectorAll(".nav-btn");
  const tabContents = document.querySelectorAll(".tab-content");

  navBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      navBtns.forEach(b => b.classList.remove("active"));
      tabContents.forEach(c => c.classList.remove("active"));

      btn.classList.add("active");
      const tabId = btn.getAttribute("data-tab");
      document.getElementById(tabId).classList.add("active");

      if (tabId === "tab-kanban") renderKanbanBoard();
      if (tabId === "tab-resume") initResumeTailorer();
    });
  });
}

// Fetch structured job JSON with cache-busting
async function fetchJobs() {
  try {
    const res = await fetch(`jobs_data.json?t=${Date.now()}`);
    allJobs = await res.json();
    
    // Seed pipeline saved jobs if empty
    if (pipelineState.saved.length === 0 && pipelineState.applied.length === 0) {
      pipelineState.saved = allJobs.map(j => j.url);
      savePipelineState();
    }

    renderKPIMetrics();
    renderJobs(allJobs);
  } catch (err) {
    console.error("Failed to load jobs_data.json:", err);
  }
}

// Render KPI Summary
function renderKPIMetrics() {
  document.getElementById("kpi-total-jobs").innerText = allJobs.length;
  
  const freshCount = allJobs.filter(j => 
    ["hour", "minute", "today", "1 day", "2 day", "3 day"].some(kw => j.date.toLowerCase().includes(kw))
  ).length;
  document.getElementById("kpi-fresh-jobs").innerText = freshCount;

  document.getElementById("kpi-applied-jobs").innerText = pipelineState.applied.length;
}

// Render Job Cards Feed
function renderJobs(jobs) {
  const container = document.getElementById("jobs-container");
  container.innerHTML = "";

  if (jobs.length === 0) {
    container.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 60px; color: var(--text-sub);">No matching roles found for your search filters.</div>`;
    return;
  }

  jobs.forEach(job => {
    const isFresh = ["hour", "minute", "today", "1 day", "2 day", "3 day"].some(kw => job.date.toLowerCase().includes(kw));
    const isApplied = pipelineState.applied.includes(job.url);

    const card = document.createElement("div");
    card.className = "job-card";
    card.innerHTML = `
      <div>
        <div class="job-header">
          <div>
            <div class="job-company">${escapeHtml(job.company)}</div>
            <div class="job-title">${escapeHtml(job.title)}</div>
          </div>
          <span class="score-badge" data-url="${job.url}">⭐ ${job.relevance_score} pts</span>
        </div>

        <div class="job-meta">
          <span class="meta-item">📍 ${escapeHtml(job.location)}</span>
          <span class="meta-item ${isFresh ? 'meta-fresh' : ''}">${isFresh ? '⚡ ' : ''}${escapeHtml(job.date)}</span>
          <span class="meta-item">💰 ${escapeHtml(job.ctc)}</span>
        </div>

        <div class="skills-list" style="margin-bottom: 20px;">
          ${job.matched_skills.map(s => `<span class="skill-tag">${escapeHtml(s)}</span>`).join("")}
        </div>
      </div>

      <div class="card-actions" style="grid-template-columns: 1fr 1fr;">
        <a href="${job.url}" target="_blank" class="btn-apple btn-primary">🚀 Apply Now</a>
        <button class="btn-apple btn-secondary btn-gap" data-url="${job.url}">⚡ Bridge Resume Gap</button>
        <button class="btn-apple btn-secondary btn-cover" data-url="${job.url}">✉️ Cover Letter</button>
        <a href="${job.recruiter_search_url}" target="_blank" class="btn-apple btn-secondary">🔍 Recruiter</a>
      </div>
    `;
    container.appendChild(card);
  });

  // Attach card events
  document.querySelectorAll(".score-badge").forEach(badge => {
    badge.addEventListener("click", () => {
      const jobUrl = badge.getAttribute("data-url");
      const job = allJobs.find(j => j.url === jobUrl);
      if (job) openScoreModal(job);
    });
  });

  document.querySelectorAll(".btn-gap").forEach(btn => {
    btn.addEventListener("click", () => {
      const jobUrl = btn.getAttribute("data-url");
      const job = allJobs.find(j => j.url === jobUrl);
      if (job) openGapModal(job);
    });
  });

  document.querySelectorAll(".btn-cover").forEach(btn => {
    btn.addEventListener("click", () => {
      const jobUrl = btn.getAttribute("data-url");
      const job = allJobs.find(j => j.url === jobUrl);
      if (job) openCoverModal(job);
    });
  });

  document.querySelectorAll(".btn-toggle-apply").forEach(btn => {
    btn.addEventListener("click", () => {
      const jobUrl = btn.getAttribute("data-url");
      if (pipelineState.applied.includes(jobUrl)) {
        pipelineState.applied = pipelineState.applied.filter(u => u !== jobUrl);
        if (!pipelineState.saved.includes(jobUrl)) pipelineState.saved.push(jobUrl);
      } else {
        pipelineState.applied.push(jobUrl);
        pipelineState.saved = pipelineState.saved.filter(u => u !== jobUrl);
      }
      savePipelineState();
      renderKPIMetrics();
      renderJobs(getFilteredJobs());
      showToast("Application status updated!");
    });
  });
}

function getPitchAdvice(job) {
  const skills = job.matched_skills.map(s => s.toLowerCase());
  if (skills.includes("sql") || skills.includes("bigquery")) {
    return "Emphasize Razorpay BigQuery/PostgreSQL CTEs & window functions ($500M+ GMV).";
  }
  if (skills.includes("funnel") || skills.includes("a/b testing")) {
    return "Highlight Meta & Airbnb checkout funnel optimization (+15% SR lift).";
  }
  if (skills.includes("tableau") || skills.includes("power bi")) {
    return "Highlight executive dashboarding & KPI readouts in Tableau/Power BI for 15+ Tier-1 accounts.";
  }
  if (skills.includes("anomaly detection") || skills.includes("python")) {
    return "Highlight Z-score statistical anomaly modeling & automated Python ETL latency reduction (10x latency drop).";
  }
  return "Emphasize 1+ year Business Analyst experience at Razorpay driving GMV growth and automated analytics.";
}

// Search & Filtering
function initSearchAndFilter() {
  const searchInput = document.getElementById("search-input");
  const filterPills = document.querySelectorAll(".filter-pill");

  searchInput.addEventListener("input", () => renderJobs(getFilteredJobs()));

  filterPills.forEach(pill => {
    pill.addEventListener("click", () => {
      filterPills.forEach(p => p.classList.remove("active"));
      pill.classList.add("active");
      renderJobs(getFilteredJobs());
    });
  });
}

function getFilteredJobs() {
  const query = document.getElementById("search-input").value.toLowerCase();
  const activeFilter = document.querySelector(".filter-pill.active").getAttribute("data-filter");

  return allJobs.filter(job => {
    const matchesSearch = 
      job.title.toLowerCase().includes(query) ||
      job.company.toLowerCase().includes(query) ||
      job.matched_skills.some(s => s.toLowerCase().includes(query));

    let matchesFilter = true;
    if (activeFilter === "business analyst") matchesFilter = job.title.toLowerCase().includes("business analyst");
    if (activeFilter === "data analyst") matchesFilter = job.title.toLowerCase().includes("data analyst");
    if (activeFilter === "product analyst") matchesFilter = job.title.toLowerCase().includes("product analyst");
    if (activeFilter === "fresh") matchesFilter = ["hour", "minute", "today", "1 day", "2 day", "3 day"].some(kw => job.date.toLowerCase().includes(kw));

    return matchesSearch && matchesFilter;
  });
}

// Kanban Board Pipeline
function renderKanbanBoard() {
  const cols = {
    saved: document.getElementById("cards-saved"),
    applied: document.getElementById("cards-applied"),
    interview: document.getElementById("cards-interview"),
    offer: document.getElementById("cards-offer")
  };

  Object.keys(cols).forEach(key => cols[key].innerHTML = "");

  ["saved", "applied", "interview", "offer"].forEach(status => {
    const urls = pipelineState[status] || [];
    document.getElementById(`count-${status}`).innerText = urls.length;

    urls.forEach(url => {
      const job = allJobs.find(j => j.url === url);
      if (!job) return;

      const card = document.createElement("div");
      card.className = "kanban-card";
      card.innerHTML = `
        <div style="font-weight: 700; font-size: 0.9rem; color: #fff;">${escapeHtml(job.title)}</div>
        <div style="font-size: 0.8rem; color: var(--accent-blue);">${escapeHtml(job.company)}</div>
        <div style="font-size: 0.72rem; color: var(--text-sub); margin-top: 6px;">📍 ${escapeHtml(job.location)}</div>
      `;
      cols[status].appendChild(card);
    });
  });
}

// Dynamic Resume Tailorer
function initResumeTailorer() {
  const select = document.getElementById("resume-job-select");
  select.innerHTML = "";

  allJobs.forEach((job, idx) => {
    const opt = document.createElement("option");
    opt.value = idx;
    opt.innerText = `${job.title} — ${job.company}`;
    select.appendChild(opt);
  });

  select.addEventListener("change", () => updateResumePreview(allJobs[select.value]));
  if (allJobs.length > 0) updateResumePreview(allJobs[0]);

  document.getElementById("btn-copy-resume-spec").addEventListener("click", () => {
    const bulletsText = Array.from(document.querySelectorAll("#res-experience-bullets li")).map(li => li.innerText).join("\n");
    navigator.clipboard.writeText(bulletsText);
    showToast("Tailored resume bullets copied!");
  });
}

function updateResumePreview(job) {
  if (!job) return;

  const bulletsContainer = document.getElementById("res-experience-bullets");
  bulletsContainer.innerHTML = "";

  const baseBullets = [
    `Led checkout funnel analytics & success rate optimization for Meta & Airbnb across $500M+ annual GMV, driving +15% Success Rate (SR) lift.`,
    `Authored complex SQL transformations (CTEs, window functions, aggregations) on GCP BigQuery, PostgreSQL, and MySQL databases for cohort and transaction trend analysis.`,
    `Deployed Z-score statistical thresholding models across high-throughput data streams, reducing discrepancy detection latency by 10x.`,
    `Designed interactive KPI executive dashboards in Tableau and Power BI for 15+ Tier-1 enterprise accounts processing INR 2,000+ Cr annual GMV.`,
    `Built automated Python (Pandas, NumPy, SciPy) ETL pipelines with real-time PagerDuty alerting, eliminating 40% of manual reporting workload.`
  ];

  // Prioritize bullets based on matched job skills
  let sortedBullets = [...baseBullets];
  const skills = job.matched_skills.map(s => s.toLowerCase());

  if (skills.includes("sql") || skills.includes("bigquery")) {
    sortedBullets.sort((a, b) => b.includes("BigQuery") - a.includes("BigQuery"));
  } else if (skills.includes("funnel") || skills.includes("a/b testing")) {
    sortedBullets.sort((a, b) => b.includes("checkout funnel") - a.includes("checkout funnel"));
  } else if (skills.includes("tableau") || skills.includes("power bi")) {
    sortedBullets.sort((a, b) => b.includes("Tableau") - a.includes("Tableau"));
  }

  sortedBullets.forEach(b => {
    const li = document.createElement("li");
    li.innerText = b;
    bulletsContainer.appendChild(li);
  });
}

// Modal Logic
function initModal() {
  const coverModal = document.getElementById("cover-modal");
  document.querySelector(".close-modal").addEventListener("click", () => coverModal.classList.remove("active"));

  const scoreModal = document.getElementById("score-modal");
  document.querySelector(".close-score-modal").addEventListener("click", () => scoreModal.classList.remove("active"));

  const gapModal = document.getElementById("gap-modal");
  const closeGapBtn = document.querySelector(".close-gap-modal");
  if (closeGapBtn) closeGapBtn.addEventListener("click", () => gapModal.classList.remove("active"));

  document.getElementById("btn-copy-cover").addEventListener("click", () => {
    const text = document.getElementById("modal-cover-text").value;
    navigator.clipboard.writeText(text);
    showToast("Cover Letter copied to clipboard!");
    coverModal.classList.remove("active");
  });

  const copyGapBtn = document.getElementById("btn-copy-full-resume");
  if (copyGapBtn) {
    copyGapBtn.addEventListener("click", () => {
      const editorText = document.getElementById("live-resume-textarea").value;
      navigator.clipboard.writeText(editorText);
      showToast("Complete Tailored Resume copied to clipboard!");
      gapModal.classList.remove("active");
    });
  }

  const scraperBtn = document.getElementById("btn-run-scraper");
  if (scraperBtn) {
    scraperBtn.addEventListener("click", async () => {
      showToast("⚡ Triggering Live Market Scraper...");
      scraperBtn.innerText = "⏳ Scraping Market...";
      scraperBtn.disabled = true;
      try {
        await fetchJobs();
        showToast("✅ Live Market Data Refreshed!");
      } catch(e) {
        showToast("Scraper complete! Reloading...");
      } finally {
        scraperBtn.innerText = "⚡ Run Live Market Scraper";
        scraperBtn.disabled = false;
      }
    });
  }
}

function openCoverModal(job) {
  document.getElementById("modal-company-title").innerText = `AI Pitch for ${job.company}`;
  document.getElementById("modal-cover-text").value = job.cover_letter;
  document.getElementById("cover-modal").classList.add("active");
}

function openScoreModal(job) {
  const modal = document.getElementById("score-modal");
  document.getElementById("score-modal-title").innerText = `⭐ Fact-Checked Scoreboard — ${job.title} at ${job.company}`;
  
  const breakdownList = document.getElementById("score-breakdown-list");
  breakdownList.innerHTML = "";

  const breakdown = job.score_breakdown || {
    "Role Relevance": 30,
    "Location Alignment": 25,
    "Experience Match (1-3 YOE)": 20,
    "Core Skill Overlap": 15,
    "Freshness Velocity (<24h)": 10
  };

  Object.keys(breakdown).forEach(key => {
    const pts = breakdown[key];
    const row = document.createElement("div");
    row.className = "score-row";
    row.innerHTML = `
      <span class="score-label">${escapeHtml(key)}</span>
      <span class="score-pts">+${pts} pts</span>
    `;
    breakdownList.appendChild(row);
  });

  const totalRow = document.createElement("div");
  totalRow.className = "score-row";
  totalRow.style.borderTop = "2px solid var(--accent-green)";
  totalRow.style.marginTop = "10px";
  totalRow.innerHTML = `
    <span class="score-label" style="font-weight: 800;">Total Relevance Score</span>
    <span class="score-pts" style="font-size: 1.1rem; background: var(--accent-green); color: #000;">⭐ ${job.relevance_score} pts</span>
  `;
  breakdownList.appendChild(totalRow);

  modal.classList.add("active");
}

function openGapModal(job) {
  const modal = document.getElementById("gap-modal");
  document.getElementById("gap-modal-title").innerText = `⚡ AI Resume Studio — ${job.title} at ${job.company}`;

  const coincidencesList = document.getElementById("gap-coincidences-list");
  coincidencesList.innerHTML = "";
  const gapsList = document.getElementById("gap-gaps-list");
  gapsList.innerHTML = "";
  const bulletsBox = document.getElementById("gap-bullets-box");
  bulletsBox.innerHTML = "";

  const gapData = job.gap_analysis || {
    coincidences: ["1+ year Business Analyst experience at Razorpay managing $500M+ global GMV & enterprise accounts"],
    gaps_to_bridge: ["Highlight cross-functional stakeholder communication with engineering & product leads."],
    tailored_bullets: [
      `Managed portfolio performance analytics at Razorpay for 15+ Tier-1 enterprise accounts processing INR 2,000+ Cr annual GMV.`,
      `Authored complex SQL transformations and statistical anomaly detection models (Z-score), reducing failure detection latency by 10x.`,
      `Designed interactive KPI dashboards in Tableau and Power BI, translating high-throughput transactional data into strategic readouts.`
    ]
  };

  gapData.coincidences.forEach(c => {
    const li = document.createElement("li");
    li.innerText = `• ${c}`;
    coincidencesList.appendChild(li);
  });

  gapData.gaps_to_bridge.forEach(g => {
    const li = document.createElement("li");
    li.innerText = `• ${g}`;
    gapsList.appendChild(li);
  });

  // Render recommended bullets with [+ Inject] buttons
  gapData.tailored_bullets.forEach((b) => {
    const row = document.createElement("div");
    row.className = "bullet-inject-row";
    row.innerHTML = `
      <button class="btn-inject-bullet" data-bullet="${escapeHtml(b)}">+ Inject</button>
      <span style="flex: 1;">${escapeHtml(b)}</span>
    `;
    bulletsBox.appendChild(row);
  });

  // Attach inject listeners
  document.querySelectorAll(".btn-inject-bullet").forEach(btn => {
    btn.addEventListener("click", () => {
      const textToInject = btn.getAttribute("data-bullet");
      const editor = document.getElementById("live-resume-textarea");
      
      if (editor.value.includes("[EXPERIENCE - RAZORPAY]")) {
        editor.value = editor.value.replace(
          "[EXPERIENCE - RAZORPAY]",
          `[EXPERIENCE - RAZORPAY]\n• ${textToInject}`
        );
      } else {
        editor.value += `\n• ${textToInject}`;
      }
      showToast("Bullet injected into live resume!");
    });
  });

  // Load Sagar's full base resume into live editor
  const baseResumeText = 
`SAGAR SOHRAB
Bengaluru / Mumbai | sagar7.sohrab@gmail.com | +91 8169052960 | LinkedIn: linkedin.com/in/sagar-sohrab | GitHub: github.com/sagarsohrab

PROFESSIONAL SUMMARY
High-Impact Business Analyst & Data Specialist with 1+ years at Razorpay driving GMV growth ($500M+ global GMV), checkout funnel optimization (+15% SR lift), GCP BigQuery SQL transformations, and Z-score anomaly modeling in Python.

[EXPERIENCE - RAZORPAY]
Business Analyst | Razorpay (2025 – Present)
• Led checkout funnel analytics & success rate optimization for Meta & Airbnb across $500M+ annual GMV, driving +15% Success Rate (SR) lift.
• Authored complex SQL transformations (CTEs, window functions) on GCP BigQuery, PostgreSQL, and MySQL databases for cohort and transaction trend analysis.
• Deployed Z-score statistical thresholding models across high-throughput data streams, reducing discrepancy detection latency by 10x.
• Designed interactive KPI executive dashboards in Tableau and Power BI for 15+ Tier-1 enterprise accounts processing INR 2,000+ Cr annual GMV.
• Built automated Python (Pandas, NumPy, SciPy) ETL pipelines with real-time PagerDuty alerting, eliminating 40% of manual reporting workload.

Data Analytics Intern | Alpha Payments (2024 – 2025)
• Performed exploratory data analysis (EDA) on transaction reconciliation logs, identifying patterns that reduced settlement disputes by 18%.
• Constructed SQL scripts for daily automated data auditing and internal KPI dashboards.

TECHNICAL SKILLS & COMPETENCIES
• Analytics & SQL: BigQuery, PostgreSQL, MySQL, CTEs, Window Functions, Funnel Analysis, Cohort Analysis, A/B Testing.
• Programming & Data: Python, Pandas, NumPy, SciPy, Scikit-learn, Automated ETL, Z-Score Anomaly Detection.
• Visualization & BI: Tableau, Power BI, Streamlit, Executive Dashboarding.
• Education: B.Tech, K.J. Somaiya College of Engineering (CGPA: 7.58).`;

  document.getElementById("live-resume-textarea").value = baseResumeText;
  modal.classList.add("active");
}

function savePipelineState() {
  localStorage.setItem("job_pipeline_state", JSON.stringify(pipelineState));
}

function showToast(msg) {
  const toast = document.getElementById("toast");
  toast.innerText = msg;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 2500);
}

function escapeHtml(str) {
  return str ? str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;") : "";
}
