class ModelBookValidatorError(Exception):
    pass


class CharacterInconsistentError(ModelBookValidatorError):
    def __init__(self, character_ids: set[int]):
        super().__init__(f"Error: Inconsistent characters found: {character_ids}")
