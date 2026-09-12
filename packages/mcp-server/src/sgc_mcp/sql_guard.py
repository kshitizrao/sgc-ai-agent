"""SQL safety guard — ensures only SELECT queries are executed.

Every SQL string must pass through ``validate_query`` before being sent to the
prod_pikpart database.  The guard performs three checks:

1. The query begins with ``SELECT`` (after stripping whitespace / comments).
2. None of the mutation keywords (INSERT, UPDATE, DELETE, DROP …) appear.
3. Only whitelisted tables are referenced.
"""

import logging
import re

logger = logging.getLogger("agent.mcp.sql_guard")

# ---------------------------------------------------------------------------
# Whitelist of tables the MCP server is allowed to read
# ---------------------------------------------------------------------------
ALLOWED_TABLES: frozenset[str] = frozenset(
    {
        "customers",
        "services",
        "customer_vehicles",
        "vehicle_services",
        "service_centre_services",
        "booking_services",
        "bookings",
        "vehicle_brands",
        "vehicle_categories",
    }
)

# ---------------------------------------------------------------------------
# Keywords that must NEVER appear in a query
# ---------------------------------------------------------------------------
_MUTATION_KEYWORDS: frozenset[str] = frozenset(
    {
        "INSERT",
        "UPDATE",
        "DELETE",
        "DROP",
        "ALTER",
        "TRUNCATE",
        "CREATE",
        "GRANT",
        "REVOKE",
        "EXECUTE",
        "EXEC",
        "CALL",
        "SET ",
        "COPY",
        "VACUUM",
        "REINDEX",
        "LOCK",
    }
)

# Maximum number of rows the guard will allow a query to return.
MAX_RESULT_LIMIT: int = 100

# Pre-compiled regex to strip SQL-style line comments and block comments.
_COMMENT_RE = re.compile(r"(--[^\n]*|/\*.*?\*/)", re.DOTALL)


class SQLGuardError(Exception):
    """Raised when a query fails the safety validation."""


def validate_query(sql: str) -> str:
    """Validate and return the sanitised SQL.

    Raises :class:`SQLGuardError` if the query is unsafe.

    Parameters
    ----------
    sql:
        The raw SQL string to validate.

    Returns
    -------
    str
        The validated SQL with a ``LIMIT`` clause appended if missing.
    """
    if not sql or not sql.strip():
        raise SQLGuardError("Empty SQL query")

    # Strip comments so attackers cannot hide keywords inside them.
    cleaned = _COMMENT_RE.sub(" ", sql).strip()
    upper = cleaned.upper()

    # 1. Must start with SELECT
    if not upper.startswith("SELECT"):
        raise SQLGuardError(
            f"Only SELECT queries are allowed. Got: {cleaned[:60]}…"
        )

    # 2. No mutation keywords
    for kw in _MUTATION_KEYWORDS:
        # Use word-boundary check to avoid false positives like "UPDATED_AT"
        pattern = rf"\b{kw}\b"
        if re.search(pattern, upper):
            raise SQLGuardError(
                f"Mutation keyword '{kw}' detected in query — blocked."
            )

    # 3. Enforce LIMIT
    if "LIMIT" not in upper:
        cleaned = cleaned.rstrip(";") + f" LIMIT {MAX_RESULT_LIMIT}"
        logger.debug("Appended LIMIT %d to query", MAX_RESULT_LIMIT)

    logger.info(
        "SQL guard passed",
        extra={"query_preview": cleaned[:120]},
    )
    return cleaned


def validate_table_name(table: str) -> str:
    """Ensure a table name is in the whitelist.

    Raises :class:`SQLGuardError` for disallowed tables.
    """
    if table not in ALLOWED_TABLES:
        raise SQLGuardError(
            f"Table '{table}' is not in the allowed whitelist: {sorted(ALLOWED_TABLES)}"
        )
    return table
