import sys
import re
import joblib
import difflib
import numpy as np
from IPython.core.interactiveshell import InteractiveShell
from IPython.display import display, HTML

# --- CONFIGURATION ---
BRAIN_PATH = "it_steward_brain.pkl"

# IMPROVEMENT: Multiple Support Links
SUPPORT_LINKS = {
    "📖 Knowledge Base": "https://wiki.yourcompany.com/it-help",
    "🎫 Submit Ticket": "https://jira.yourcompany.com/servicedesk",
    "💬 Ask on Slack": "https://slack.com/app_redirect?channel=it-support"
}

# --- LOAD BRAIN ---
try:
    brain_package = joblib.load(BRAIN_PATH)
    model = brain_package["model"]
    advice_map = brain_package["advice_map"]
    devops_scope_map = brain_package["devops_scope_map"]
    AI_LOADED = True
except Exception as e:
    print(f"Warning: IT Steward AI could not load. {e}")
    AI_LOADED = False

# --- HELPER: FOOTER LINK GENERATOR ---
def generate_footer_html():
    """Generates the HTML for the multi-link footer."""
    links_html = []
    for label, url in SUPPORT_LINKS.items():
        # Creates a link with hover effect
        link = f'<a href="{url}" target="_blank" style="color:#0056b3; text-decoration:none; font-weight:bold; margin-right:15px;">{label}</a>'
        links_html.append(link)
    
    # Join them with a small separator
    return "".join(links_html)

# --- FEATURE 1: Variable Typo Check ---
def get_variable_suggestion(error_text, shell):
    if "is not defined" in error_text:
        match = re.search(r"name '(\w+)' is not defined", error_text)
        if match:
            typo_var = match.group(1)
            current_vars = [v for v in shell.user_ns.keys() if not v.startswith('_')]
            
            # Exact Case Match
            case_matches = [v for v in current_vars if v.lower() == typo_var.lower()]
            if case_matches:
                return True, (
                    f"<b>Typo Detected (Case Mismatch):</b><br>"
                    f"You typed '{typo_var}', but variable <code style='background:#fff3cd; padding:2px 4px; border-radius:3px;'>{case_matches[0]}</code> exists."
                )
            
            # Fuzzy Match
            fuzzy_matches = difflib.get_close_matches(typo_var, current_vars, n=3, cutoff=0.5)
            if fuzzy_matches:
                return True, (
                    f"<b>Possible Typo Detected:</b><br>"
                    f"Did you mean one of these? <span style='background:#fff3cd; padding:2px 6px; border:1px solid #ffeeba;'>{', '.join(fuzzy_matches)}</span>"
                )
    return False, ""

# --- FEATURE 2: Dynamic Advice ---
def enhance_advice(category, base_advice, error_text):
    
    if category == "MISSING_LIBRARY":
        match = re.search(r"No module named '([^']+)'", error_text)
        if match:
            missing_pkg = match.group(1)
            cmd = f"!pip install {missing_pkg}"
            pypi_url = f"https://pypi.org/project/{missing_pkg}/"
            
            return (
                f"It seems you are missing a library. Try running this command:<br>"
                f"<div style='margin-top:8px; margin-bottom:8px;'>"
                f"<code style='background:#eee; padding:6px 10px; font-weight:bold; border-radius:4px;'>{cmd}</code>"
                f"</div>"
                f"⚠️ <i>Note: If this fails, verify the package exists on PyPI: "
                f"<a href='{pypi_url}' target='_blank' style='color:#0056b3; text-decoration:underline;'>{pypi_url}</a></i>"
                f"<br><br>"
                f"<span style='color:#856404; background-color:#fff3cd; padding:4px 6px; border-radius:4px; font-size:13px; border:1px solid #ffeeba;'>"
                f"🛑 <b>Production Policy:</b> 'pip install' is not recommended in prod environment."
                f"</span>"
            )

    if category == "PACKAGE_NOT_FOUND":
        match = re.search(r"requirement\s+([a-zA-Z0-9_\-]+)", error_text)
        pkg_name = match.group(1) if match else "your package"
        
        return (
            f"<b>Repository Error:</b> The package <b>'{pkg_name}'</b> was not found in the Nexus/Artifactory.<br><br>"
            f"<b>Recommended Actions:</b><br>"
            f"1. Ask DevOps to <b>append the package</b> to the repository.<br>"
            f"2. Or, try specifying a different version (e.g., <code>{pkg_name}==1.0.0</code>)."
        )

    return base_advice

# --- FEATURE 3: Highlighting ---
def get_highlighted_text(error_text, model):
    try:
        vect = model.steps[0][1]
        keywords = vect.get_feature_names_out()
        found_keywords = [w for w in keywords if w in error_text.lower()]
        top_words = sorted(found_keywords, key=len, reverse=True)[:4]
        annotated_text = error_text[-300:] 
        for word in top_words:
            annotated_text = annotated_text.replace(word, f'<span style="background-color: #ffeb3b; font-weight: bold;">{word}</span>')
        return annotated_text
    except:
        return error_text[-300:]

# --- UI RENDERERS (With Multi-Link Footer) ---

def render_devops_box(category, advice, logs):
    footer_links = generate_footer_html()
    html = f"""
    <div style="border-left: 6px solid #d9534f; background-color: #fff9f9; padding: 15px; margin-top: 15px; border-radius: 4px; font-family: 'Segoe UI', Arial, sans-serif; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
        <div style="color: #d9534f; font-weight: bold; font-size: 14px; padding-bottom: 8px; border-bottom: 1px solid #f5c6cb; margin-bottom: 10px;">
             🔧 DevOps Scope | Detected: {category}
        </div>
        <div style="font-size: 15px; color: #333; line-height: 1.5;">
            {advice}
        </div>
        <div style="font-size: 12px; color: #777; background-color: #fdfdfd; padding: 8px; margin-top: 12px; border-radius: 4px; border: 1px solid #eee;">
            <b>Focus Area:</b> ... {logs} ...
        </div>
        <div style="margin-top: 12px; padding-top: 10px; border-top: 1px solid #eee; font-size: 13px;">
            Need help? &nbsp; {footer_links}
        </div>
    </div>
    """
    display(HTML(html))

def render_user_scope_box(category, advice, logs):
    footer_links = generate_footer_html()
    html = f"""
    <div style="border-left: 6px solid #6c757d; background-color: #f8f9fa; padding: 15px; margin-top: 15px; border-radius: 4px; font-family: 'Segoe UI', Arial, sans-serif; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
        <div style="color: #495057; font-weight: bold; font-size: 14px; padding-bottom: 8px; border-bottom: 1px solid #dee2e6; margin-bottom: 10px;">
             👤 Self-Service | Detected: {category}
        </div>
        <div style="font-size: 15px; color: #333; line-height: 1.5;">
            {advice}
        </div>
        <div style="font-size: 12px; color: #777; background-color: #fff; padding: 8px; margin-top: 12px; border-radius: 4px; border: 1px solid #e9ecef;">
            <b>Focus Area:</b> ... {logs} ...
        </div>
        <div style="margin-top: 12px; padding-top: 10px; border-top: 1px solid #e9ecef; font-size: 13px;">
            Need help? &nbsp; {footer_links}
        </div>
    </div>
    """
    display(HTML(html))

def render_unknown_box(logs):
    footer_links = generate_footer_html()
    html = f"""
    <div style="border-left: 6px solid #f0ad4e; background-color: #fffdf5; padding: 15px; margin-top: 15px; border-radius: 4px; font-family: 'Segoe UI', Arial, sans-serif; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
        <div style="color: #8a6d3b; font-weight: bold; font-size: 14px; padding-bottom: 8px; border-bottom: 1px solid #faebcc; margin-bottom: 10px;">
             🤔 IT Steward AI | Unrecognized Issue
        </div>
        <div style="font-size: 15px; color: #333; line-height: 1.5;">
            <b>Status:</b> The system cannot identify this error clearly.
        </div>
        <div style="font-size: 12px; color: #777; background-color: #fff; padding: 8px; margin-top: 12px; border-radius: 4px; border: 1px solid #faebcc;">
             <b>Analysis Log:</b> ... {logs} ...
        </div>
        <div style="margin-top: 12px; padding-top: 10px; border-top: 1px solid #faebcc; font-size: 13px;">
            Need help? &nbsp; {footer_links}
        </div>
    </div>
    """
    display(HTML(html))

# --- MAIN LOGIC ---
def show_ai_help(shell, error_text, user_cmd=""):
    if not AI_LOADED: return

    # A. PREDICT
    category_pred = model.predict([error_text])[0]
    probs = model.predict_proba([error_text])
    confidence = np.max(probs) * 100

    # B. OVERRIDES (Regex Force)
    if "pip install" in user_cmd:
        category_pred = "PACKAGE_NOT_FOUND"
        confidence = 100
    elif "No module named" in error_text or "ModuleNotFoundError" in error_text:
        category_pred = "MISSING_LIBRARY"
        confidence = 100

    # C. RETRIEVE INFO
    is_devops = devops_scope_map.get(category_pred, False)
    base_advice = advice_map.get(category_pred, "No advice available.")
    
    # D. DYNAMIC ADVICE
    is_typo, typo_msg = get_variable_suggestion(error_text, shell)
    if is_typo:
        final_advice = typo_msg
        category_pred = "VARIABLE_ERROR" 
        is_devops = False 
    else:
        final_advice = enhance_advice(category_pred, base_advice, error_text)

    # 3. Highlights
    highlighted_log = get_highlighted_text(error_text, model)

    # E. RENDER SCENARIOS
    if confidence < 50:
        render_unknown_box(highlighted_log)
        return

    if is_devops:
        render_devops_box(category_pred, final_advice, highlighted_log)
    else:
        render_user_scope_box(category_pred, final_advice, highlighted_log)

# --- SYSTEM HOOKS ---
def smart_exception_handler(shell, etype, evalue, tb, tb_offset=None):
    shell.showtraceback((etype, evalue, tb), tb_offset=tb_offset)
    show_ai_help(shell, str(evalue))

def custom_system_executor(cmd):
    import subprocess
    print(f"👀 AI is watching command: '{cmd}' ...")
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = proc.communicate()
    if stdout: print(stdout)
    if stderr: print(stderr)
    
    full_log = (stdout or "") + (stderr or "")
    if proc.returncode != 0 or "ERROR" in full_log or "Traceback" in full_log:
        ip = get_ipython()
        show_ai_help(ip, full_log, user_cmd=cmd)

ip = get_ipython()
ip.set_custom_exc((Exception,), smart_exception_handler)
ip.system = custom_system_executor

print("✅ IT Steward AI: Active (Multi-Link Footer Support).")