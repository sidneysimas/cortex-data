**Example**

`system` at `localhost:1521`, service name `ORCLPDB1`

**Credentials**

Use an Oracle account with `SELECT` access to the tables you need. Ask your DBA for the host, port, service name, username, and password — Oracle almost always requires a password (there is no blank-password mode like some other databases).

**Service name vs SID**

Modern Oracle (12c and newer, including Autonomous Database and Oracle 26ai) is addressed by *service name*, not the older *SID*. If you only have a SID, most Oracle installations also expose it as a service name of the same value — ask your DBA to confirm, or check your `tnsnames.ora` file for the `SERVICE_NAME=` entry.

**Scope**

Leave `schema` empty to browse your own schema (the objects owned by the user you connect as) plus anything explicitly granted to you. Enter a schema name to browse a specific owner's tables instead.

**No client install required**

This connector uses the `oracledb` driver in *thin mode* — pure Python, no Oracle Instant Client / `libclntsh` installation needed on this machine.

**Check**

Confirm the listener is reachable and the service name is correct with:

```bash
sqlplus <user>/<password>@<host>:<port>/<service_name>
```
