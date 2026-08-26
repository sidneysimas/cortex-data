import logging
from typing import Any

import oracledb
import pyarrow as pa

from data_formulator.data_loader.external_data_loader import (
    CatalogNode,
    ExternalDataLoader,
    MAX_IMPORT_ROWS,
    build_source_filter_where_clause_inline,
    build_where_clause_inline,
    _esc_id,
    _esc_str,
)
from data_formulator.data_loader import probe_utils
from data_formulator.datalake.parquet_utils import df_to_safe_records

logger = logging.getLogger(__name__)

# oracledb ships in "thin" mode by default — pure Python, talks the Oracle
# wire protocol directly, no Oracle Instant Client / libclntsh install
# required. That's deliberately left as the default here (no
# init_oracle_client() call) so this loader works out of the box; thin mode
# covers Oracle 12.1+ servers, which is effectively everything still in
# production use.


def _output_type_handler(cursor, metadata):
    """oracledb's default behavior returns CLOB/BLOB columns as LOB objects
    requiring an explicit .read() — auto-converting them to plain str/bytes
    here means every other method on this class can treat a query result as
    a normal row tuple, matching every other connector."""
    if metadata.type_code in (oracledb.DB_TYPE_CLOB, oracledb.DB_TYPE_NCLOB, oracledb.DB_TYPE_BLOB):
        return cursor.var(metadata.type_code, arraysize=cursor.arraysize, outconverter=lambda v: v.read() if v is not None else None)
    return None


class OracleDataLoader(ExternalDataLoader):
    DISPLAY_NAME = "Oracle Database"
    DESCRIPTION = "Connect to an Oracle Database to query tables with SQL."

    @staticmethod
    def list_params() -> list[dict[str, Any]]:
        return [
            {"name": "user", "type": "string", "required": True, "default": "", "tier": "auth", "description": "Oracle username"},
            {"name": "password", "type": "string", "required": True, "default": "", "sensitive": True, "tier": "auth", "description": "Oracle password"},
            {"name": "host", "type": "string", "required": True, "default": "localhost", "tier": "connection", "description": "Oracle host"},
            {"name": "port", "type": "string", "required": False, "default": "1521", "tier": "connection", "advanced": True, "description": "Oracle listener port"},
            {"name": "service_name", "type": "string", "required": True, "default": "", "tier": "connection", "description": "Oracle service name (e.g. ORCLPDB1, or your TNS service alias)"},
            {"name": "schema", "type": "string", "required": False, "default": "", "tier": "filter", "description": "Schema/owner to browse (leave empty to browse all schemas visible to this user)"},
        ]

    AUTH_GUIDE = "oracle.md"

    _CONNECT_TIMEOUT = 10  # seconds — prevents hangs on unreachable databases

    def __init__(self, params: dict[str, Any]):
        self.params = params

        self.host = self.params.get("host", "")
        self.port = self.params.get("port", "") or "1521"
        self.user = self.params.get("user", "")
        self.password = self.params.get("password", "")
        self.service_name = self.params.get("service_name", "")
        self.schema = (self.params.get("schema") or "").strip().upper()

        if not self.host:
            raise ValueError("Oracle host is required")
        if not self.user:
            raise ValueError("Oracle user is required")
        if not self.service_name:
            raise ValueError("Oracle service_name is required")

        dsn = oracledb.makedsn(self.host, int(self.port), service_name=self.service_name)

        try:
            self._conn = oracledb.connect(
                user=self.user, password=self.password, dsn=dsn,
                tcp_connect_timeout=self._CONNECT_TIMEOUT,
            )
            self._conn.outputtypehandler = _output_type_handler
        except Exception as e:
            logger.error(
                "Failed to connect to Oracle (%s@%s:%s/%s): %s",
                self.user, self.host, self.port, self.service_name, e,
            )
            raise ValueError(
                f"Failed to connect to Oracle service '{self.service_name}' on host '{self.host}': {e}"
            ) from e

        # Default browsing scope: the connecting user's own schema, unless
        # the operator pinned a different one — mirrors ALL_TABLES access
        # rules (a user sees their own objects plus anything explicitly
        # GRANTed) without forcing a full-instance scan by default.
        if not self.schema:
            self.schema = self.user.upper()

        logger.info(
            "Successfully connected to Oracle: %s@%s:%s/%s (schema=%s)",
            self.user, self.host, self.port, self.service_name, self.schema,
        )

    # -- Query execution -----------------------------------------------------

    def _read_sql(self, query: str, params: dict[str, Any] | None = None) -> pa.Table:
        """Execute a query and return results as a PyArrow Table (no pandas)."""
        cur = self._conn.cursor()
        try:
            cur.execute(query, params or {})
            if cur.description is None:
                return pa.table({})
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
            if not rows:
                return pa.table({col: pa.array([], type=pa.null()) for col in columns})
            col_data = {col: [row[i] for row in rows] for i, col in enumerate(columns)}
            return pa.table(col_data)
        finally:
            cur.close()

    def _qualified(self, owner: str, table_name: str) -> str:
        return f'{_esc_id(owner, chr(34))}.{_esc_id(table_name, chr(34))}'

    def fetch_data_as_arrow(
        self,
        source_table: str,
        import_options: dict[str, Any] | None = None,
    ) -> pa.Table:
        """Fetch data from Oracle as a PyArrow Table."""
        opts = import_options or {}
        size = min(opts.get("size", MAX_IMPORT_ROWS), MAX_IMPORT_ROWS)
        sort_columns = opts.get("sort_columns")
        sort_order = opts.get("sort_order", "asc")
        conditions = opts.get("conditions", [])
        source_filters = opts.get("source_filters", [])

        if not source_table:
            raise ValueError("source_table must be provided")

        owner, table = self._resolve_source_table(source_table)
        qualified = self._qualified(owner, table)
        base_query = f"SELECT * FROM {qualified}"

        where_clause = build_source_filter_where_clause_inline(
            source_filters, quote_char='"', dialect="oracle"
        ) or build_where_clause_inline(conditions, quote_char='"')
        if where_clause:
            base_query = f"{base_query} {where_clause}"

        order_by_clause = ""
        if sort_columns and len(sort_columns) > 0:
            order_direction = "DESC" if sort_order == 'desc' else "ASC"
            sanitized_cols = [f'{_esc_id(col, chr(34))} {order_direction}' for col in sort_columns]
            order_by_clause = f" ORDER BY {', '.join(sanitized_cols)}"

        query = f"{base_query}{order_by_clause} FETCH FIRST {int(size)} ROWS ONLY"

        logger.info(f"Executing Oracle query: {query[:200]}...")
        arrow_table = self._read_sql(query)
        logger.info(f"Fetched {arrow_table.num_rows} rows from Oracle")
        return arrow_table

    def _resolve_source_table(self, source_table: str) -> tuple[str, str]:
        """Parse ``"OWNER.TABLE"`` or bare ``"TABLE"`` (defaults to the
        connector's pinned/default schema)."""
        parts = source_table.split(".")
        if len(parts) >= 2:
            return parts[0], ".".join(parts[1:])
        return self.schema, parts[0]

    def probe(self, path: list[str], query: dict[str, Any]) -> dict[str, Any]:
        """Compile the SPJQ to Oracle SQL and run it server-side."""
        if not path:
            return {"error": "probe requires a non-empty table path"}
        owner, table = self._resolve_source_table(".".join(str(p) for p in path))
        try:
            relation = (
                f"{probe_utils.quote_ident(owner, probe_utils.ORACLE)}."
                f"{probe_utils.quote_ident(table, probe_utils.ORACLE)}"
            )
        except ValueError as exc:
            return {"error": f"invalid table identifier: {exc}"}
        return probe_utils.probe_via_native_sql(
            query, relation=relation, dialect=probe_utils.ORACLE, execute=self._read_sql,
        )

    # -- Catalog ---------------------------------------------------------

    @staticmethod
    def catalog_hierarchy() -> list[dict[str, str]]:
        return [
            {"key": "schema", "label": "Schema"},
            {"key": "table", "label": "Table"},
        ]

    def list_tables(self, table_filter: str | None = None) -> list[dict[str, Any]]:
        try:
            owner_filter = f"AND OWNER = '{_esc_str(self.schema)}'" if self.schema else ""
            tables_query = f"""
                SELECT OWNER, TABLE_NAME
                FROM ALL_TABLES
                WHERE 1=1 {owner_filter}
                ORDER BY OWNER, TABLE_NAME
            """
            tables_df = self._read_sql(tables_query).to_pandas()

            columns_query = f"""
                SELECT c.OWNER, c.TABLE_NAME, c.COLUMN_NAME, c.DATA_TYPE,
                       cc.COMMENTS AS COLUMN_COMMENT
                FROM ALL_TAB_COLUMNS c
                LEFT JOIN ALL_COL_COMMENTS cc
                  ON cc.OWNER = c.OWNER AND cc.TABLE_NAME = c.TABLE_NAME AND cc.COLUMN_NAME = c.COLUMN_NAME
                WHERE 1=1 {owner_filter}
                ORDER BY c.OWNER, c.TABLE_NAME, c.COLUMN_ID
            """
            cols_df = self._read_sql(columns_query).to_pandas()

            col_map: dict[str, list[dict]] = {}
            for _, cr in cols_df.iterrows():
                key = f"{cr['OWNER']}.{cr['TABLE_NAME']}"
                entry: dict[str, Any] = {"name": cr["COLUMN_NAME"], "type": cr["DATA_TYPE"]}
                comment = cr.get("COLUMN_COMMENT")
                if comment and str(comment).strip():
                    entry["description"] = str(comment).strip()
                col_map.setdefault(key, []).append(entry)

            table_comments_query = f"""
                SELECT OWNER, TABLE_NAME, COMMENTS
                FROM ALL_TAB_COMMENTS
                WHERE COMMENTS IS NOT NULL {owner_filter}
            """
            try:
                tc_df = self._read_sql(table_comments_query).to_pandas()
                table_comment_map = {
                    f"{r['OWNER']}.{r['TABLE_NAME']}": str(r['COMMENTS']).strip()
                    for _, r in tc_df.iterrows() if r['COMMENTS'] and str(r['COMMENTS']).strip()
                }
            except Exception:
                table_comment_map = {}

            results = []
            for _, row in tables_df.iterrows():
                owner, table_name = row['OWNER'], row['TABLE_NAME']
                full_table_name = f"{owner}.{table_name}"
                if table_filter and table_filter.lower() not in full_table_name.lower():
                    continue
                columns = col_map.get(full_table_name, [])
                metadata: dict[str, Any] = {
                    "columns": columns,
                    "source_metadata_status": "synced" if columns else "partial",
                }
                table_desc = table_comment_map.get(full_table_name)
                if table_desc:
                    metadata["description"] = table_desc
                results.append({
                    "name": full_table_name,
                    "path": [owner, table_name],
                    "metadata": metadata,
                })
            return results
        except Exception as e:
            logger.error(f"Error listing Oracle tables: {e}")
            return []

    def sync_catalog_metadata(self, table_filter: str | None = None) -> list[dict[str, Any]]:
        tables = self.list_tables(table_filter)
        self.ensure_table_keys(tables)
        return tables

    def search_catalog(self, query: str, limit: int = 100) -> dict:
        text = (query or "").strip()
        if not text:
            return {"tree": [], "truncated": False}
        max_results = max(1, int(limit or 100))
        pattern = f"%{_esc_str(text.upper())}%"
        owner_filter = f"AND OWNER = '{_esc_str(self.schema)}'" if self.schema else ""
        try:
            rows = self._read_sql(f"""
                SELECT OWNER, TABLE_NAME FROM ALL_TABLES
                WHERE TABLE_NAME LIKE '{pattern}' {owner_filter}
                ORDER BY OWNER, TABLE_NAME
                FETCH FIRST {max_results + 1} ROWS ONLY
            """).to_pandas()
            entries = [{
                "name": f"{r['OWNER']}.{r['TABLE_NAME']}",
                "path": [r['OWNER'], r['TABLE_NAME']],
                "metadata": {"_source_name": f"{r['OWNER']}.{r['TABLE_NAME']}"},
            } for _, r in rows.iterrows()]
        except Exception as exc:
            logger.warning("Oracle catalog search failed: %s", type(exc).__name__)
            entries = []
        truncated = len(entries) > max_results
        return {"tree": self._tables_to_catalog_tree(entries[:max_results]), "truncated": truncated}

    def ls(
        self,
        path: list[str] | None = None,
        filter: str | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[CatalogNode]:
        path = path or []
        eff = self.effective_hierarchy()
        if len(path) >= len(eff):
            return []
        level_key = eff[len(path)]["key"]
        pagination_clause = ""
        if limit is not None:
            pagination_clause = f" OFFSET {max(0, int(offset))} ROWS FETCH NEXT {max(0, int(limit))} ROWS ONLY"

        if level_key == "schema":
            query = f"""
                SELECT USERNAME AS OWNER FROM ALL_USERS
                WHERE USERNAME IN (SELECT DISTINCT OWNER FROM ALL_TABLES)
                ORDER BY USERNAME
                {pagination_clause}
            """
            rows = self._read_sql(query).to_pandas()
            nodes = []
            for _, r in rows.iterrows():
                name = r["OWNER"]
                if filter and filter.lower() not in name.lower():
                    continue
                nodes.append(CatalogNode(name=name, node_type="namespace", path=path + [name]))
            return nodes

        if level_key == "table":
            pinned = self.pinned_scope()
            remaining_path = list(path)
            owner = pinned.get("schema")
            if not owner:
                if not remaining_path:
                    return []
                owner = remaining_path.pop(0)
            query = f"""
                SELECT TABLE_NAME FROM ALL_TABLES
                WHERE OWNER = '{_esc_str(owner)}'
                ORDER BY TABLE_NAME
                {pagination_clause}
            """
            rows = self._read_sql(query).to_pandas()
            nodes = []
            for _, r in rows.iterrows():
                name = r["TABLE_NAME"]
                if filter and filter.lower() not in name.lower():
                    continue
                full_source = f"{owner}.{name}"
                nodes.append(CatalogNode(
                    name=name, node_type="table", path=path + [name],
                    metadata={"_source_name": full_source},
                ))
            return nodes
        return []

    def get_metadata(self, path: list[str]) -> dict[str, Any]:
        if not path:
            return {}
        pinned = self.pinned_scope()
        remaining = list(path)
        owner = pinned.get("schema")
        if not owner:
            if not remaining:
                return {}
            owner = remaining.pop(0)
        if not remaining:
            return {}
        table_name = remaining[0]
        full_source = f"{owner}.{table_name}"
        try:
            cols_df = self._read_sql(f"""
                SELECT c.COLUMN_NAME, c.DATA_TYPE, cc.COMMENTS AS COLUMN_COMMENT
                FROM ALL_TAB_COLUMNS c
                LEFT JOIN ALL_COL_COMMENTS cc
                  ON cc.OWNER = c.OWNER AND cc.TABLE_NAME = c.TABLE_NAME AND cc.COLUMN_NAME = c.COLUMN_NAME
                WHERE c.OWNER = '{_esc_str(owner)}' AND c.TABLE_NAME = '{_esc_str(table_name)}'
                ORDER BY c.COLUMN_ID
            """).to_pandas()
            columns = []
            for _, r in cols_df.iterrows():
                entry: dict[str, Any] = {"name": r["COLUMN_NAME"], "type": r["DATA_TYPE"]}
                comment = r.get("COLUMN_COMMENT")
                if comment and str(comment).strip():
                    entry["description"] = str(comment).strip()
                columns.append(entry)

            table_description = None
            try:
                td_df = self._read_sql(f"""
                    SELECT COMMENTS FROM ALL_TAB_COMMENTS
                    WHERE OWNER = '{_esc_str(owner)}' AND TABLE_NAME = '{_esc_str(table_name)}'
                """).to_pandas()
                if not td_df.empty and td_df["COMMENTS"].iloc[0]:
                    table_description = str(td_df["COMMENTS"].iloc[0]).strip() or None
            except Exception:
                pass

            qualified = self._qualified(owner, table_name)
            count_df = self._read_sql(f'SELECT COUNT(*) AS CNT FROM {qualified}').to_pandas()
            row_count = int(count_df["CNT"].iloc[0])
            sample_df = self._read_sql(f'SELECT * FROM {qualified} FETCH FIRST 5 ROWS ONLY').to_pandas()
            sample_rows = df_to_safe_records(sample_df)

            result: dict[str, Any] = {
                "_source_name": full_source,
                "row_count": row_count,
                "columns": columns,
                "sample_rows": sample_rows,
            }
            if table_description:
                result["description"] = table_description
            return result
        except Exception as e:
            logger.warning(f"get_metadata failed for {path}: {e}")
            return {}

    def test_connection(self) -> bool:
        try:
            self._read_sql("SELECT 1 FROM DUAL")
            return True
        except Exception:
            return False
