"""
voice.py
---------
Accessible voice support for MindBloom.

Uses the browser's built-in Web Speech API (speechSynthesis) for
Text-to-Speech, since this works reliably inside Streamlit apps
(including Streamlit Community Cloud) without extra server-side
dependencies. Full speech RECOGNITION (listening to the user talk)
is not reliably supported inside Streamlit Cloud's sandboxed browser
environment, so this app uses simple, large text/button inputs as a
dependable fallback instead. Voice is always optional, never required.
"""

import streamlit.components.v1 as components

# Map our app languages to BCP-47 language codes for the browser's
# speech synthesis engine. Hindi/Kannada voice availability depends
# on the user's device and browser.
LANG_CODES = {
    "English": "en-IN",
    "Hindi": "hi-IN",
    "Kannada": "kn-IN",
}


def speak(text, language="English", key="speak"):
    """
    Render an invisible helper that immediately reads the given text
    aloud using the browser's speech synthesis, if available.
    Fails silently (no crash) if the browser does not support it.
    """
    lang_code = LANG_CODES.get(language, "en-IN")
    safe_text = text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")

    html_code = f"""
    <script>
    try {{
        if ('speechSynthesis' in window) {{
            var utterance = new SpeechSynthesisUtterance("{safe_text}");
            utterance.lang = "{lang_code}";
            utterance.rate = 0.9;
            window.speechSynthesis.cancel();
            window.speechSynthesis.speak(utterance);
        }}
    }} catch (e) {{
        // Voice not supported - fail silently, text is always shown too.
    }}
    </script>
    """
    components.html(html_code, height=0, width=0)


def read_aloud_button(text, language="English", label="🔊 Read Aloud", key="read_aloud"):
    """
    Render a large, friendly 'Read Aloud' button. When pressed, it
    speaks the given text aloud. Returns True if the button was
    pressed this run (useful if the caller wants to react to it).
    """
    import streamlit as st
    pressed = st.button(label, key=key, use_container_width=True)
    if pressed:
        speak(text, language=language, key=key + "_speak")
    return pressed
