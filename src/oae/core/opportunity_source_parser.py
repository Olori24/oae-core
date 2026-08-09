class OpportunitySourceParser:
    """
    Convert source-specific payloads into normalized opportunity
    dictionaries.

    The parser only maps fields and extracts records. It does not
    score, rank, verify, or mutate the source payload.
    """

    def __init__(self, field_mapping=None):
        self.field_mapping = field_mapping or {}

    def parse(self, payload):
        """
        Parse a direct list or a payload containing a `results` list.
        """

        records = self._extract_records(payload)

        if not records:
            return []

        parsed = []

        for record in records:
            if not isinstance(record, dict):
                continue

            parsed.append(
                self._parse_record(record)
            )

        return parsed

    def _extract_records(self, payload):
        if isinstance(payload, list):
            return payload

        if isinstance(payload, dict):
            results = payload.get("results")

            if isinstance(results, list):
                return results

        return []

    def _parse_record(self, record):
        result = dict(record)

        for source_field, target_field in self.field_mapping.items():
            if source_field not in record:
                continue

            value = record[source_field]

            if isinstance(value, str):
                value = value.strip()

            result[target_field] = value

            if source_field != target_field:
                result.pop(source_field, None)

        return result
