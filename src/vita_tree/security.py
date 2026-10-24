"""Small boundary policies, not a sandbox for arbitrary local programs."""
import os
from pathlib import Path, PurePosixPath
import re
from urllib.parse import quote, quote_plus


def snapshot_excluded(name):
    parts = [part.casefold() for part in PurePosixPath(name).parts]
    return any(part in {'.git','.vita','.ssh','.aws','.codex','.env','.netrc','_netrc',
                        '.pypirc','.npmrc','.git-credentials','id_rsa','id_ed25519'}
               or part.startswith('.env.') for part in parts)


def credential_name(name):
    return bool(re.search(r'(?:KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL)', name, re.I))


def redact(value, secrets):
    result = str(value)
    for secret in sorted({s for s in secrets if isinstance(s,str) and s}, key=len, reverse=True):
        for encoded in {secret,quote(secret,safe=''),quote_plus(secret,safe='')}:
            result = result.replace(encoded, '[REDACTED]')
    # Repository remotes can contain HTTP userinfo even when no session key is known.
    return re.sub(r'(https?://)[^\s/@]+(?::[^\s/@]*)?@',r'\1[REDACTED]@',result,flags=re.I)


def scrub_generated(folder, secrets):
    """Withhold detected credentials before reports, reviews or checkpoints publish.

    This checks known literal/URL-encoded values, not arbitrary encodings or PII.
    The caller fails the run; redacted output is never accepted as a valid result.
    """
    from .fileio import atomic_write_bytes
    from .workspace import safe_path
    changed = False
    oversized = False
    paths = [folder/'main.tex',folder/'cover-letter.tex']
    for name in ('results','factual-changes','tmp'):
        paths.extend((folder/'.vita'/name).rglob('*'))
    for path in paths:
        path = safe_path(folder,path.relative_to(folder).as_posix())
        if not path.is_file():
            continue
        if path.stat().st_size > 32_000_000:
            path.unlink()
            oversized = True
            continue
        content = path.read_bytes()
        # Use byte replacement too: JSON, logs and PDFs must not gain a known
        # credential merely because they are not UTF-8 text.
        clean = content
        for secret in {s for s in secrets if isinstance(s,str) and s}:
            for encoded in {secret,quote(secret,safe=''),quote_plus(secret,safe='')}:
                clean = clean.replace(encoded.encode('utf-8'),b'[REDACTED]')
        if clean != content:
            atomic_write_bytes(path,clean)
            changed = True
    if oversized:
        raise ValueError('Generated output exceeds the inspection limit')
    return changed


def compiler_environment(folder, output):
    """A TeX child needs OS/font configuration, not provider or session secrets."""
    allowed = {'PATH','SYSTEMROOT','WINDIR','SYSTEMDRIVE','PROGRAMFILES','PROGRAMFILES(X86)',
               'APPDATA','LOCALAPPDATA','USERPROFILE','HOMEDRIVE','HOMEPATH','HOME',
               'TMP','TEMP','TMPDIR','LANG','LC_ALL','LC_CTYPE','TZ','FONTCONFIG_PATH','FONTCONFIG_FILE'}
    env = {k:v for k,v in os.environ.items() if k.upper() in allowed}
    directories = []
    roots = untrusted_roots(folder)
    for raw in os.get_exec_path(env):
        path = Path(raw)
        if path.is_absolute() and path.resolve() != Path.cwd().resolve() and not any(path.resolve().is_relative_to(root) for root in roots):
            directories.append(str(path))
    env.update(PATH=os.pathsep.join(directories), NoDefaultCurrentDirectoryInExePath='1',
               openin_any='p',openout_any='p',TEXMFOUTPUT=str(output))
    # MiKTeX does not use Kpathsea's openin_any policy. Set per-application
    # values too, which take precedence over installed application settings.
    for app in ('','MIKTEX_','PDFLATEX_','PDFTEX_','LATEX_','TEX_','XELATEX_','XETEX_',
                'LUALATEX_','LUATEX_','LUAHBTEX_'):
        prefix = 'MIKTEX_'+app+'CORE_'
        env[prefix+'ALLOWUNSAFEINPUTFILES'] = 'false'
        env[prefix+'ALLOWUNSAFEOUTPUTFILES'] = 'false'
        env[prefix+'SHELLCOMMANDMODE'] = 'Forbidden'
    return env


def untrusted_roots(folder):
    folder = Path(folder).resolve()
    roots = [folder]
    for parent in (folder,*folder.parents):
        if (parent/'.git').exists():
            roots.append(parent)
            break
    return roots


def engine_executable(engine, folder, env):
    import shutil
    # Absolute candidate lookup avoids Windows' implicit current-directory
    # executable search. Trust the installed PATH, never a template's binaries.
    suffixes = ['.exe'] if os.name == 'nt' else ['']
    for directory in os.get_exec_path(env):
        for suffix in suffixes:
            candidate = Path(directory)/(engine+suffix)
            found = shutil.which(str(candidate)) if candidate.is_absolute() else None
            if found and not any(Path(found).resolve().is_relative_to(root) for root in untrusted_roots(folder)):
                return found
    raise ValueError(f'{engine} not found outside the application folder. Install MiKTeX or TeX Live, or choose an installed engine.')
