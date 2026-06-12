// Global variables for Chart.js instances
let pressureFlowChart = null;
let wardFailureChart = null;
let riskScatterChart = null;

// Global GIS map variables
let map = null;
let pipeMarkersLayer = null;
let allPipesData = []; // Store pipes data loaded from server

// Active state
let currentZoneOffice = "";

// Theme and Language states
let currentTheme = localStorage.getItem("theme") || "light";
let currentLanguage = localStorage.getItem("lang") || "hi";
let currentUserRole = "employee"; // 'employee' or 'admin'
let adminToken = localStorage.getItem("adminToken") || "";

// ============================================================
// I18N TRANSLATION MAPS
// ============================================================
const translations = {
    hi: {
        // Sidebar & Brand
        "brand-name": "जल प्रदाय विभाग",
        "brand-sub": "इंदौर नगर निगम",
        "nav-dashboard": "मुख्य डैशबोर्ड (Monitor)",
        "nav-gis": "GIS पाइपलाइन नेटवर्क",
        "nav-predict": "विफलता पूर्वानुमान",
        "nav-maintenance": "अनुरक्षण अनुशंसाएं",
        "nav-settings": "अलार्म सेटिंग्स",
        "status-text": "सिस्टम लाइव मॉनिटर",
        // Header
        "title-main": "स्मार्ट जल ग्रिड नियंत्रण केंद्र",
        "title-sub": "इंदौर जल प्रदाय नेटवर्क प्रबंधन प्रणाली (जल प्रदाय संभाग)",
        "label-zone": "प्राधिकृत ज़ोन:",
        "option-all-zones": "-- सभी इंदौर ज़ोन कार्यालय --",
        "btn-pdf": "PDF रिपोर्ट डाउनलोड",
        "btn-csv": "CSV डेटा निर्यात",
        "role-employee": "स्थानीय कर्मचारी",
        "role-admin": "प्रशासक (Administrator)",
        // Login Modal
        "login-title": "प्रशासक लॉगिन (Administrator Login)",
        "login-user-lbl": "उपयोगकर्ता नाम (Username)",
        "login-pass-lbl": "पासवर्ड (Password)",
        "login-cancel": "रद्द करें",
        "login-submit": "लॉगिन",
        // KPI Cards
        "kpi-total-pipes-lbl": "कुल पाइपलाइन खंड",
        "kpi-active-leaks-lbl": "सक्रिय रिसाव (Leaks)",
        "kpi-high-risk-lbl": "अति संवेदनशील खंड",
        "kpi-avg-pressure-lbl": "औसत जल दबाव",
        "sub-total": "कुल मॉनिटर किए गए",
        "sub-active": "तत्काल कार्रवाई आवश्यक",
        "sub-high": "विफलता जोखिम > 40%",
        "sub-pressure": "ग्रिड का औसत मान",
        // Charts
        "chart-pressure-flow-title": "पाइपलाइन दबाव और प्रवाह दर (Telemetry Analysis)",
        "chart-pressure-flow-tag": "ऐतिहासिक और वास्तविक समय प्रवृत्ति",
        "chart-pressure-flow-info": "यह चार्ट 20 इंदौर पाइपलाइन खंडों के लिए जल दबाव (नीली रेखा, बाएँ अक्ष) और प्रवाह दर (बैंगनी रेखा, दाएँ अक्ष) प्रदर्शित करता है। दबाव में अचानक गिरावट और प्रवाह दर में उछाल पाइप फटने या रिसाव विसंगति को दर्शाता है। Random Forest मॉडल इस सहसंबंध का उपयोग रीयल-टाइम भविष्यवाणियों के लिए करते हैं।",
        "chart-ward-title": "वार्ड-वार सक्रिय विफलता वितरण",
        "chart-ward-tag": "रिसाव आवृत्तियाँ",
        "chart-ward-info": "यह चार्ट प्रशासनिक वार्डों में सक्रिय रिसाव आवृत्तियों (Leakage_Flag = 1) का वितरण दिखाता है। यह पुरानी बुनियादी ढांचे (हॉटस्पॉट) वाले वार्डों को उजागर करता है, जिससे इंजीनियरों को स्थानीय पाइपलाइन प्रतिस्थापन योजनाओं को प्राथमिकता देने में मदद मिलती है।",
        "chart-scatter-title": "दबाव बनाम प्रवाह क्लस्टर विश्लेषण",
        "chart-scatter-tag": "विसंगति क्लस्टर",
        "chart-scatter-info": "यह स्कैटर चार्ट प्रत्येक पाइपलाइन खंड के लिए प्रवाह दर (X-अक्ष) बनाम जल दबाव (Y-अक्ष) को प्लॉट करता है। मानक परिचालन पाइप एक विशिष्ट हाइड्रोलिक ज़ोन में क्लस्टर होते हैं। ऑफ-क्लस्टर स्कैटर बिंदु जोड़ विफलता, क्लॉगिंग या रिसाव जैसी विसंगतियों को दर्शाते हैं।",
        "btn-guide": "मार्गदर्शिका",
        // Alerts Feed
        "alerts-feed-title": "वास्तविक समय विसंगति और रिसाव अलार्म लॉग्स",
        "alerts-feed-sub": "सेंसर सिमुलेशन द्वारा स्वचालित रूप से पहचाने गए अलार्म",
        "alerts-empty": "सिस्टम सामान्य रूप से कार्य कर रहा है। कोई सक्रिय अलार्म नहीं है।",
        // GIS Map
        "gis-legend-title": "पाइपलाइन संकेतक",
        "gis-legend-normal": "सामान्य संचालन खंड",
        "gis-legend-medium": "मध्यम जोखिम (जोखिम स्कोर > 20)",
        "gis-legend-leak": "सक्रिय विफलता/लीकेज खंड",
        "gis-filter-title": "पाइपलाइन फ़िल्टर नियंत्रण",
        "gis-filter-normal": "सामान्य पाइपलाइन दिखाएं",
        "gis-filter-high": "उच्च जोखिम पाइपलाइन दिखाएं",
        "gis-filter-leak": "सक्रिय लीकेज दिखाएं",
        "gis-search-title": "वार्ड/पाइप ID खोजें",
        "gis-search-placeholder": "खोजें (जैसे IND-PIPE)...",
        "map-btn-street": "सड़क मानचित्र",
        "map-btn-satellite": "उपग्रह दृश्य",
        // Diagnostics
        "diag-form-title": "AI-आधारित विफलता विश्लेषण उपकरण",
        "diag-form-sub": "telemetry इनपुट मानों को एडजस्ट करें और मशीन लर्निंग मॉडल द्वारा तत्काल परिणाम प्राप्त करें",
        "diag-pipe-label": "पाइप आईडी से लोड करें:",
        "diag-pipe-placeholder": "-- इंदौर पाइपलाइन डेटासेट से सेगमेंट चुनें --",
        "diag-flow-lbl": "प्रवाह दर (L/s)",
        "diag-temp-lbl": "तापमान (°C)",
        "diag-vib-lbl": "कंपन (mm/s)",
        "diag-rpm-lbl": "पंप RPM",
        "diag-hours-lbl": "परिचालन घंटे",
        "diag-lat-lbl": "अक्षांश",
        "diag-lon-lbl": "देशांतर",
        "diag-zone-lbl": "ज़ोन कोड",
        "diag-run-btn": "विफलता जोखिम पूर्वानुमान चलाएं",
        "diag-result-title": "मशीन लर्निंग पूर्वानुमान परिणाम",
        "badge-safe": "सुरक्षित",
        "diag-leak-gauge": "अनुमानित रिसाव जोखिम (Leakage Risk)",
        "diag-leak-label": "विफलता जोखिम",
        "diag-pressure-gauge": "अनुमानित पाइपलाइन दबाव (Pressure)",
        "diag-pressure-label": "दबाव",
        "diag-rec-title": "सुरक्षात्मक रखरखाव अनुशंसाएं:",
        "diag-rec-placeholder": "मॉडल चलाने के बाद अनुशंसाएं यहाँ दिखाई देंगी।",
        // Maintenance
        "maint-header": "प्राथमिकता-वार रखरखाव अनुसूची (Priority Actions)",
        "maint-sub": "उपकरण के wear factor, thermal stress और ML रिसाव जोखिम के आधार पर सुझाई गई गतिविधियाँ",
        "maint-critical": "गंभीर (सक्रिय विफलताएँ)",
        "maint-high": "उच्च जोखिम (जोखिम > 40%)",
        "maint-scheduled": "अनुसूचित रखरखाव (Wear > 0.8)",
        "maint-empty-critical": "सभी खंड सामान्य रूप से कार्य कर रहे हैं।",
        "maint-empty-high": "कोई उच्च जोखिम खंड नहीं है।",
        "maint-empty-sched": "कोई अनुसूचित निरीक्षण आवश्यक नहीं।",
        // Settings
        "settings-email-title": "अलर्ट ईमेल कॉन्फ़िगरेशन",
        "settings-email-sub": "रिसाव या विसंगति घटनाओं के लिए अलर्ट प्राप्त करने हेतु ईमेल पता सेट करें",
        "settings-alert-email-lbl": "प्राधिकरण अलर्ट ईमेल",
        "settings-alert-email-help": "जब भी कोई गंभीर विसंगति या रिसाव का पता चलता है, इस ईमेल पर अलर्ट भेजा जाएगा",
        "settings-save-btn": "सेटिंग्स सहेजें",
        "settings-test-btn": "परीक्षण ईमेल भेजें",
        "settings-thresh-title": "विसंगति अलार्म थ्रेशोल्ड",
        "settings-thresh-sub": "रीयल-टाइम विश्लेषण के दौरान अलार्म ट्रिगर करने की सीमाएँ निर्धारित करें",
        "settings-thresh-leak": "विफलता संभावना थ्रेशोल्ड",
        "settings-thresh-press-low": "न्यूनतम दबाव अलार्म थ्रेशोल्ड",
        "settings-thresh-press-high": "अधिकतम दबाव अलार्म थ्रेशोल्ड",
        // Report Modal
        "modal-report-title": "PDF रिपोर्ट विकल्प",
        "modal-scope-lbl": "रिपोर्ट का दायरा",
        "modal-scope-bulk": "बल्क ग्रिड / ज़ोन",
        "modal-scope-single": "विशेष पाइप",
        "modal-zone-lbl": "ज़ोन कार्यालय चुनें:",
        "modal-pipe-lbl": "पाइप आईडी चुनें:",
        "modal-pipe-placeholder": "-- पाइपलाइन खंड चुनें --",
        "modal-time-lbl": "समय अवधि फ़िल्टर:",
        "modal-cancel": "रद्द करें",
        "modal-download": "PDF डाउनलोड करें"
    },
    en: {
        // Sidebar & Brand
        "brand-name": "Water Works Department",
        "brand-sub": "Indore Municipal Corporation",
        "nav-dashboard": "Main Dashboard (Monitor)",
        "nav-gis": "GIS Pipeline Network",
        "nav-predict": "Failure Diagnostics",
        "nav-maintenance": "Maintenance Recommendations",
        "nav-settings": "Alarm Settings",
        "status-text": "System Live Monitor",
        // Header
        "title-main": "Smart Water Grid Control Center",
        "title-sub": "Indore Water Supply Network Management System",
        "label-zone": "Authorized Zone:",
        "option-all-zones": "-- All Indore Zone Offices --",
        "btn-pdf": "Download PDF Report",
        "btn-csv": "Export CSV Data",
        "role-employee": "Local Employee",
        "role-admin": "Administrator",
        // Login Modal
        "login-title": "Administrator Login",
        "login-user-lbl": "Username",
        "login-pass-lbl": "Password",
        "login-cancel": "Cancel",
        "login-submit": "Log In",
        // KPI Cards
        "kpi-total-pipes-lbl": "Total Pipeline Segments",
        "kpi-active-leaks-lbl": "Active Leaks",
        "kpi-high-risk-lbl": "High-Risk Segments",
        "kpi-avg-pressure-lbl": "Avg Water Pressure",
        "sub-total": "Total Monitored",
        "sub-active": "Immediate Action Required",
        "sub-high": "Failure Risk > 40%",
        "sub-pressure": "Grid Average Value",
        // Charts
        "chart-pressure-flow-title": "Pipeline Pressure & Flow Rate (Telemetry Analysis)",
        "chart-pressure-flow-tag": "Historical & Real-time Trend",
        "chart-pressure-flow-info": "This chart displays water pressure (blue line, left axis) and flow rate (purple line, right axis) for 20 Indore pipeline segments. A sudden pressure drop with a flow rate surge indicates a pipe burst or leakage anomaly. The Random Forest models use this correlation for real-time predictions.",
        "chart-ward-title": "Ward-wise Active Failure Distribution",
        "chart-ward-tag": "Leak Frequencies",
        "chart-ward-info": "This chart shows the distribution of active leak frequencies (Leakage_Flag = 1) across administrative wards. It highlights wards with aging infrastructure (hotspots), helping engineers prioritize localized pipeline replacement schemes.",
        "chart-scatter-title": "Pressure vs Flow Cluster Analysis",
        "chart-scatter-tag": "Anomaly Clusters",
        "chart-scatter-info": "This scatter chart plots flow rate (X-axis) vs water pressure (Y-axis) for each pipeline segment. Standard operational pipes cluster in a specific hydraulic zone. Off-cluster scatter points indicate anomalies like joint failure, clogging, or leakages.",
        "btn-guide": "Guide",
        // Alerts Feed
        "alerts-feed-title": "Real-time Anomaly & Leak Alarm Logs",
        "alerts-feed-sub": "Alarms automatically detected by sensor simulation",
        "alerts-empty": "System operating normally. No active alarms.",
        // GIS Map
        "gis-legend-title": "Pipeline Indicators",
        "gis-legend-normal": "Normal Operating Segment",
        "gis-legend-medium": "Medium Risk (Risk Score > 20)",
        "gis-legend-leak": "Active Failure/Leakage Segment",
        "gis-filter-title": "Pipeline Filter Controls",
        "gis-filter-normal": "Show Normal Pipelines",
        "gis-filter-high": "Show High-Risk Pipelines",
        "gis-filter-leak": "Show Active Leakages",
        "gis-search-title": "Search Ward/Pipe ID",
        "gis-search-placeholder": "Search (e.g. IND-PIPE)...",
        "map-btn-street": "Street Map",
        "map-btn-satellite": "Satellite View",
        // Diagnostics
        "diag-form-title": "AI-Based Failure Analysis Tool",
        "diag-form-sub": "Adjust telemetry input values and get instant results from Machine Learning models",
        "diag-pipe-label": "Load from Pipe ID:",
        "diag-pipe-placeholder": "-- Select segment from Indore Pipeline Dataset --",
        "diag-flow-lbl": "Flow Rate (L/s)",
        "diag-temp-lbl": "Temperature (°C)",
        "diag-vib-lbl": "Vibration (mm/s)",
        "diag-rpm-lbl": "Pump RPM",
        "diag-hours-lbl": "Operational Hours",
        "diag-lat-lbl": "Latitude",
        "diag-lon-lbl": "Longitude",
        "diag-zone-lbl": "Zone Code",
        "diag-run-btn": "Run Failure Risk Prediction",
        "diag-result-title": "Machine Learning Prediction Results",
        "badge-safe": "Safe",
        "diag-leak-gauge": "Estimated Leakage Risk",
        "diag-leak-label": "Failure Risk",
        "diag-pressure-gauge": "Estimated Pipeline Pressure",
        "diag-pressure-label": "Pressure",
        "diag-rec-title": "Preventive Maintenance Recommendations:",
        "diag-rec-placeholder": "Recommendations will appear here after running the model.",
        // Maintenance
        "maint-header": "Priority-wise Maintenance Schedule (Priority Actions)",
        "maint-sub": "Suggested activities based on equipment wear factor, thermal stress and ML leakage risk",
        "maint-critical": "Critical (Active Failures)",
        "maint-high": "High Risk (Risk > 40%)",
        "maint-scheduled": "Scheduled Maintenance (Wear > 0.8)",
        "maint-empty-critical": "All segments operating normally.",
        "maint-empty-high": "No high-risk segments.",
        "maint-empty-sched": "No scheduled inspections required.",
        // Settings
        "settings-email-title": "Alert Email Configuration",
        "settings-email-sub": "Set the email address to receive alerts for leakage or anomaly events",
        "settings-alert-email-lbl": "Authority Alert Email",
        "settings-alert-email-help": "Whenever a critical anomaly or leakage is detected, an alert will be sent to this email",
        "settings-save-btn": "Save Settings",
        "settings-test-btn": "Send Test Email",
        "settings-thresh-title": "Anomaly Alarm Thresholds",
        "settings-thresh-sub": "Set the threshold limits for triggering alarms during real-time analysis",
        "settings-thresh-leak": "Failure Probability Threshold",
        "settings-thresh-press-low": "Low Pressure Alarm Threshold",
        "settings-thresh-press-high": "High Pressure Alarm Threshold",
        // Report Modal
        "modal-report-title": "PDF Report Options",
        "modal-scope-lbl": "Report Scope",
        "modal-scope-bulk": "Bulk Grid / Zone",
        "modal-scope-single": "Particular Pipe",
        "modal-zone-lbl": "Select Zone Office:",
        "modal-pipe-lbl": "Select Pipe ID:",
        "modal-pipe-placeholder": "-- Select Pipeline Segment --",
        "modal-time-lbl": "Time Period Filter:",
        "modal-cancel": "Cancel",
        "modal-download": "Download PDF"
    }
};

document.addEventListener("DOMContentLoaded", () => {
    initApp();
});

function initApp() {
    initTheme();
    setupThemeToggle();
    setupLanguageToggle();
    setupRoleManagement();
    
    setupTabNavigation();
    setupFilters();
    loadDashboardData();
    setupDiagnostics();
    setupSettings();
    setupReportModal();
    
    applyTranslations();

    // Poll live alerts feed every 5 seconds
    loadLiveAlerts();
    setInterval(loadLiveAlerts, 5000);
}

// ============================================================
// THEME AND LANGUAGE HELPERS
// ============================================================
function initTheme() {
    const icon = document.querySelector("#theme-toggle-btn i");
    if (currentTheme === "dark") {
        document.body.classList.add("dark-theme");
        if (icon) icon.className = "fa-solid fa-sun";
    } else {
        document.body.classList.remove("dark-theme");
        if (icon) icon.className = "fa-solid fa-moon";
    }
}

function setupThemeToggle() {
    const btn = document.getElementById("theme-toggle-btn");
    if (btn) {
        btn.addEventListener("click", () => {
            currentTheme = currentTheme === "light" ? "dark" : "light";
            localStorage.setItem("theme", currentTheme);
            initTheme();
        });
    }
}

function setupLanguageToggle() {
    const btn = document.getElementById("lang-toggle-btn");
    if (btn) {
        btn.addEventListener("click", () => {
            currentLanguage = currentLanguage === "hi" ? "en" : "hi";
            localStorage.setItem("lang", currentLanguage);
            applyTranslations();
            
            // Re-trigger stats rendering to translate chart titles/legends if chart exists
            const activeTab = document.querySelector(".tab-content.active");
            if (activeTab && activeTab.id === "dashboard-tab") {
                loadDashboardData();
            }
        });
    }
}

function applyTranslations() {
    const trans = translations[currentLanguage];
    document.querySelectorAll("[data-i18n]").forEach(elem => {
        const key = elem.getAttribute("data-i18n");
        if (trans[key]) {
            elem.innerText = trans[key];
        }
    });
    
    // Update active tab title
    updatePageTitle();
    
    // Update Language Switcher Button Text
    const langBtnSpan = document.querySelector("#lang-toggle-btn span");
    if (langBtnSpan) {
        langBtnSpan.innerText = currentLanguage === "hi" ? "EN" : "हिं";
    }
    
    // Update dropdown placeholder and buttons
    const select = document.getElementById("authority-filter");
    if (select && select.options.length > 0) {
        select.options[0].text = trans["option-all-zones"];
    }
}

function updatePageTitle() {
    const activeTab = document.querySelector(".tab-content.active");
    if (!activeTab) return;
    const targetTab = activeTab.id;
    const pageTitle = document.getElementById("page-title");
    if (!pageTitle) return;
    
    if (targetTab === "dashboard-tab") {
        pageTitle.innerText = currentLanguage === "hi" ? "मुख्य डैशबोर्ड (Monitor)" : "Main Dashboard (Monitor)";
    } else if (targetTab === "gis-tab") {
        pageTitle.innerText = currentLanguage === "hi" ? "GIS पाइपलाइन नेटवर्क" : "GIS Pipeline Network";
    } else if (targetTab === "predict-tab") {
        pageTitle.innerText = currentLanguage === "hi" ? "विफलता पूर्वानुमान (Diagnostics)" : "Failure Diagnostics";
    } else if (targetTab === "maintenance-tab") {
        pageTitle.innerText = currentLanguage === "hi" ? "अनुरक्षण अनुशंसाएं" : "Maintenance Recommendations";
    } else if (targetTab === "settings-tab") {
        pageTitle.innerText = currentLanguage === "hi" ? "अलार्म सेटिंग्स" : "Alarm Settings";
    }
}

// ============================================================
// ROLE & LOGIN ACCESS CONTROL
// ============================================================
function showLoginModal() {
    document.getElementById("login-modal").classList.add("active");
    document.getElementById("login-error-msg").style.display = "none";
}

function hideLoginModal() {
    document.getElementById("login-modal").classList.remove("active");
    document.getElementById("admin-login-form").reset();
}

function setupRoleManagement() {
    const roleBtn = document.getElementById("role-badge-btn");
    const loginModalClose = document.getElementById("login-modal-close-btn");
    const loginCancel = document.getElementById("login-btn-cancel");
    const loginSubmit = document.getElementById("login-btn-submit");
    const loginForm = document.getElementById("admin-login-form");
    
    if (roleBtn) {
        roleBtn.addEventListener("click", () => {
            if (currentUserRole === "admin") {
                logoutAdmin();
            } else {
                showLoginModal();
            }
        });
    }
    
    if (loginModalClose) loginModalClose.addEventListener("click", hideLoginModal);
    if (loginCancel) loginCancel.addEventListener("click", hideLoginModal);
    
    if (loginForm) {
        loginForm.addEventListener("submit", (e) => {
            e.preventDefault();
            performLogin();
        });
    }
    if (loginSubmit) loginSubmit.addEventListener("click", performLogin);
    
    if (adminToken) {
        verifyAdminSession();
    } else {
        updateRoleUI("employee");
    }
}

function performLogin() {
    const userField = document.getElementById("login-username").value;
    const passField = document.getElementById("login-password").value;
    const errorMsg = document.getElementById("login-error-msg");
    
    fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: userField, password: passField })
    })
    .then(res => {
        if (!res.ok) {
            return res.json().then(data => { throw new Error(data.error || "Login failed"); });
        }
        return res.json();
    })
    .then(data => {
        adminToken = data.token;
        localStorage.setItem("adminToken", adminToken);
        updateRoleUI("admin");
        hideLoginModal();
        
        // If we were blocked from navigating, go ahead and select settings-tab
        const settingsItem = document.getElementById("nav-settings-item");
        if (settingsItem) settingsItem.click();
    })
    .catch(err => {
        errorMsg.innerText = err.message;
        errorMsg.style.display = "block";
    });
}

function verifyAdminSession() {
    fetch('/api/alerts/config', {
        headers: { 'Authorization': `Bearer ${adminToken}` }
    })
    .then(res => {
        if (res.ok) {
            updateRoleUI("admin");
        } else {
            logoutAdmin();
        }
    })
    .catch(() => {
        logoutAdmin();
    });
}

function logoutAdmin() {
    if (adminToken) {
        fetch('/api/logout', {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${adminToken}` }
        }).finally(() => {
            adminToken = "";
            localStorage.removeItem("adminToken");
            updateRoleUI("employee");
            
            // Redirect to dashboard tab if currently in settings
            const activeTab = document.querySelector(".tab-content.active");
            if (activeTab && activeTab.id === "settings-tab") {
                const dashboardItem = document.querySelector('[data-target="dashboard-tab"]');
                if (dashboardItem) dashboardItem.click();
            }
        });
    } else {
        updateRoleUI("employee");
    }
}

function updateRoleUI(role) {
    currentUserRole = role;
    const roleBtn = document.getElementById("role-badge-btn");
    const roleSpan = document.getElementById("current-role-text");
    const lockIcon = document.getElementById("settings-lock-icon");
    const settingsItem = document.getElementById("nav-settings-item");
    
    if (role === "admin") {
        if (roleBtn) roleBtn.className = "role-badge admin";
        if (roleSpan) roleSpan.innerText = currentLanguage === "hi" ? "प्रशासक (Admin)" : "Administrator";
        if (lockIcon) lockIcon.style.display = "none";
        if (settingsItem) settingsItem.classList.remove("locked");
    } else {
        if (roleBtn) roleBtn.className = "role-badge employee";
        if (roleSpan) roleSpan.innerText = currentLanguage === "hi" ? "स्थानीय कर्मचारी" : "Local Employee";
        if (lockIcon) lockIcon.style.display = "inline-block";
        if (settingsItem) settingsItem.classList.add("locked");
    }
}

// ============================================================
// TAB NAVIGATION
// ============================================================
function setupTabNavigation() {
    const navItems = document.querySelectorAll(".nav-item");
    const tabContents = document.querySelectorAll(".tab-content");

    navItems.forEach(item => {
        item.addEventListener("click", (e) => {
            e.preventDefault();
            
            const targetTab = item.getAttribute("data-target");
            if (targetTab === "settings-tab" && currentUserRole !== 'admin') {
                showLoginModal();
                return;
            }
            
            // Remove active class
            navItems.forEach(nav => nav.classList.remove("active"));
            tabContents.forEach(tab => tab.classList.remove("active"));
            
            // Add active class
            item.classList.add("active");
            document.getElementById(targetTab).classList.add("active");
            
            // Update Page title dynamically (handles i18n)
            updatePageTitle();
            
            if (targetTab === "dashboard-tab") {
                loadDashboardData();
            } else if (targetTab === "gis-tab") {
                initGisMap();
            } else if (targetTab === "predict-tab") {
                // No extra load needed
            } else if (targetTab === "maintenance-tab") {
                loadMaintenanceRecommendations();
            } else if (targetTab === "settings-tab") {
                // Settings is auto loaded from state
            }
        });
    });
}

// ============================================================
// GLOBAL FILTERS & REPORTS
// ============================================================
function setupFilters() {
    const authorityFilter = document.getElementById("authority-filter");
    const btnReport = document.getElementById("btn-csv-report");
    
    if (authorityFilter) {
        authorityFilter.addEventListener("change", (e) => {
            currentZoneOffice = e.target.value;
            
            // Refresh active tab
            const activeTab = document.querySelector(".tab-content.active");
            if (activeTab) {
                const activeId = activeTab.id;
                if (activeId === "dashboard-tab") {
                    loadDashboardData();
                } else if (activeId === "gis-tab") {
                    loadGisData();
                } else if (activeId === "maintenance-tab") {
                    loadMaintenanceRecommendations();
                }
            }
        });
    }

    if (btnReport) {
        btnReport.addEventListener("click", () => {
            window.location.href = `/api/report?zone_office=${encodeURIComponent(currentZoneOffice)}`;
        });
    }
}

// ============================================================
// TAB 1: DASHBOARD DATA & CHARTS
// ============================================================
function loadDashboardData() {
    fetch(`/api/stats?zone_office=${encodeURIComponent(currentZoneOffice)}`)
        .then(res => res.json())
        .then(data => {
            // Populate Dropdown if not already populated
            populateAuthorityDropdown(data.authorities);
            
            // Populate KPIs
            document.getElementById("kpi-total-pipes").innerText = data.total_pipes;
            document.getElementById("kpi-active-leaks").innerText = data.active_leaks;
            document.getElementById("kpi-high-risk").innerText = data.high_risk_pipes;
            document.getElementById("kpi-avg-pressure").innerText = `${data.avg_pressure} PSI`;
            
            // Build Charts
            buildTrendChart(data.trend_data);
            buildWardChart(data.ward_distribution);
            buildRiskScatterChart(data.trend_data);
        })
        .catch(err => console.error("Error loading stats:", err));
}

function populateAuthorityDropdown(authorities) {
    const filter = document.getElementById("authority-filter");
    if (filter.options.length > 1) return; // Already populated
    
    authorities.forEach(auth => {
        const opt = document.createElement("option");
        opt.value = auth;
        opt.innerText = auth;
        filter.appendChild(opt);
    });
}

function buildTrendChart(trendData) {
    const ctx = document.getElementById("pressureFlowChart").getContext("2d");
    
    if (pressureFlowChart) {
        pressureFlowChart.destroy();
    }
    
    const labels = trendData.map(item => item.pipe_id.replace("IND-PIPE-", "#"));
    const pressures = trendData.map(item => item.pressure);
    const flowRates = trendData.map(item => item.flow_rate);
    
    const labelPressure = currentLanguage === 'hi' ? 'जल दबाव (Pressure PSI)' : 'Water Pressure (PSI)';
    const labelFlow = currentLanguage === 'hi' ? 'प्रवाह दर (Flow Rate L/s)' : 'Flow Rate (L/s)';
    const titlePressure = currentLanguage === 'hi' ? 'दबाव (Pressure PSI)' : 'Pressure (PSI)';
    const titleFlow = currentLanguage === 'hi' ? 'प्रवाह दर (Flow Rate L/s)' : 'Flow Rate (L/s)';
    
    const isDark = document.body.classList.contains('dark-theme');
    const gridColor = isDark ? '#1e2a3a' : '#e2e8f0';
    const tickColor = isDark ? '#94a3b8' : '#475569';
    const titleColor = isDark ? '#94a3b8' : '#475569';
    const legendColor = isDark ? '#e2e8f0' : '#1e293b';
    
    pressureFlowChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: labelPressure,
                    data: pressures,
                    borderColor: '#0ea5e9',
                    backgroundColor: 'rgba(14, 165, 233, 0.1)',
                    borderWidth: 2,
                    tension: 0.3,
                    yAxisID: 'y'
                },
                {
                    label: labelFlow,
                    data: flowRates,
                    borderColor: '#8b5cf6',
                    backgroundColor: 'rgba(139, 92, 246, 0.1)',
                    borderWidth: 2,
                    tension: 0.3,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    grid: { color: gridColor },
                    ticks: { color: tickColor }
                },
                y: {
                    position: 'left',
                    grid: { color: gridColor },
                    ticks: { color: tickColor },
                    title: { display: true, text: titlePressure, color: titleColor }
                },
                y1: {
                    position: 'right',
                    grid: { drawOnChartArea: false },
                    ticks: { color: tickColor },
                    title: { display: true, text: titleFlow, color: titleColor }
                }
            },
            plugins: {
                legend: { labels: { color: legendColor, font: { weight: '600' } } }
            }
        }
    });
}

function buildWardChart(wardDist) {
    const ctx = document.getElementById("wardFailureChart").getContext("2d");
    if (wardFailureChart) {
        wardFailureChart.destroy();
    }
    
    const labels = Object.keys(wardDist);
    const data = Object.values(wardDist);
    
    const labelLeaks = currentLanguage === 'hi' ? 'कुल रिसाव दर्ज' : 'Total Leaks Recorded';
    
    const isDark = document.body.classList.contains('dark-theme');
    const gridColor = isDark ? '#1e2a3a' : '#e2e8f0';
    const tickColor = isDark ? '#94a3b8' : '#475569';
    
    wardFailureChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: labelLeaks,
                data: data,
                backgroundColor: 'rgba(239, 68, 68, 0.7)',
                borderColor: '#ef4444',
                borderWidth: 1.5,
                borderRadius: 4
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    grid: { color: gridColor },
                    ticks: { color: tickColor, stepSize: 1 }
                },
                y: {
                    grid: { color: gridColor },
                    ticks: { color: tickColor }
                }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
}

function buildRiskScatterChart(trendData) {
    const ctx = document.getElementById("riskScatterChart").getContext("2d");
    if (riskScatterChart) {
        riskScatterChart.destroy();
    }
    
    const points = trendData.map(item => ({
        x: item.flow_rate,
        y: item.pressure,
        label: item.pipe_id
    }));
    
    const datasetLabel = currentLanguage === 'hi' ? 'प्रवाह बनाम दबाव' : 'Flow vs Pressure';
    const labelX = currentLanguage === 'hi' ? 'प्रवाह दर (L/s)' : 'Flow Rate (L/s)';
    const labelY = currentLanguage === 'hi' ? 'जल दबाव (PSI)' : 'Water Pressure (PSI)';
    
    const isDark = document.body.classList.contains('dark-theme');
    const gridColor = isDark ? '#1e2a3a' : '#e2e8f0';
    const tickColor = isDark ? '#94a3b8' : '#475569';
    const titleColor = isDark ? '#94a3b8' : '#475569';
    
    riskScatterChart = new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [{
                label: datasetLabel,
                data: points,
                backgroundColor: '#f59e0b',
                pointRadius: 6,
                pointHoverRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    title: { display: true, text: labelX, color: titleColor },
                    grid: { color: gridColor },
                    ticks: { color: tickColor }
                },
                y: {
                    title: { display: true, text: labelY, color: titleColor },
                    grid: { color: gridColor },
                    ticks: { color: tickColor }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: (context) => {
                            const p = context.raw;
                            return `${p.label}: Flow=${p.x} L/s, Pressure=${p.y} PSI`;
                        }
                    }
                },
                legend: { display: false }
            }
        }
    });
}

function loadLiveAlerts() {
    const t = translations[currentLanguage];
    fetch('/api/alerts/live')
        .then(res => res.json())
        .then(alerts => {
            const feed = document.getElementById("live-alerts-feed");
            if (alerts.length === 0) {
                feed.innerHTML = `<div class="alert-empty">${t['alerts-empty']}</div>`;
                return;
            }
            
            feed.innerHTML = "";
            alerts.forEach(alt => {
                const lblAlertSent = currentLanguage === 'hi' ? 'अलर्ट प्रेषित' : 'Email Sent';
                const lblSimAlert = currentLanguage === 'hi' ? 'सिमुलेशन अलर्ट' : 'Simulation Alert';
                const lblPipeFailure = currentLanguage === 'hi' ? 'पाइप विफलता संकेत' : 'Pipe Failure Signal';
                const lblZone = currentLanguage === 'hi' ? 'क्षेत्र' : 'Zone';
                const lblAlarmReason = currentLanguage === 'hi' ? 'अलार्म कारण' : 'Alarm Reason';
                const lblLeakProb = currentLanguage === 'hi' ? 'लीक संभावना' : 'Leak Prob';
                const lblPressure = currentLanguage === 'hi' ? 'दबाव' : 'Pressure';
                const lblFlow = currentLanguage === 'hi' ? 'प्रवाह' : 'Flow';
                
                const mailStatus = alt.email_sent 
                    ? `<span class="alert-email-indicator sent"><i class="fa-solid fa-circle-check"></i> ${lblAlertSent}</span>` 
                    : `<span class="alert-email-indicator failed"><i class="fa-solid fa-triangle-exclamation"></i> ${lblSimAlert} (${alt.log.split(".")[0]})</span>`;
                
                const item = document.createElement("div");
                item.className = "alert-item";
                item.innerHTML = `
                    <div class="alert-item-content">
                        <h5>⚠️ ${lblPipeFailure}: Pipe ${alt.pipe_id}</h5>
                        <p>${lblZone}: ${alt.zone_name} (${alt.ward_name}). ${lblAlarmReason}: ${alt.reasons.join(", ")}</p>
                        <div class="alert-badge-row">
                            <span class="badge-alert badge-red">${lblLeakProb}: ${(alt.leak_prob * 100).toFixed(1)}%</span>
                            <span class="badge-alert badge-blue">${lblPressure}: ${alt.pressure.toFixed(1)} PSI</span>
                            <span class="badge-alert badge-gold">${lblFlow}: ${alt.flow_rate.toFixed(1)} L/s</span>
                        </div>
                    </div>
                    <div class="alert-item-actions">
                        <span class="alert-time">${alt.timestamp.split(" ")[1]}</span>
                        <div>${mailStatus}</div>
                    </div>
                `;
                feed.appendChild(item);
            });
        })
        .catch(err => console.error("Error loading alerts:", err));
}

// ============================================================
// TAB 2: GIS VISUALIZATION (POLYLINES + OVERLAYS)
// ============================================================
// GIS Map tile layers
let streetLayer = null;
let satelliteLayer = null;

function initGisMap() {
    if (map) return; // Map already loaded
    
    // Center map on Indore with better zoom
    map = L.map('gis-map').setView([22.7196, 75.8577], 13);
    
    // OpenStreetMap standard tiles (street view with roads/buildings)
    streetLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
        maxZoom: 19
    }).addTo(map);
    
    // Esri World Imagery (satellite view)
    satelliteLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
        attribution: 'Tiles &copy; Esri',
        maxZoom: 18
    });
    
    pipeMarkersLayer = L.layerGroup().addTo(map);
    
    // Load data and draw polylines
    loadGisData();
    setupMapSearch();
    setupLayerControls();
    setupMapLayerToggle();
}

function setupMapLayerToggle() {
    const layerBtns = document.querySelectorAll('.map-layer-btn');
    layerBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            layerBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            const layerType = btn.getAttribute('data-layer');
            if (layerType === 'satellite') {
                map.removeLayer(streetLayer);
                map.addLayer(satelliteLayer);
            } else {
                map.removeLayer(satelliteLayer);
                map.addLayer(streetLayer);
            }
        });
    });
}

function setupLayerControls() {
    const showNormal = document.getElementById("layer-normal");
    const showHighRisk = document.getElementById("layer-high-risk");
    const showLeakage = document.getElementById("layer-leakage");
    
    [showNormal, showHighRisk, showLeakage].forEach(box => {
        box.addEventListener("change", () => {
            loadGisData(); // Redraw layers matching checks
        });
    });
}

function loadGisData() {
    if (!pipeMarkersLayer) return;
    
    pipeMarkersLayer.clearLayers();
    
    fetch(`/api/pipes?zone_office=${encodeURIComponent(currentZoneOffice)}`)
        .then(res => res.json())
        .then(pipes => {
            allPipesData = pipes;
            populateGisSidebar(pipes);
            
            // Group coordinates by Zone_Road (road segments) to draw continuous Polylines
            const roads = {};
            pipes.forEach(pipe => {
                const roadName = pipe.road || "Main Road Segment";
                if (!roads[roadName]) {
                    roads[roadName] = {
                        coordinates: [],
                        status: 'normal',
                        pipes: []
                    };
                }
                roads[roadName].coordinates.push([pipe.latitude, pipe.longitude]);
                roads[roadName].pipes.push(pipe);
                
                // Track highest severity
                if (pipe.status === 'leakage') {
                    roads[roadName].status = 'leakage';
                } else if (pipe.status === 'high_risk' && roads[roadName].status !== 'leakage') {
                    roads[roadName].status = 'high_risk';
                }
            });
            
            // Sort coordinates within each road to form proper line segments (fix zigzag clusters)
            Object.keys(roads).forEach(roadName => {
                roads[roadName].coordinates.sort((a, b) => {
                    if (a[0] !== b[0]) return a[0] - b[0];
                    return a[1] - b[1];
                });
            });
            
            // Draw polylines
            Object.keys(roads).forEach(roadName => {
                const roadData = roads[roadName];
                
                // Polyline requires at least 2 points
                if (roadData.coordinates.length < 2) {
                    // Inject close offset to draw a line segment
                    roadData.coordinates.push([
                        roadData.coordinates[0][0] + 0.0003,
                        roadData.coordinates[0][1] + 0.0003
                    ]);
                }
                
                let color = '#10b981'; // Green (Normal)
                if (roadData.status === 'leakage') {
                    color = '#ef4444'; // Red
                } else if (roadData.status === 'high_risk') {
                    color = '#f59e0b'; // Orange
                }
                
                const polyline = L.polyline(roadData.coordinates, {
                    color: color,
                    weight: 5,
                    opacity: 0.85
                });
                
                const showNormal = document.getElementById("layer-normal").checked;
                const showHighRisk = document.getElementById("layer-high-risk").checked;
                const showLeakage = document.getElementById("layer-leakage").checked;
                
                let shouldShow = false;
                if (roadData.status === 'normal' && showNormal) shouldShow = true;
                if (roadData.status === 'high_risk' && showHighRisk) shouldShow = true;
                if (roadData.status === 'leakage' && showLeakage) shouldShow = true;
                
                if (shouldShow) {
                    const avgPress = (roadData.pipes.reduce((a, b) => a + b.pressure, 0) / roadData.pipes.length).toFixed(1);
                    const avgFlow = (roadData.pipes.reduce((a, b) => a + b.flow_rate, 0) / roadData.pipes.length).toFixed(1);
                    
                    const lblRoadSeg = currentLanguage === 'hi' ? 'मार्ग खंड' : 'Road Segment';
                    const lblZoneOff = currentLanguage === 'hi' ? 'ज़ोन कार्यालय' : 'Zone Office';
                    const lblPipeCount = currentLanguage === 'hi' ? 'पाइप संख्या' : 'Pipe Count';
                    const lblSegments = currentLanguage === 'hi' ? 'खंड' : 'segments';
                    const lblPressure = currentLanguage === 'hi' ? 'दबाव' : 'Pressure';
                    const lblAvgFlow = currentLanguage === 'hi' ? 'औसत प्रवाह' : 'Avg Flow';
                    const lblStatus = currentLanguage === 'hi' ? 'स्थिति' : 'Status';
                    
                    const popupContent = `
                        <div class="map-popup-card">
                            <h4>${lblRoadSeg}: ${roadName}</h4>
                            <p><strong>${lblZoneOff}:</strong> ${roadData.pipes[0].zone_name}</p>
                            <p><strong>${lblPipeCount}:</strong> ${roadData.pipes.length} ${lblSegments}</p>
                            <p><strong>${lblPressure}:</strong> ${avgPress} PSI</p>
                            <p><strong>${lblAvgFlow}:</strong> ${avgFlow} L/s</p>
                            <p><strong>${lblStatus}:</strong> <span style="color:${color}; font-weight:bold;">${roadData.status.toUpperCase()}</span></p>
                        </div>
                    `;
                    
                    polyline.bindPopup(popupContent);
                    pipeMarkersLayer.addLayer(polyline);
                }
                
                // Link polyline markers references
                roadData.pipes.forEach(p => {
                    p._marker = polyline; 
                });
            });
            
            // Plot specific node markers for active leakages
            pipes.forEach(pipe => {
                if (pipe.status === 'leakage' && document.getElementById("layer-leakage").checked) {
                    const leakMarker = L.circleMarker([pipe.latitude, pipe.longitude], {
                        radius: 6,
                        fillColor: '#ef4444',
                        color: '#ffffff',
                        weight: 2,
                        opacity: 1,
                        fillOpacity: 1
                    }).addTo(pipeMarkersLayer);
                    
                    const lblLeakNode = currentLanguage === 'hi' ? '⚠️ विफलता बिंदु (Leak Node)' : '⚠️ Leak Node';
                    const lblPipeId = currentLanguage === 'hi' ? 'पाइप आईडी' : 'Pipe ID';
                    const lblWard = currentLanguage === 'hi' ? 'वार्ड' : 'Ward';
                    const lblPressLeak = currentLanguage === 'hi' ? 'दबाव' : 'Pressure';
                    const lblFlowLeak = currentLanguage === 'hi' ? 'प्रवाह दर' : 'Flow Rate';
                    const lblRunAnalysis = currentLanguage === 'hi' ? '🔬 विफलता विश्लेषण चलाएं' : '🔬 Run Failure Analysis';
                    
                    const popupContent = `
                        <div class="map-popup-card">
                            <h4 style="color:#ef4444;">${lblLeakNode}</h4>
                            <p><strong>${lblPipeId}:</strong> ${pipe.pipe_id}</p>
                            <p><strong>${lblWard}:</strong> ${pipe.ward_name}</p>
                            <p><strong>${lblPressLeak}:</strong> ${pipe.pressure} PSI</p>
                            <p><strong>${lblFlowLeak}:</strong> ${pipe.flow_rate} L/s</p>
                            <p style="margin-top: 6px;"><a href="#" onclick="loadPipeInDiagnostics('${pipe.pipe_id}')" style="color:#0F2E59; font-weight:600; text-decoration:none;">${lblRunAnalysis}</a></p>
                        </div>
                    `;
                    leakMarker.bindPopup(popupContent);
                    pipe._marker = leakMarker; // Target node details directly
                }
            });
        })
        .catch(err => console.error("Error loading map coordinates:", err));
}

function populateGisSidebar(pipes) {
    const list = document.getElementById("map-pipes-list");
    list.innerHTML = "";
    
    pipes.slice(0, 50).forEach(pipe => {
        let dotColor = 'dot-green';
        if (pipe.status === 'leakage') dotColor = 'dot-red';
        else if (pipe.status === 'high_risk') dotColor = 'dot-orange';
        
        const item = document.createElement("div");
        item.className = "pipe-list-item";
        const lblZone = currentLanguage === 'hi' ? 'ज़ोन' : 'Zone';
        item.innerHTML = `
            <div class="pipe-item-header">
                <span>${pipe.pipe_id}</span>
                <span class="pipe-item-status-dot ${dotColor}"></span>
            </div>
            <div class="sub-text">${lblZone}: ${pipe.zone_name} (${pipe.pressure} PSI)</div>
        `;
        
        item.addEventListener("click", () => {
            document.querySelectorAll(".pipe-list-item").forEach(i => i.classList.remove("active"));
            item.classList.add("active");
            
            map.setView([pipe.latitude, pipe.longitude], 15);
            pipe._marker.openPopup();
        });
        
        list.appendChild(item);
    });
}

function setupMapSearch() {
    const search = document.getElementById("map-search-input");
    search.addEventListener("input", (e) => {
        const query = e.target.value.toUpperCase();
        const filteredPipes = allPipesData.filter(p => 
            p.pipe_id.toUpperCase().includes(query) || 
            p.zone_name.toUpperCase().includes(query) ||
            p.road.toUpperCase().includes(query)
        );
        populateGisSidebar(filteredPipes);
    });
}

function loadPipeInDiagnostics(pipeId) {
    const pipe = allPipesData.find(p => p.pipe_id === pipeId);
    if (!pipe) return;
    
    // Switch Tab to diagnostics
    document.querySelector('[data-target="predict-tab"]').click();
    
    // Set template value and select dropdown
    const select = document.getElementById("diagnostics-pipe-template");
    select.value = pipeId;
    
    // Populate form values
    populateDiagnosticsSliders(pipe);
}

// ============================================================
// TAB 3: PREDICTIVE DIAGNOSTICS & SCENARIOS
// ============================================================
function setupDiagnostics() {
    // Sliders hooks
    const sliders = [
        { id: "flow", label: "val-flow" },
        { id: "temp", label: "val-temp" },
        { id: "vib", label: "val-vib" },
        { id: "rpm", label: "val-rpm" },
        { id: "hours", label: "val-hours" },
        { id: "lat", label: "val-lat", fixed: 3 },
        { id: "lon", label: "val-lon", fixed: 3 }
    ];
    
    sliders.forEach(s => {
        const slider = document.getElementById(`input-${s.id}`);
        const valLabel = document.getElementById(s.label);
        slider.addEventListener("input", (e) => {
            const val = parseFloat(e.target.value);
            valLabel.innerText = s.fixed ? val.toFixed(s.fixed) : val;
        });
    });
    
    // Load pipeline list in scenario template selector
    fetch('/api/pipes')
        .then(res => res.json())
        .then(pipes => {
            const select = document.getElementById("diagnostics-pipe-template");
            pipes.slice(0, 100).forEach(pipe => {
                const opt = document.createElement("option");
                opt.value = pipe.pipe_id;
                opt.innerText = `${pipe.pipe_id} - ${pipe.zone_name}`;
                select.appendChild(opt);
            });
            
            // Set template listener
            select.addEventListener("change", (e) => {
                const selectedPipeId = e.target.value;
                const pipe = pipes.find(p => p.pipe_id === selectedPipeId);
                if (pipe) populateDiagnosticsSliders(pipe);
            });
        });
        
    // Prediction trigger
    document.getElementById("btn-run-prediction").addEventListener("click", runModelPrediction);
}

function populateDiagnosticsSliders(pipe) {
    document.getElementById("input-flow").value = pipe.flow_rate;
    document.getElementById("val-flow").innerText = pipe.flow_rate;
    
    document.getElementById("input-temp").value = pipe.temperature;
    document.getElementById("val-temp").innerText = pipe.temperature;
    
    document.getElementById("input-vib").value = pipe.vibration;
    document.getElementById("val-vib").innerText = pipe.vibration.toFixed(1);
    
    document.getElementById("input-rpm").value = pipe.rpm;
    document.getElementById("val-rpm").innerText = pipe.rpm.toFixed(0);
    
    document.getElementById("input-hours").value = pipe.hours;
    document.getElementById("val-hours").innerText = pipe.hours;
    
    document.getElementById("input-lat").value = pipe.latitude;
    document.getElementById("val-lat").innerText = pipe.latitude.toFixed(3);
    
    document.getElementById("input-lon").value = pipe.longitude;
    document.getElementById("val-lon").innerText = pipe.longitude.toFixed(3);
}

function runModelPrediction() {
    const payload = {
        Flow_Rate: parseFloat(document.getElementById("input-flow").value),
        Temperature: parseFloat(document.getElementById("input-temp").value),
        Vibration: parseFloat(document.getElementById("input-vib").value),
        RPM: parseFloat(document.getElementById("input-rpm").value),
        Operational_Hours: parseFloat(document.getElementById("input-hours").value),
        Latitude: parseFloat(document.getElementById("input-lat").value),
        Longitude: parseFloat(document.getElementById("input-lon").value),
        Zone_Enc: parseInt(document.getElementById("input-zone-enc").value),
        Block_Enc: 1 // Baseline
    };
    
    fetch('/api/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    })
    .then(res => res.json())
    .then(outputs => {
        if (outputs.error) {
            alert("Prediction failed: " + outputs.error);
            return;
        }
        
        // Update circular progress dials matching government portal colors (green, amber, red)
        updateCircularProgress('leak-progress', outputs.leakage_probability, 'leak', '%');
        
        const pressurePercent = Math.min(100, Math.max(0, outputs.predicted_pressure)) / 100;
        updateCircularProgress('pressure-progress', pressurePercent, 'pressure', ' PSI', outputs.predicted_pressure.toFixed(1));
        
        // Severity Badge Update
        const severity = document.getElementById("severity-badge");
        severity.innerText = outputs.severity;
        severity.className = "badge"; // Reset classes
        if (outputs.severity === "High") {
            severity.classList.add("badge-danger");
        } else if (outputs.severity === "Medium") {
            severity.classList.add("badge-caution");
        } else {
            severity.classList.add("badge-safe");
        }
        
        // Populate recommendations list
        const recList = document.getElementById("diagnostic-rec-list");
        recList.innerHTML = "";
        outputs.recommendations.forEach(rec => {
            const li = document.createElement("li");
            li.innerText = rec;
            recList.appendChild(li);
        });
    })
    .catch(err => console.error("Error predicting:", err));
}

function updateCircularProgress(elementId, ratio, type, unit, rawVal = null) {
    const circularProgress = document.getElementById(elementId);
    const textVal = circularProgress.querySelector(".percentage-val");
    
    const displayVal = rawVal ? `${rawVal}${unit}` : `${(ratio * 100).toFixed(1)}${unit}`;
    textVal.innerText = displayVal;
    
    // Map colors to Government light theme (emerald, gold, crimson)
    let color = '#0ea5e9';
    if (type === 'leak') {
        if (ratio >= 0.70) color = '#ef4444'; // Red
        else if (ratio >= 0.40) color = '#f59e0b'; // Amber
        else color = '#10b981'; // Emerald
    } else {
        if (ratio < 0.45 || ratio > 0.75) color = '#ef4444';
        else color = '#10b981';
    }
    
    const deg = ratio * 360;
    const isDark = document.body.classList.contains('dark-theme');
    const ringBg = isDark ? '#1e293b' : '#f1f5f9';
    circularProgress.style.background = `conic-gradient(${color} 0deg, ${color} ${deg}deg, ${ringBg} ${deg}deg, ${ringBg} 360deg)`;
}

// ============================================================
// TAB 4: MAINTENANCE CARD RECOMMENDATIONS
// ============================================================
function loadMaintenanceRecommendations() {
    fetch(`/api/recommendations?zone_office=${encodeURIComponent(currentZoneOffice)}`)
        .then(res => res.json())
        .then(data => {
            populateMaintenanceColumn("critical-rec-list", data.critical, "critical");
            populateMaintenanceColumn("high-rec-list", data.high, "high");
            populateMaintenanceColumn("scheduled-rec-list", data.scheduled, "scheduled");
        })
        .catch(err => console.error("Error loading recommendations:", err));
}

function populateMaintenanceColumn(elementId, items, urgencyClass) {
    const list = document.getElementById(elementId);
    if (items.length === 0) {
        const emptyMsg = currentLanguage === 'hi' ? 'ज़ोन में कोई ट्रिगर नहीं है।' : 'No triggers in this zone.';
        list.innerHTML = `<div class="rec-card-empty">${emptyMsg}</div>`;
        return;
    }
    
    list.innerHTML = "";
    const lblRisk = currentLanguage === 'hi' ? 'जोखिम' : 'Risk';
    items.forEach(item => {
        const card = document.createElement("div");
        card.className = `rec-card ${urgencyClass}`;
        card.innerHTML = `
            <h5>${item.pipe_id}</h5>
            <div class="rec-card-meta">
                <span><i class="fa-solid fa-map-pin"></i> ${item.zone}</span>
                <span>${lblRisk}: ${item.risk_score}</span>
                <span>Wear: ${item.wear}</span>
            </div>
            <div class="rec-card-action">${item.action}</div>
        `;
        list.appendChild(card);
    });
}

// ============================================================
// TAB 5: ALERTS & CONFIGURATIONS (SMTP)
// ============================================================
function setupSettings() {
    // Load settings from config
    fetch('/api/alerts/config', {
        headers: { 'Authorization': `Bearer ${adminToken}` }
    })
        .then(res => {
            if (res.status === 401) {
                logoutAdmin();
                throw new Error("Unauthorized");
            }
            return res.json();
        })
        .then(cfg => {
            document.getElementById("alert_email").value = cfg.alert_email || "";
            
            // Sync thresholds sliders
            document.getElementById("thresh-leak").value = (cfg.leak_prob_threshold || 0.70) * 100;
            document.getElementById("lbl-thresh-leak").innerText = `${((cfg.leak_prob_threshold || 0.70) * 100).toFixed(0)}%`;
            
            document.getElementById("thresh-press-low").value = cfg.pressure_threshold_low || 45.0;
            document.getElementById("lbl-thresh-press-low").innerText = `${(cfg.pressure_threshold_low || 45.0).toFixed(1)} PSI`;
            
            document.getElementById("thresh-press-high").value = cfg.pressure_threshold_high || 75.0;
            document.getElementById("lbl-thresh-press-high").innerText = `${(cfg.pressure_threshold_high || 75.0).toFixed(1)} PSI`;
        })
        .catch(err => {
            console.error("Error loading settings:", err);
        });
        
    // Bind Alert settings threshold slider label changes
    document.getElementById("thresh-leak").addEventListener("input", (e) => {
        document.getElementById("lbl-thresh-leak").innerText = `${e.target.value}%`;
    });
    
    document.getElementById("thresh-press-low").addEventListener("input", (e) => {
        document.getElementById("lbl-thresh-press-low").innerText = `${parseFloat(e.target.value).toFixed(1)} PSI`;
    });
    
    document.getElementById("thresh-press-high").addEventListener("input", (e) => {
        document.getElementById("lbl-thresh-press-high").innerText = `${parseFloat(e.target.value).toFixed(1)} PSI`;
    });

    // Save triggers
    document.getElementById("btn-save-smtp").addEventListener("click", saveSettings);
    document.getElementById("btn-test-smtp").addEventListener("click", testSmtpAlert);
}

function gatherSettingsPayload() {
    return {
        alert_email: document.getElementById("alert_email").value,
        leak_prob_threshold: parseFloat(document.getElementById("thresh-leak").value) / 100,
        pressure_threshold_low: parseFloat(document.getElementById("thresh-press-low").value),
        pressure_threshold_high: parseFloat(document.getElementById("thresh-press-high").value)
    };
}

function saveSettings() {
    const payload = gatherSettingsPayload();
    
    fetch('/api/alerts/config', {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${adminToken}`
        },
        body: JSON.stringify(payload)
    })
    .then(res => {
        if (res.status === 401) {
            logoutAdmin();
            throw new Error("Unauthorized access. Logged out.");
        }
        return res.json();
    })
    .then(data => {
        if (data.error) {
            alert("Error saving config: " + data.error);
        } else {
            alert(data.message || "Alert configurations saved!");
        }
    })
    .catch(err => {
        console.error("Error posting config:", err);
        alert(err.message || "Error saving configurations.");
    });
}

function testSmtpAlert() {
    const payload = gatherSettingsPayload();
    const btn = document.getElementById("btn-test-smtp");
    
    btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Sending Test...`;
    btn.disabled = true;
    
    fetch('/api/alerts/send-test', {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${adminToken}`
        },
        body: JSON.stringify({ alert_email: document.getElementById("alert_email").value })
    })
    .then(res => {
        if (res.status === 401) {
            logoutAdmin();
            throw new Error("Unauthorized access. Logged out.");
        }
        return res.json();
    })
    .then(data => {
        const lblTestBtn = currentLanguage === 'hi' ? 'परीक्षण ईमेल भेजें' : 'Send Test Email';
        btn.innerHTML = `<i class="fa-solid fa-paper-plane"></i> ${lblTestBtn}`;
        btn.disabled = false;
        
        if (data.error) {
            alert(`Test Failed:\n${data.error}`);
        } else {
            alert(data.message || "Test email dispatched successfully!");
        }
    })
    .catch(err => {
        const lblTestBtn = currentLanguage === 'hi' ? 'परीक्षण ईमेल भेजें' : 'Send Test Email';
        btn.innerHTML = `<i class="fa-solid fa-paper-plane"></i> ${lblTestBtn}`;
        btn.disabled = false;
        console.error("Error testing SMTP:", err);
        alert(err.message || "Test Failed: Connection timeout or server error.");
    });
}

// ============================================================
    // REPORT OPTIONS MODAL CONTROL & TRIGGERS
// ============================================================
function setupReportModal() {
    const modal = document.getElementById("report-modal");
    const btnPdf = document.getElementById("btn-pdf-report");
    const btnClose = document.getElementById("modal-close-btn");
    const btnCancel = document.getElementById("modal-btn-cancel");
    const btnDownload = document.getElementById("modal-btn-download");
    const radios = document.querySelectorAll('input[name="report-scope"]');
    
    const bulkSection = document.getElementById("modal-bulk-section");
    const singleSection = document.getElementById("modal-single-section");
    
    // Toggle scope sections
    radios.forEach(radio => {
        radio.addEventListener("change", (e) => {
            if (e.target.value === "bulk") {
                bulkSection.style.display = "block";
                singleSection.style.display = "none";
            } else {
                bulkSection.style.display = "none";
                singleSection.style.display = "block";
                // Populate pipes list dynamically
                populateModalPipes();
            }
        });
    });
    
    // Open modal
    btnPdf.addEventListener("click", () => {
        populateModalZones();
        modal.classList.add("active");
    });
    
    // Close modal handlers
    const closeModal = () => modal.classList.remove("active");
    btnClose.addEventListener("click", closeModal);
    btnCancel.addEventListener("click", closeModal);
    modal.addEventListener("click", (e) => {
        if (e.target === modal) closeModal();
    });
    
    // Download trigger
    btnDownload.addEventListener("click", () => {
        const scope = document.querySelector('input[name="report-scope"]:checked').value;
        let url = "/api/report/pdf?";
        
        if (scope === "bulk") {
            const zone = document.getElementById("modal-zone-filter").value;
            url += `scope=bulk&zone_office=${encodeURIComponent(zone)}`;
        } else {
            const pipeId = document.getElementById("modal-pipe-id").value;
            if (!pipeId) {
                alert("कृपया विफलता रिपोर्ट के लिए एक पाइप आईडी चुनें!");
                return;
            }
            const days = document.getElementById("modal-time-period").value;
            url += `scope=single&pipe_id=${encodeURIComponent(pipeId)}&days=${encodeURIComponent(days)}`;
        }
        
        closeModal();
        window.location.href = url;
    });
}

function populateModalZones() {
    const mainFilter = document.getElementById("authority-filter");
    const modalFilter = document.getElementById("modal-zone-filter");
    
    // Clear and clone options from main filter
    modalFilter.innerHTML = "";
    Array.from(mainFilter.options).forEach(opt => {
        const newOpt = document.createElement("option");
        newOpt.value = opt.value;
        newOpt.innerText = opt.innerText;
        modalFilter.appendChild(newOpt);
    });
    // Sync current zone office selection
    modalFilter.value = currentZoneOffice;
}

function populateModalPipes() {
    const pipeSelect = document.getElementById("modal-pipe-id");
    if (pipeSelect.options.length > 1) return; // Already populated
    
    const fetchPipes = () => {
        fetch("/api/pipes")
            .then(res => res.json())
            .then(pipes => {
                pipes.forEach(pipe => {
                    const opt = document.createElement("option");
                    opt.value = pipe.pipe_id;
                    opt.innerText = `${pipe.pipe_id} - ${pipe.zone_name} (${pipe.road})`;
                    pipeSelect.appendChild(opt);
                });
            })
            .catch(err => console.error("Error loading pipes for modal:", err));
    };
    
    if (allPipesData && allPipesData.length > 0) {
        allPipesData.forEach(pipe => {
            const opt = document.createElement("option");
            opt.value = pipe.pipe_id;
            opt.innerText = `${pipe.pipe_id} - ${pipe.zone_name} (${pipe.road})`;
            pipeSelect.appendChild(opt);
        });
    } else {
        fetchPipes();
    }
}

// Global toggle chart info
function toggleChartInfo(infoId) {
    const box = document.getElementById(infoId);
    if (box) {
        box.classList.toggle("active");
    }
}
