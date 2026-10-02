"""Shared CSV decoding for the bulk importers.
Both importers (students and results) need the same three things before they
can differ at all: get the bytes off the upload and into text, work out what
separates the columns, and turn the header row into canonical field names.
That part lives here so a file exported from Excel behaves the same way in
both wizards.
"""
import csv
import io
# Guards a runaway file; a school cohort is a few hundred, not a few million.
MAX_CSV_ROWS = 5000
_EXTENSIONS = (".csv", ".txt", ".tsv")
_CANDIDATE_DELIMITERS = (",", ";", "\t", "|")
def _detect_delimiter(header_line):
    """Work out what separates the columns, using only the header row.
    csv.Sniffer guesses from statistical patterns across the whole sample, and
    it gives up on files people actually produce: one blank line in the middle
    is enough to make it raise. It then falls back to comma, every row
    collapses into a single column, and the import fails with a confusing
    "missing required column" instead of naming the real problem.
    The header is the reliable place to look. Each candidate is run through
    csv.reader on its own, so a delimiter that appears inside a quoted cell
    ("Science, General") is not counted.
    """
    best = (0, 0, ",")  # (count, -position, delimiter): ties favour earlier candidates
    for position, delimiter in enumerate(_CANDIDATE_DELIMITERS):
        try:
            fields = next(csv.reader([header_line], delimiter=delimiter))
        except (csv.Error, StopIteration):
            continue
        count = len(fields) - 1
        if count > best[0]:
            best = (count, -position, delimiter)
    return best[2]
def read_csv(upload):
    """Decode an uploaded CSV into (header_cells, rows).
    `rows` is a list of (line_number, cells) pairs, blank lines dropped but the
    original line number kept so an error can point staff at the right row in
    their editor.
    Returns (None, None, message) when the file cannot be used at all. Nothing
    is written to the database here.
    """
    if not upload:
        return None, None, "Choose a CSV file to upload."
    name = (upload.name or "").lower()
    if not name.endswith(_EXTENSIONS):
        return None, None, "That file is not a CSV. Expected a .csv file."
    raw = upload.read()
    if not raw.strip():
        return None, None, "That file is empty."
    # utf-8-sig strips the byte-order mark Excel writes, which otherwise ends
    # up glued to the first header name and breaks column detection.
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            text = raw.decode("latin-1")
        except UnicodeDecodeError:
            return None, None, "That file is not readable as text. Save it as UTF-8 CSV."
    # Detect from the header's own line, then let csv.reader re-read the header
    # properly. Sniffing is the only line-based step; everything after it is
    # parsed by the csv module.
    delimiter = _detect_delimiter(io.StringIO(text).readline())
    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    try:
        header = next(reader)
    except StopIteration:
        return None, None, "That file has no header row."
    rows = []
    for line_no, cells in enumerate(reader, start=2):
        if not any((cell or "").strip() for cell in cells):
            continue  # blank line
        if len(rows) >= MAX_CSV_ROWS:
            return None, None, (
                "That file has more than %d rows. Split it into smaller files."
                % MAX_CSV_ROWS
            )
        rows.append((line_no, cells))
    return header, rows, None
def normalise_headers(header, aliases):
    """Map each header cell to a canonical field name via `aliases`.
    Case, surrounding space, a BOM, and spaces or hyphens instead of
    underscores are all forgiven, so "Index Number", "index-number" and
    "INDEX_NUMBER" are the same column. Unrecognised cells map to None and are
    ignored.
    """
    columns = []
    for name in header:
        key = (name or "").strip().lower().lstrip("\ufeff")
        key = key.replace(" ", "_").replace("-", "_")
        columns.append(aliases.get(key))
    return columns
def cells_to_values(columns, cells):
    """Collapse a raw CSV row into {field: value}. First occurrence wins, so a
    duplicated column does not silently overwrite the first one's value."""
    values = {}
    for position, key in enumerate(columns):
        if key and key not in values:
            values[key] = cells[position].strip() if position < len(cells) else ""
    return values
def to_int(value):
    """Parse a mark from a cell. Returns None when it is not a whole number.
    "88", " 88 " and "88.0" all become 88, because a spreadsheet will happily
    hand back 88.0 for a whole mark. Anything else is None and the caller
    reports the row.
    """
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        pass
    try:
        number = float(text)
    except ValueError:
        return None
    return int(number) if number.is_integer() else None
