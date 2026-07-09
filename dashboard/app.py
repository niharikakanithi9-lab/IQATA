import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sys
import os
import io
import time
import subprocess

sys.path.append(os.getcwd())

st.set_page_config(page_title="IQATA Dashboard", page_icon="🧪", layout="wide")

ACCENT = "#2563EB"
BG = "#0F172A"
CARD = "#1E293B"
TEXT = "#F8FAFC"
GOOD = "#22C55E"
WARN = "#F59E0B"
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
.card {{ background:{CARD}; border-radius:14px; padding:20px; box-shadow:0px 3px 10px rgba(0,0,0,0.2); margin-bottom:14px; }}
footer{{ visibility:hidden; }}
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# Optional auto-refresh (used only on the Website Testing page,
# so it doesn't spam reruns on every other page).
# -------------------------------------------------
try:
    from streamlit_autorefresh import st_autorefresh
    AUTOREFRESH_AVAILABLE = True
except Exception:
    AUTOREFRESH_AVAILABLE = False

# -------------------------------------------------
# Safe imports from YOUR modules — each wrapped so one
# broken module doesn't crash the whole dashboard.
# -------------------------------------------------
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
    """Call a metrics method; fall back to default if it errors."""
    try:
        return fn()
    except Exception:
        return default


@st.cache_data(ttl=5)
def load_prediction_csv():
    """Cached read of the prediction results CSV, cleared on refresh."""
    return pd.read_csv("data/prediction_results.csv")


def _subprocess_env():
    """
    Build an environment for child processes that includes the project
    root on PYTHONPATH. Without this, `python analytics/reports.py`
    (or runner.py) only sees its own folder on sys.path, so top-level
    packages like database/ can't be imported and you get
    ModuleNotFoundError.
    """
    env = os.environ.copy()
    project_root = os.getcwd()
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = project_root + (os.pathsep + existing if existing else "")
    return env


def run_predictor():
    """
    predictor.py is currently a top-level script (runs on import, reads
    data/test_cases.csv, writes data/prediction_results.csv). We run it
    as a subprocess instead of importing it, so it doesn't re-execute on
    every Streamlit rerun, and we read back its output CSV.

    NOTE: this predicts on data/test_cases.csv, which is a separate file
    from your SQLite test_cases table — the two may not match yet.
    """
    try:
        subprocess.run(
            ["python", "ml/predictor.py"],
            capture_output=True,
            timeout=60,
            check=True,
            cwd=os.getcwd(),
            env=_subprocess_env(),
        )
        st.cache_data.clear()
        return pd.read_csv("data/prediction_results.csv"), None
    except Exception as e:
        return None, str(e)


def run_live_tests(website=None, browser=None, environment=None, modules=None):
    """
    Executes runner.py and returns (success: bool, output: str).

    This is the ONE signature both pages now use:
      - Dashboard page calls run_live_tests() with no arguments, so
        runner.py falls back to its own defaults (Chrome, Development,
        Login+Search+Checkout).
      - Website Testing page calls run_live_tests(website=..., browser=...,
        environment=..., modules=[...]); those values are forwarded to
        runner.py as CLI flags (--url/--browser/--env/--modules), which
        runner.py now actually reads and acts on.

    Previously the two pages expected different return shapes
    (success/output vs out/err) and different argument counts — that
    mismatch is what's fixed here.
    """
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
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=os.getcwd(),
            env=_subprocess_env(),
        )
        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            output += "\n\nERROR:\n"
            output += result.stderr
        return result.returncode == 0, output
    except subprocess.TimeoutExpired:
        return False, "Execution timed out after 5 minutes."
    except Exception as e:
        return False, str(e)


def run_reports_script():
    """Runs analytics/reports.py as a subprocess to (re)generate reports/qa_report.txt."""
    try:
        result = subprocess.run(
            ["python", "analytics/reports.py"],
            capture_output=True,
            timeout=60,
            text=True,
            cwd=os.getcwd(),
            env=_subprocess_env(),
        )
        return result.stdout, result.stderr
    except Exception as e:
        return None, str(e)


# -------------------------------------------------
# Sidebar
# -------------------------------------------------
st.sidebar.title("🧪 IQATA")
page = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Dashboard",
        "📊 Analytics",
        "🤖 AI Prediction",
        "🧩 Root Cause Analysis",
        "🌐 Website Testing",
        "📄 Reports",
        "⚙ Settings",
    ],
)

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Refresh Dashboard"):
    st.cache_data.clear()
    st.cache_resource.clear()
    st.toast("Refreshing data...")
    st.rerun()

if metrics_error:
    st.sidebar.error(f"metrics.py error:\n{metrics_error}")
else:
    st.sidebar.success("🟢 DB connected")

# -------------------------------------------------
# Header
# -------------------------------------------------
st.title("🧪 Intelligent QA & Test Automation Platform")
st.caption(f"Live data · last loaded {datetime.now().strftime('%H:%M:%S')}")
st.markdown("---")

# =================================================
# DASHBOARD
# =================================================
if page == "🏠 Dashboard":
    if metrics_error:
        st.error(
            "Couldn't load analytics.metrics.Metrics(). Showing this instead of fake numbers:\n\n"
            f"{metrics_error}\n\nCheck that qa_platform.db exists and database/base_db.py "
            "is importable from this working directory."
        )
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
            left.plotly_chart(fig, width="stretch")
        else:
            left.info("No rows in test_runs yet — run tests via runner.py to populate this.")

        mod_stats = safe_call(metrics.module_statistics, [])
        if mod_stats:
            mod_df = pd.DataFrame(mod_stats, columns=["Module", "Count"])
            fig2 = px.bar(mod_df, x="Module", y="Count", title="Test Cases by Module",
                          color_discrete_sequence=[ACCENT])
            right.plotly_chart(fig2, width="stretch")
        else:
            right.info("No module_statistics data returned (check 'module' column in test_cases).")

        st.markdown("### 🚀 Live Test Execution")
        if st.button("▶ Run Live Tests", width="stretch"):
            with st.spinner("Running Selenium Tests..."):
                success, output = run_live_tests()
            st.session_state["test_success"] = success
            st.session_state["test_output"] = output
            st.cache_data.clear()
            st.cache_resource.clear()
            st.rerun()

        if "test_success" in st.session_state:
            if st.session_state["test_success"]:
                st.success(" Selenium tests completed successfully.")
            else:
                st.error(" Selenium execution failed.")
            st.code(st.session_state["test_output"], language="text")

        if "test_output" in st.session_state:
            if st.button("🗑 Clear Console"):
                del st.session_state["test_output"]
                del st.session_state["test_success"]
                st.rerun()

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
                                    color_discrete_sequence=[ACCENT]), width="stretch")
        else:
            c1.info("No browser_statistics data.")

        env_stats = safe_call(metrics.environment_statistics, [])
        if env_stats:
            edf = pd.DataFrame(env_stats, columns=["Environment", "Count"])
            c2.plotly_chart(px.pie(edf, values="Count", names="Environment",
                                    title="Environment Distribution"), width="stretch")
        else:
            c2.info("No environment_statistics data.")

        st.metric("Failure Rate", f"{safe_call(metrics.failure_rate)}%")

# =================================================
# AI PREDICTION
# =================================================
elif page == "🤖 AI Prediction":
    st.markdown("## 🤖 AI Defect Prediction")
    st.caption(
        " predictor.py currently predicts on data/test_cases.csv, which is separate from your "
        "SQLite test_cases table. Until that CSV is generated from the live DB, treat this panel "
        "as a demo of the model pipeline, not a live reflection of test_runs above."
    )

    if st.button("Run Prediction Model"):
        with st.spinner("Running ml/predictor.py..."):
            pred_df, err = run_predictor()
        if err:
            st.error(f"predictor.py failed:\n\n{err}\n\nCheck ml/model.pkl and data/test_cases.csv "
                     "exist and are readable from this working directory.")
        elif pred_df is not None:
            st.session_state["pred_df"] = pred_df

    if "pred_df" in st.session_state:
        pred_df = st.session_state["pred_df"]
        st.dataframe(pred_df, use_container_width=True, hide_index=True)
        if "failure_probability" in pred_df.columns:
            fig = px.bar(pred_df.sort_values("failure_probability", ascending=False),
                         x=pred_df.columns[0], y="failure_probability",
                         title="Failure Probability by Test Case",
                         color_discrete_sequence=[BAD])
            st.plotly_chart(fig, width="stretch")
    else:
        st.info("Click 'Run Prediction Model' to generate live predictions from your trained model.")

# =================================================
# RCA
# =================================================
elif page == " Root Cause Analysis":
    st.markdown("## Root Cause Analysis")
    if rca_error:
        st.error(f"rca_engine.py unavailable: {rca_error}")
    else:
        st.caption(
            "Failure reasons are now captured automatically by runner.py whenever a live test "
            "fails (TimeoutException, NoSuchElementException, AssertionError, etc.), so this "
            "engine has real data to work with. You can also paste any reason manually below."
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
        "This page passes the fields below to runner.py as command-line args "
        "(--url, --browser, --env, --modules), and runner.py now reads sys.argv "
        "(via argparse) so these actually control the Selenium run instead of "
        "being ignored."
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

    run_clicked = st.button("▶ Run Tests")

    if run_clicked:
        if not website:
            st.warning("Enter a website URL before running tests.")
        else:
            progress = st.progress(0, text="Starting...")
            progress.progress(20, text="Launching Selenium session...")
            time.sleep(0.3)
            progress.progress(45, text="Running selected modules...")

            with st.spinner(f"Running runner.py against {website}..."):
                success, output = run_live_tests(
                    website=website,
                    browser=browser,
                    environment=environment,
                    modules=selected_modules,
                )

            progress.progress(80, text="Collecting results...")

            st.session_state["website_test_result"] = {
                "website": website,
                "browser": browser,
                "environment": environment,
                "modules": selected_modules,
                "success": success,
                "output": output,
                "timestamp": datetime.now().strftime("%H:%M:%S"),
            }
            progress.progress(100, text="Done")
            st.cache_data.clear()

    result = st.session_state.get("website_test_result")
    if result:
        st.markdown("---")
        st.markdown(f"### Results for {result['website']}")
        st.caption(
            f"Browser: {result['browser']} · Environment: {result['environment']} · "
            f"Finished {result['timestamp']}"
        )

        if result["success"]:
            st.success(" All selected modules passed.")
        else:
            st.error(" One or more modules failed (or runner.py hit an error). See output below.")

        if result["output"]:
            st.markdown("#### Console Output")
            st.code(result["output"])

        st.markdown("#### Execution Timeline")
        for mod in result["modules"]:
            st.write(f"- **{mod}** — see console output above for pass/fail (runner.py output is the source of truth)")

        st.markdown("#### Artifacts")
        art1, art2, art3 = st.columns(3)
        art1.write("📸 Screenshot — runner.py now saves one to screenshots/ on failure; "
                    "wire up st.image(path) here once you're reading paths back from the DB.")
        art2.write("📄 HTML Report — link it here once runner.py writes one")
        art3.write("🧾 Logs — runner.py now writes a per-test log file to logs/; "
                    "shown inline in Console Output above")

        st.markdown("---")
        st.markdown("#### AI Prediction on this run")
        if st.button("Run Prediction for This Test"):
            with st.spinner("Running ml/predictor.py..."):
                pred_df, perr = run_predictor()
            if perr:
                st.error(f"predictor.py failed:\n\n{perr}")
            elif pred_df is not None:
                st.dataframe(pred_df, use_container_width=True, hide_index=True)

        st.markdown("#### Root Cause (if failed)")
        if not rca_error:
            if not result["success"] and result["output"]:
                st.info(analyze_failure(result["output"]))
            else:
                st.caption("No failure text captured for this run.")
        else:
            st.error(f"rca_engine.py unavailable: {rca_error}")

    if AUTOREFRESH_AVAILABLE and run_clicked:
        st_autorefresh(interval=5000, key="website_test_refresh")

# =================================================
# REPORTS
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
    st.write("**metrics.py status:**", " OK" if not metrics_error else f" {metrics_error}")
    st.write("**rca_engine.py status:**", " OK" if not rca_error else f" {rca_error}")
    st.write("**streamlit-autorefresh installed:**", " Yes" if AUTOREFRESH_AVAILABLE else " No (pip install streamlit-autorefresh)")

    st.markdown("---")
    st.markdown(
        "#### Known gaps (fix if time allows before demo)\n"
        "1. predictor.py reads data/test_cases.csv, not the SQLite DB — the two can drift apart.\n"
        "2. Both predictor.py and runner.py are scripts, not functions — this app runs them as "
        "subprocesses to stay safe, which is slower than a direct function call would be.\n"
        "3. Screenshot/log paths are now stored in the DB by runner.py, but this page doesn't "
        "read them back yet with st.image()/a download link — that's a nice follow-up.\n"
        "4. Registration/Profile modules only run if tests/registration_test.py and "
        "tests/profile_test.py exist — otherwise runner.py prints a warning and skips them."
    )
    st.markdown("---")
    st.caption("IQATA Dashboard © 2026")