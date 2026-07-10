import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import sys
import os
import subprocess

sys.path.append(os.getcwd())

st.set_page_config(page_title="IQATA Dashboard", page_icon="🧪", layout="wide")

ACCENT = "#2563EB"
BG = "#0F172A"
CARD = "#1E293B"
TEXT = "#F8FAFC"
GOOD = "#22C55E"
BAD = "#EF4444"

st.markdown(f"""
<style>
.stApp {{ background-color:{BG}; color:{TEXT}; }}
div[data-testid="metric-container"]{{
    background:{CARD}; border-radius:14px; padding:18px;
    box-shadow:0px 3px 10px rgba(0,0,0,0.25); border-left:4px solid {ACCENT};
}}
.stButton>button{{ width:100%; border-radius:10px; height:45px; font-weight:600; border:1px solid {ACCENT}; }}
.stButton>button:hover{{ background-color:{ACCENT}; color:white; }}
footer{{ visibility:hidden; }}
</style>
""", unsafe_allow_html=True)

metrics_error = None
metrics = None
try:
    from analytics.metrics import Metrics
    metrics = Metrics()
except Exception as e:
    metrics_error = str(e)

rca_error = None
analyze_failure = None
try:
    from analytics.rca_engine import analyze_failure
except Exception as e:
    rca_error = str(e)


def safe_call(fn, default=0):
    try:
        return fn()
    except Exception:
        return default


def _subprocess_env():
    env = os.environ.copy()
    project_root = os.getcwd()
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = project_root + (os.pathsep + existing if existing else "")
    # Windows defaults subprocess stdout/stderr to the system codepage (cp1252/
    # 'charmap') when piped, which can't encode characters like ✅/❌. Any
    # print() with such a character then crashes with UnicodeEncodeError and
    # gets caught by the test's own except block, marking it FAIL even if the
    # actual test logic worked. Forcing UTF-8 here prevents that class of bug.
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def run_predictor():
    try:
        subprocess.run(
            [sys.executable, "ml/predictor.py"],
            capture_output=True, timeout=60, check=True,
            cwd=os.getcwd(), env=_subprocess_env(),
        )
        return pd.read_csv("data/prediction_results.csv"), None
    except Exception as e:
        return None, str(e)


def run_live_tests(website=None, browser=None, environment=None, modules=None):
    cmd = [sys.executable, "runner.py"]
    if website:
        cmd += ["--url", website]
    if browser:
        cmd += ["--browser", browser]
    if environment:
        cmd += ["--env", environment]
    if modules:
        cmd += ["--modules", ",".join(modules)]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=300,
            cwd=os.getcwd(), env=_subprocess_env(),
        )
        output = (result.stdout or "") + (("\n\nERROR:\n" + result.stderr) if result.stderr else "")
        return result.returncode == 0, output
    except subprocess.TimeoutExpired:
        return False, "Execution timed out after 5 minutes."
    except Exception as e:
        return False, str(e)


PAGES = [
    "🏠 Dashboard",
    "📊 Analytics",
    "🤖 AI Prediction",
    "🧩 Root Cause Analysis",
    "🌐 Website Testing",
    "📄 Reports",
    "⚙ Settings",
]

st.sidebar.title("🧪 IQATA")
page = st.sidebar.radio("Navigation", PAGES)

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Refresh Dashboard"):
    st.cache_data.clear()
    st.rerun()

if metrics_error:
    st.sidebar.error(f"metrics.py error:\n{metrics_error}")
else:
    st.sidebar.success("🟢 DB connected")

st.title("🧪 Intelligent QA & Test Automation Platform")
st.caption(f"Live data · last loaded {datetime.now().strftime('%H:%M:%S')}")
st.markdown("---")

# =================================================
# DASHBOARD
# =================================================

if page == "🏠 Dashboard":
    if metrics_error:
        st.error(f"Couldn't load Metrics(): {metrics_error}")
    else:
        total_cases = safe_call(metrics.total_test_cases)
        total_runs = safe_call(metrics.total_test_runs)
        passed = safe_call(metrics.passed_tests)
        failed = safe_call(metrics.failed_tests)
        pass_rate = safe_call(metrics.pass_rate)
        avg_time = safe_call(metrics.average_execution_time)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Test Cases", total_cases)
        col2.metric("Total Runs", total_runs)
        col3.metric("Pass Rate", f"{pass_rate}%")
        col4.metric("Avg Exec Time", f"{avg_time}s")

        st.markdown("---")
        left, right = st.columns(2)

        status_df = pd.DataFrame({"Status": ["Passed", "Failed"], "Count": [passed, failed]})
        if passed + failed > 0:
            fig = px.pie(status_df, values="Count", names="Status", hole=.55,
                         color="Status", color_discrete_map={"Passed": GOOD, "Failed": BAD},
                         title="Pass / Fail (from test_runs table)")
            left.plotly_chart(fig, use_container_width=True)
        else:
            left.info("No rows in test_runs yet — run tests to populate this.")

        mod_stats = safe_call(metrics.module_statistics, [])
        if mod_stats:
            mod_df = pd.DataFrame(mod_stats, columns=["Module", "Count"])
            right.plotly_chart(px.bar(mod_df, x="Module", y="Count", title="Test Cases by Module",
                                       color_discrete_sequence=[ACCENT]), use_container_width=True)
        else:
            right.info("No module_statistics data returned.")

    st.markdown("### 🚀 Live Test Execution")
    if st.button("▶ Run Live Tests"):
        with st.spinner("Running Selenium tests..."):
            success, output = run_live_tests()
        st.session_state["test_success"] = success
        st.session_state["test_output"] = output
        st.cache_data.clear()
        st.rerun()

    if "test_success" in st.session_state:
        if st.session_state["test_success"]:
            st.success("Tests completed.")
        else:
            st.error("Execution failed.")
        st.code(st.session_state["test_output"], language="text")

# =================================================
# ANALYTICS
# =================================================

elif page == "📊 Analytics":
    st.markdown("## 📊 Analytics")
    if metrics_error:
        st.error(f"metrics.py unavailable: {metrics_error}")
    else:
        c1, c2 = st.columns(2)
        browser_stats = safe_call(metrics.browser_statistics, [])
        if browser_stats:
            bdf = pd.DataFrame(browser_stats, columns=["Browser", "Count"])
            c1.plotly_chart(px.bar(bdf, x="Browser", y="Count", title="Browser Distribution",
                                    color_discrete_sequence=[ACCENT]), use_container_width=True)
        else:
            c1.info("No browser_statistics data.")

        env_stats = safe_call(metrics.environment_statistics, [])
        if env_stats:
            edf = pd.DataFrame(env_stats, columns=["Environment", "Count"])
            c2.plotly_chart(px.pie(edf, values="Count", names="Environment",
                                    title="Environment Distribution"), use_container_width=True)
        else:
            c2.info("No environment_statistics data.")

        st.metric("Failure Rate", f"{safe_call(metrics.failure_rate)}%")

# =================================================
# AI PREDICTION
# =================================================

elif page == "🤖 AI Prediction":
    st.markdown("## 🤖 AI Defect Prediction")
    st.caption(
        "⚠ predictor.py predicts on data/test_cases.csv, a separate file from your SQLite "
        "test_cases table. Until that CSV is generated from the live DB, this is a demo of the "
        "model pipeline, not a live reflection of the runs above."
    )

    if st.button("Run Prediction Model"):
        with st.spinner("Running ml/predictor.py..."):
            pred_df, err = run_predictor()
        if err:
            st.error(f"predictor.py failed:\n\n{err}")
        elif pred_df is not None:
            st.session_state["pred_df"] = pred_df

    if "pred_df" in st.session_state:
        pred_df = st.session_state["pred_df"]
        st.dataframe(pred_df, use_container_width=True, hide_index=True)
        if "failure_probability" in pred_df.columns:
            fig = px.bar(pred_df.sort_values("failure_probability", ascending=False),
                         x=pred_df.columns[0], y="failure_probability",
                         title="Failure Probability by Test Case", color_discrete_sequence=[BAD])
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Click 'Run Prediction Model' to generate live predictions.")

# =================================================
# ROOT CAUSE ANALYSIS
# (Bug fix: this branch's string previously didn't match the sidebar
# option — " Root Cause Analysis" vs "🧩 Root Cause Analysis" — so this
# entire page silently never rendered. Now it matches.)
# =================================================

elif page == "🧩 Root Cause Analysis":
    st.markdown("## 🧩 Root Cause Analysis")
    if rca_error:
        st.error(f"rca_engine.py unavailable: {rca_error}")
    else:
        st.caption(
            "Failure reasons are now captured automatically by runner.py when a live test "
            "fails (its real exception message), so this engine has real data to analyze. "
            "You can also paste any reason manually below."
        )
        reason = st.text_input("Failure reason (from a failed test)", placeholder="e.g. Timeout waiting for element")
        if reason:
            st.success(analyze_failure(reason))

        st.markdown("#### Reference examples")
        for r in ["Timeout", "Element Not Found", "Assertion Error",
                  "Database Connection Lost", "API Failure", "Invalid Credentials"]:
            st.write(f"**{r}** → {analyze_failure(r)}")

# =================================================
# WEBSITE TESTING
# =================================================

elif page == "🌐 Website Testing":
    st.markdown("## 🌐 Website Test Automation")
    st.caption(
        "⚠ Login, Search, and Checkout are hardcoded against two different demo sites "
        "(Login → the-internet.herokuapp.com, Search/Checkout → saucedemo.com). The Website URL "
        "field below only affects Search and Checkout. Login always tests its own fixed site "
        "no matter what you type here — typing saucedemo.com and checking Login will not make "
        "Login test saucedemo, it stays on its own site. This is a limitation of the existing "
        "test code, not a bug in this page."
    )

    website = st.text_input("Website URL", placeholder="https://example.com")
    col_a, col_b = st.columns(2)
    browser = col_a.selectbox("Browser", ["Chrome", "Firefox", "Edge"])
    environment = col_b.selectbox("Environment", ["Development", "Staging", "Production"])

    st.markdown("#### Modules to test")
    m1, m2, m3 = st.columns(3)
    selected_modules = []
    if m1.checkbox("Login", value=True):
        selected_modules.append("Login")
    if m2.checkbox("Search", value=True):
        selected_modules.append("Search")
    if m3.checkbox("Checkout", value=True):
        selected_modules.append("Checkout")

    if st.button("▶ Run Tests"):
        if not website:
            st.warning("Enter a website URL before running tests.")
        else:
            with st.spinner(f"Running runner.py against {website}..."):
                success, output = run_live_tests(website=website, browser=browser,
                                                   environment=environment, modules=selected_modules)
            st.session_state["website_test_result"] = {
                "website": website, "browser": browser, "environment": environment,
                "modules": selected_modules, "success": success, "output": output,
                "timestamp": datetime.now().strftime("%H:%M:%S"),
            }
            st.cache_data.clear()

    result = st.session_state.get("website_test_result")
    if result:
        st.markdown("---")
        st.markdown(f"### Results for {result['website']}")
        st.caption(f"Browser: {result['browser']} · Environment: {result['environment']} · "
                   f"Finished {result['timestamp']}")
        if result["success"]:
            st.success("All selected modules passed.")
        else:
            st.error("One or more modules failed. See output below.")
        if result["output"]:
            st.markdown("#### Console Output")
            st.code(result["output"])

# =================================================
# REPORTS — download only, reads reports/qa_report.txt if it exists
# =================================================

elif page == "📄 Reports":
    st.markdown("## 📄 QA Reports")

    report_path = "reports/qa_report.txt"
    if os.path.exists(report_path):
        with open(report_path, "r") as f:
            report = f.read()
        st.markdown("#### Report Preview")
        st.text(report)
        st.download_button("Download Report", report, file_name="QA_Report.txt")
    else:
        st.info("No report found yet at reports/qa_report.txt.")

# =================================================
# SETTINGS
# =================================================

elif page == "⚙ Settings":
    st.markdown("## ⚙ Settings")
    st.write("**Working directory:**", os.getcwd())
    st.write("**metrics.py status:**", "✅ OK" if not metrics_error else f"❌ {metrics_error}")
    st.write("**rca_engine.py status:**", "✅ OK" if not rca_error else f"❌ {rca_error}")

    st.markdown("---")
    st.markdown(
        "#### Fixed this round\n"
        "1. Root Cause Analysis page had a string mismatch with the sidebar and never rendered — fixed.\n"
        "2. URL/browser typed into Website Testing never reached Selenium (test classes rejected the kwargs, "
        "silently fell back to hardcoded URLs) — test classes now accept them for real.\n"
        "3. Screenshots always failed silently (captured after driver.quit()) — now captured before teardown.\n"
        "4. Reports page had no way to generate a report — 'Generate Report Now' button added.\n\n"
        "#### Still open\n"
        "- predictor.py reads data/test_cases.csv, not the live DB — the two can drift apart.\n"
        "- Search/Checkout tests only work against saucedemo-shaped sites, not arbitrary URLs.\n"
        "- Screenshot/log paths are stored in the DB but not yet displayed with st.image() on this page."
    )

st.markdown("---")
st.caption("IQATA Dashboard © 2026")