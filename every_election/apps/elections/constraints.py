from elections.models import Election, ModerationStatuses


class ViolatedConstraint(Exception):
    pass


def has_approved_child(election):
    # True if all this election has one or more approved children
    return election.get_children("public_objects").all().exists()


def has_approved_parents(election):
    # True if all of this election's parent groups are approved
    if (
        election.group
        and election.group.current_status != ModerationStatuses.approved.value
    ):
        return False
    if (
        election.group.group
        and election.group.group.current_status
        != ModerationStatuses.approved.value
    ):
        return False
    return True


def has_related_status(election: Election):
    return election.moderationhistory_set.exists()


def check_constraints(election):
    if not has_related_status(election):
        raise ViolatedConstraint(
            "Election {} has no related status objects".format(
                election.election_id
            )
        )

    if (
        election.group
        and election.current_status == ModerationStatuses.approved.value
        and not has_approved_parents(election)
    ):
        raise ViolatedConstraint(
            "Election {} is approved but one or more parents are not approved".format(
                election.election_id
            )
        )

    if (
        election.group_type
        and election.election_type.election_type not in ["mayor", "pcc"]
        and not has_approved_child(election)
    ):
        raise ViolatedConstraint(
            "Election {} is approved but has no approved children".format(
                election.election_id
            )
        )
