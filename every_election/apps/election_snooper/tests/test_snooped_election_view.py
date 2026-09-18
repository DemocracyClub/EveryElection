from election_snooper.models import SnoopedElection


def test_anonymous_user_cant_post(client, snooped_election):
    resp = client.post(
        "/election_radar/",
        {
            "pk": snooped_election.pk,
            f"{snooped_election.pk}-status": "rejected",
        },
    )

    assert resp.status_code == 403
    snooped_election.refresh_from_db()
    assert snooped_election.status == "election"


def test_logged_in_non_moderator_cant_post(logged_in_client, snooped_election):
    resp = logged_in_client.post(
        "/election_radar/",
        {
            "pk": snooped_election.pk,
            f"{snooped_election.pk}-status": "rejected",
        },
    )

    assert resp.status_code == 403
    snooped_election.refresh_from_db()
    assert snooped_election.status == "election"


def test_moderator_can_post(moderator_client, snooped_election):
    resp = moderator_client.post(
        "/election_radar/",
        {
            "pk": snooped_election.pk,
            f"{snooped_election.pk}-status": "rejected",
        },
    )

    assert resp.status_code == 302
    snooped_election.refresh_from_db()
    assert snooped_election.status == "rejected"


def test_anonymous_user_isnt_shown_the_review_form(client, snooped_election):
    resp = client.get("/election_radar/")

    assert resp.status_code == 200
    assert resp.context["user_is_moderator"] is False
    assert f'name="{snooped_election.pk}-status"' not in resp.content.decode()


def test_non_moderator_isnt_shown_the_review_form(
    logged_in_client, snooped_election
):
    resp = logged_in_client.get("/election_radar/")

    assert resp.status_code == 200
    assert resp.context["user_is_moderator"] is False
    assert f'name="{snooped_election.pk}-status"' not in resp.content.decode()


def test_moderator_is_shown_the_review_form(moderator_client, snooped_election):
    resp = moderator_client.get("/election_radar/")

    assert resp.status_code == 200
    assert resp.context["user_is_moderator"] is True
    assert f'name="{snooped_election.pk}-status"' in resp.content.decode()


def test_permalink_and_create_link_shown(client, snooped_election):
    resp = client.get("/election_radar/")

    content = resp.content.decode()
    assert f'href="/election_radar/?pk={snooped_election.pk}"' in content
    assert f'href="/id_creator/?radar_id={snooped_election.pk}"' in content


def test_create_link_shown_even_when_not_marked_as_an_election(
    client, snooped_election
):
    snooped_election.status = "rejected"
    snooped_election.save()

    resp = client.get("/election_radar/")

    content = resp.content.decode()
    assert f'href="/id_creator/?radar_id={snooped_election.pk}"' in content


def test_permalink_shows_only_that_election(client, snooped_election):
    other = SnoopedElection.objects.create(
        title="Another election", snooper_name="TestSnooper"
    )

    resp = client.get(f"/election_radar/?pk={snooped_election.pk}")

    content = resp.content.decode()
    assert snooped_election.title in content
    assert other.title not in content
