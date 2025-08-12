import os
import re


# Read file paths from file_list.txt and remove any leading/trailing quotes
with open('file_list.txt', 'r', encoding='utf-8') as f:
    file_paths = [line.strip().strip('\"\'') for line in f if line.strip()]

def clean_filename(filename: str) -> str:
    name, ext = os.path.splitext(filename)
    ext = ext.lower()
    base = name

    # Remove leading repeated [tags] or (tags)
    base = re.sub(r'^(?:\s*[\[(][^\]\)]*[\])]\s*)+', '', base)

    # Normalize separators to spaces
    base = re.sub(r'[._]+', ' ', base)

    # Try patterns to detect season/episode
    season = episode = None
    m = re.search(r'[Ss](\d{1,2})\s*[ ._-]*[Ee](\d{1,3})', base)
    if m:
        season, episode = int(m.group(1)), int(m.group(2))
        show_part = base[:m.start()].strip()
    else:
        m = re.search(r'(\d{1,2})[xX](\d{1,3})', base)
        if m:
            season, episode = int(m.group(1)), int(m.group(2))
            show_part = base[:m.start()].strip()
        else:
            # Season 02 - 01 or Season 2 Ep 01
            ms = re.search(r'[Ss]eason\s*(\d{1,2})', base)
            me = re.search(r'(?:-|Ep(?:isode)?\s*)?(\d{1,3})(?!\d)', base)
            # Prefer " - 01" near end
            me_dash = re.search(r'-\s*(\d{1,3})(?!\d)\s*$', base)
            if ms and me_dash:
                season, episode = int(ms.group(1)), int(me_dash.group(1))
                show_part = base[:ms.start()].strip()
            elif ms and me:
                season, episode = int(ms.group(1)), int(me.group(1))
                show_part = base[:ms.start()].strip()
            elif me_dash:
                # No explicit season, but trailing - 01 style; assume Season 1
                season, episode = 1, int(me_dash.group(1))
                show_part = base[:me_dash.start()].strip()
            else:
                show_part = base

    # Build clean show title from show_part
    # Remove bracketed tokens anywhere in show_part
    show_part = re.sub(r'[\[(][^\]\)]*[\])]', '', show_part)
    # Remove explicit "Season N" from title
    show_part = re.sub(r'\b[Ss]eason\s*\d+\b', '', show_part)

    # Remove common release tokens
    token_pattern = re.compile(r"\b(4K|8K|\d{3,4}p|10bit|8bit|WEB(?:Rip|[- ]DL)?|BRRip|Blu-?Ray|BDRip|HDRip|NF|AMZN|DSNP|HULU|MAX|iTUNES|x(?:264|265)|H\.?26[45]|HEVC|AV1|AAC|AC3|E-?AC-?3|DDP(?:\.\d)?|DTS(?:-HD)?|FLAC|ATMOS|HDR10\+?|DV|DoVi|MULTI|DUAL(?:\s*AUDIO)?|SUBS?|VOSTFR|REPACK|PROPER|INTERNAL|EXTENDED|UNCENSORED|UNRATED|REMUX|PSA|Hodl|KONTRAST|WEB|Rip|XviD|HDTV|WEBDL)\b",
                                     flags=re.IGNORECASE)
    show_part = token_pattern.sub('', show_part)

    # Collapse whitespace and trim punctuation
    show_part = re.sub(r'\s+', ' ', show_part).strip(" -_.")

    # Sanitize title for Windows (remove invalid filename chars)
    show_part = re.sub(r'[<>:"/\\|?*]', '', show_part)
    show_part = show_part.rstrip(' .')

    if season is not None and episode is not None and show_part:
        safe = f"{show_part} - S{season:02d}E{episode:02d}{ext}"
        return safe

    # Fallback: just cleaned base
    fallback = re.sub(r'\s+', ' ', base).strip()
    return f"{fallback}{ext}"

for path in file_paths:
    try:
        dirpath, filename = os.path.split(path)
        new_filename = clean_filename(filename)
        new_path = os.path.join(dirpath, new_filename)
        if path == new_path:
            print(f"No change: {filename}")
            continue
        if os.path.exists(new_path) and os.path.normcase(path) != os.path.normcase(new_path):
            print(f"Target exists, skipping to avoid overwrite: {new_path}")
            continue
        print(f"Renaming: {filename} -> {new_filename}")
        os.rename(path, new_path)
    except FileNotFoundError:
        print(f"File not found: {path}. Skipping.")
    except Exception as e:
        print(f"Error processing {path}: {e}. Skipping.")
