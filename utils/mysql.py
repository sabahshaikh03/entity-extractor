from logging import Logger
from sqlalchemy.orm import Session


class MySQL:
    def __init__(self, logger: Logger, table, session: Session):
        self.session = session
        self.logger = logger
        self.table = table

    # Add an entry to the table
    def add_entry(self, data):
        try:
            new_entry = self.table(**data)
            self.session.add(new_entry)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            self.logger.exception(f"MYSQL-UTIL : Error: {e}")

    # Update an entry in the table
    def update_entry(self, record_id, update_data):
        try:
            # Find the record by ID
            record = self.session.query(self.table).get(record_id)
            if record is None:
                self.logger.warning(f"MYSQL-UTIL : Record with ID {record_id} not found")
                return

            # Update the record with the provided data
            for key, value in update_data.items():
                setattr(record, key, value)

            self.session.commit()
            self.logger.info("MYSQL-UTIL : Entry updated")
        except Exception as e:
            self.session.rollback()
            self.logger.exception(f"MYSQL-UTIL : Error: {e}")

    # Get an entry from the table by primary key
    def get_entry_by_primary_key(self, record_id):
        try:
            # Find the record by ID
            record = self.session.query(self.table).get(record_id)
            if record is None:
                self.logger.warning(f"MYSQL-UTIL : Record with ID {record_id} not found")
                return None
            self.logger.info(f"MYSQL-UTIL : Record with ID {record_id} retrieved successfully")
            return record
        except Exception as e:
            self.logger.exception(f"MYSQL-UTIL : Error: {e}")
            return None

    # Get entries from the table by a column and value
    def get_entries_by_a_column_value(self, column_name, value):
        try:
            # Find the records by column and value
            records = (
                self.session.query(self.table)
                .filter(getattr(self.table, column_name) == value)
                .all()
            )
            if not records:
                self.logger.warning(f"MYSQL-UTIL : No records found with {column_name} = {value}")
                return []
            self.logger.info(
                f"MYSQL-UTIL : Records with {column_name} = {value} retrieved successfully"
            )
            return records
        except Exception as e:
            self.logger.exception(f"MYSQL-UTIL : Error: {e}")
            return []
