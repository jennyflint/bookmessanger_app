class JobNotFoundError(Exception):
    def __init__(self, job_id: int):
        super().__init__(f"Error: Job with ID '{job_id}' does not exist.")


class JobObjectTableNotFoundError(Exception):
    def __init__(self, table_name: str, object_id: int):
        super().__init__(
            f"Error: Job object table '{table_name}' "
            f"with ID '{object_id}' does not exist."
        )
