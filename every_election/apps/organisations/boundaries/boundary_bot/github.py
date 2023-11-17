import datetime
import os

from commitment import GitHubClient as GitHubSyncClient
from commitment import GitHubCredentials
from organisations.boundaries.boundary_bot.common import GITHUB_API_KEY
from polling_bot.brain import GitHubClient as GitHubIssueClient


class GitHubIssueHelper:
    def __init__(self):
        self.issues = []

    def append_completed_review_issue(self, record):
        self.issues.append(
            {
                "title": "Completed boundary review for %s" % (record["name"]),
                "body": "Completed boundary review for %s: %s"
                % (record["name"], record["consultation_url"]),
            }
        )

    def raise_issues(self):
        owner = "DemocracyClub"
        repo = "EveryElection"
        client = GitHubIssueClient(GITHUB_API_KEY)
        for issue in self.issues:
            client.raise_issue(owner, repo, issue["title"], issue["body"])


class GitHubSyncHelper:
    def get_github_credentials(self):
        return GitHubCredentials(
            repo=os.environ["MORPH_GITHUB_BOUNDARY_REPO"],
            name=os.environ["MORPH_GITHUB_USERNAME"],
            email=os.environ["MORPH_GITHUB_EMAIL"],
            api_key=GITHUB_API_KEY,
        )

    def sync_file_to_github(self, file_name, content):
        try:
            creds = self.get_github_credentials()
            g = GitHubSyncClient(creds)
            g.push_file(
                content,
                file_name,
                "Update %s at %s" % (file_name, str(datetime.datetime.now())),
            )
        except KeyError:
            # if no credentials are defined in env vars
            # just ignore this step
            pass
