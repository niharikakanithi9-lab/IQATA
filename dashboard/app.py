import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import sys
import os
import subprocess

sys.path.append(os.getcwd())

st.set_page_config(page_title="IQATA Dashboard", layout="wide")

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
    # 'charmap') when piped, which can't encode characters like the old status
    # emoji. Any print() with such a character then crashes with
    # UnicodeEncodeError and gets caught by the test's own except block,
    # marking it FAIL even if the actual test logic worked. Forcing UTF-8
    # here prevents that class of bug.
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


def run_report_generator():
    try:
        subprocess.run(
            [sys.executable, "analytics/reports.py"],
            capture_output=True, timeout=60, check=True,
            cwd=os.getcwd(), env=_subprocess_env(),
        )
        return True, None
    except Exception as e:
        return False, str(e)


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
    "Dashboard",
    "Analytics",
    "AI Defect Prediction",
    "Root Cause Analysis",
    "Website Testing",
    "Reports",
    "Settings",
]

st.sidebar.title("IQATA")
page = st.sidebar.radio("Navigation", PAGES)

st.sidebar.markdown("---")
if st.sidebar.button("Refresh Dashboard"):
    st.cache_data.clear()
    st.rerun()

if metrics_error:
    st.sidebar.error(f"metrics.py error:\n{metrics_error}")
else:
    st.sidebar.success("Database connection established.")

st.title("Intelligent Quality Assurance and Test Automation Platform")
st.caption(f"Dashboard last updated: {datetime.now().strftime('%H:%M:%S')}")
st.markdown("---")

# =================================================
# DASHBOARD
# =================================================

if page == "Dashboard":
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

    st.markdown("### Test Execution")
    if st.button("Execute Test Suite"):
        with st.spinner("Executing automated test suite..."):
            success, output = run_live_tests()
        st.session_state["test_success"] = success
        st.session_state["test_output"] = output
        st.cache_data.clear()
        st.rerun()

    if "test_success" in st.session_state:
        if st.session_state["test_success"]:
            st.success("Test execution completed successfully.")
        else:
            st.error("Test execution completed with one or more failures.")
        st.code(st.session_state["test_output"], language="text")

# =================================================
# ANALYTICS
# =================================================

elif page == "Analytics":
    st.markdown("## Analytics")
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
            c1.info("No browser statistics are currently available.")

        env_stats = safe_call(metrics.environment_statistics, [])
        if env_stats:
            edf = pd.DataFrame(env_stats, columns=["Environment", "Count"])
            c2.plotly_chart(px.pie(edf, values="Count", names="Environment",
                                    title="Environment Distribution"), use_container_width=True)
        else:
            c2.info("No environment statistics are currently available.")

        st.metric("Failure Rate", f"{safe_call(metrics.failure_rate)}%")

# =================================================
# AI PREDICTION
# =================================================

elif page == "AI Defect Prediction":
    st.markdown("## AI-Based Defect Prediction")
    st.caption(
        "The prediction model evaluates the available test case dataset and estimates the "
        "probability of test failure. The generated predictions provide a quality risk "
        "assessment for each test case."
    )

    if st.button("Generate Predictions"):
        with st.spinner("Generating AI predictions..."):
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
        st.info("Select 'Generate Predictions' to perform AI-based quality risk analysis.")

# =================================================
# ROOT CAUSE ANALYSIS
# =================================================

elif page == "Root Cause Analysis":
    st.markdown("## Root Cause Analysis")
    if rca_error:
        st.error(f"rca_engine.py unavailable: {rca_error}")
    else:
        st.caption(
            "The Root Cause Analysis engine evaluates recorded failure messages and provides "
            "a possible explanation for the observed issue. You may also enter a custom "
            "failure description for analysis."
        )
        reason = st.text_input("Failure Description", placeholder="Example: Timeout while locating login button")
        if reason:
            st.success(analyze_failure(reason))

        st.markdown("#### Sample Failure Scenarios")
        for r in ["Timeout", "Element Not Found", "Assertion Error",
                  "Database Connection Lost", "API Failure", "Invalid Credentials"]:
            st.write(f"**{r}** → {analyze_failure(r)}")

# =================================================
# WEBSITE TESTING
# =================================================

elif page == "Website Testing":
    st.markdown("## Website Test Automation")
    st.caption(
        "This platform currently supports automated testing for the following demonstration "
        "websites:\n\n"
        "- SauceDemo\n"
        "- Automation Exercise\n"
        "- DemoBlaze\n\n"
        "Please enter the URL of one of the supported websites below. Credentials, page "
        "structure, and test workflows have been configured specifically for these "
        "applications. Execution against unsupported websites may result in unsuccessful "
        "test execution due to differences in application structure."
    )
    st.info(
        "Supported demonstration websites:\n\n"
        "- https://www.saucedemo.com/\n"
        "- https://automationexercise.com/login\n"
        "- https://www.demoblaze.com/\n\n"
        "Automated test cases have been designed and validated specifically for these "
        "applications."
    )

    website = st.text_input(
        "Website URL (Supported Websites)",
        placeholder="Examples: https://www.saucedemo.com/  |  https://automationexercise.com/login  |  https://www.demoblaze.com/",
    )
    col_a, col_b = st.columns(2)
    browser = col_a.selectbox("Browser", ["Chrome", "Firefox", "Edge"])
    environment = col_b.selectbox("Environment", ["Development", "Staging", "Production"])

    st.markdown("#### Test Modules")
    m1, m2, m3 = st.columns(3)
    selected_modules = []
    if m1.checkbox("Login", value=True):
        selected_modules.append("Login")
    if m2.checkbox("Search", value=True):
        selected_modules.append("Search")
    if m3.checkbox("Checkout", value=True):
        selected_modules.append("Checkout")

    if st.button("Execute Selected Tests"):
        if not website:
            st.warning("Please enter the URL of a supported website before executing the test suite.")
        else:
            with st.spinner("Executing automated test suite..."):
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
        st.markdown(f"### Execution Summary — {result['website']}")
        st.caption(f"Browser: {result['browser']} · Environment: {result['environment']} · "
                   f"Completed at {result['timestamp']}")
        if result["success"]:
            st.success("All selected test modules completed successfully.")
        else:
            st.error("One or more test modules encountered execution failures. Refer to the "
                     "execution log below for details.")
        if result["output"]:
            st.markdown("#### Execution Log")
            st.code(result["output"])

# =================================================
# REPORTS
# =================================================

elif page == "Reports":
    st.markdown("## Quality Assurance Reports")

    if st.button("Generate Report"):
        with st.spinner("Generating latest quality report..."):
            success, err = run_report_generator()
        if not success:
            st.error(f"Report generation failed:\n\n{err}")
        else:
            st.cache_data.clear()
            st.rerun()

    report_path = "reports/qa_report.txt"
    if os.path.exists(report_path):
        with open(report_path, "r") as f:
            report = f.read()
        st.markdown("#### Report Summary")
        st.text(report)
        st.download_button("Download Quality Report", report, file_name="QA_Report.txt")
    else:
        st.info("No quality assurance report is currently available.")

# =================================================
# SETTINGS
# =================================================

elif page == "Settings":
    st.markdown("## System Information")
    st.write("**Project Directory:**", os.getcwd())
    st.write("**Metrics Module Status:**", "OK" if not metrics_error else f"Unavailable — {metrics_error}")
    st.write("**Root Cause Analysis Module Status:**", "OK" if not rca_error else f"Unavailable — {rca_error}")

st.markdown("---")
st.caption("Intelligent Quality Assurance and Test Automation Platform | Version 1.0 | © 2026")