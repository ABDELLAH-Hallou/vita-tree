"""Output-language choices from the same project configuration used by AI runs."""
import json
import re

BUILTIN = {
    'en': 'English', 'fr': 'French', 'ar': 'Arabic', 'de': 'German',
    'es': 'Spanish', 'it': 'Italian', 'nl': 'Dutch', 'pt': 'Portuguese',
}


def configured(raw):
    names = dict(BUILTIN)
    try:
        data = json.loads(raw)
        custom = data.get('language_map', {}) if isinstance(data, dict) else {}
        if isinstance(custom, dict):
            for code, label in custom.items():
                if (isinstance(code, str) and not code.startswith('_')
                        and re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_.-]{0,63}', code)
                        and isinstance(label, str) and 0 < len(label.strip()) <= 160
                        and not any(ord(c) < 32 or ord(c) == 127 for c in label)):
                    names[code.lower()] = label.strip()
    except (ValueError, TypeError):
        pass
    return [{'code': code, 'name': label} for code, label in names.items()]


def discover(workspace, branch):
    from .workspace import read_text, safe_path
    # A local application file replaces the collection file, just as in
    # Workspace._ai_context; do not union languages from unrelated branches.
    location = workspace.location(branch)
    if location:
        path = safe_path(location, '.vita/extensions.json')
        if path.is_file():
            return configured(read_text(path))
    else:
        raw = workspace.read(branch, '.vita/extensions.json')
        if raw:
            return configured(raw)
    return configured(read_text(safe_path(workspace.repository, '.vita/extensions.json')))
