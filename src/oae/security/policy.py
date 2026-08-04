from dataclasses import dataclass


@dataclass
class SecurityPolicy:
    """
    Global security policy for OAE.
    """

    allow_file_delete: bool = False
    allow_force_push: bool = False
    allow_shell_execution: bool = False
    require_human_approval: bool = True

    def can_delete(self) -> bool:
        return self.allow_file_delete

    def can_force_push(self) -> bool:
        return self.allow_force_push

    def can_execute_shell(self) -> bool:
        return self.allow_shell_execution