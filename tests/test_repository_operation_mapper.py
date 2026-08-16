from oae.agents.repository_operation_mapper import (
    RepositoryOperationMapper,
)


def test_repository_operation_mapping():

    mapper = RepositoryOperationMapper()

    assert (
        mapper.map("create_file")
        == "repository_create_file"
    )

    assert (
        mapper.map("modify_file")
        == "repository_modify_file"
    )

    assert (
        mapper.map("run_tests")
        == "repository_run_tests"
    )

    assert (
        mapper.map("commit_changes")
        == "repository_commit"
    )

    assert (
        mapper.map("something_unknown")
        == "unknown_operation"
    )
