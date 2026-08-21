## 2024-05-15 - [Pydantic String Validation]
**Vulnerability:** Weak string validation in tool inputs. `start_date` and `end_date` lacked regex validation allowing arbitrary strings to be parsed and potentially forwarded to Google Earth Engine execution pipelines.
**Learning:** Adding validation via regex guarantees downstream integrations (like datetime parsing or API parameter injections) do not consume malformed string payloads.
**Prevention:** Use Pydantic's `pattern` constraint in `Field` declarations for all structurally defined string inputs (like dates, emails, or IDs) to prevent invalid data or injection vulnerabilities.
