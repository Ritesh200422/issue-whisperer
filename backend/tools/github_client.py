"""GitHub client tool with caching and replay mode."""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any
from github import Github, GithubException

from models.issue import IssueModel, RepositoryModel
from services.config_service import get_config

logger = logging.getLogger(__name__)


class GitHubClient:
    """Client for GitHub API operations with local caching and replay mode."""

    def __init__(self, token: str | None = None, use_cache: bool = True):
        self.config = get_config()
        self.token = token or getattr(self.config.github, "token", None) or os.environ.get("GITHUB_TOKEN")
        self.use_cache = use_cache
        
        # Local caching directories
        self.cache_dir = Path(self.config.github.cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.issues_cache_file = self.cache_dir / "issues.json"
        self.repo_cache_file = self.cache_dir / "repository.json"
        self.readme_cache_file = self.cache_dir / "README.md"
        
        # Initialize github API client if token is present or we are online
        self._gh = None
        if self.token:
            self._gh = Github(self.token)
        else:
            self._gh = Github()  # Unauthenticated (limit 60/hr)

    def fetch_repository_info(self, repo_name: str) -> RepositoryModel:
        """Fetch repository details from Live API or Cache."""
        if not self.use_cache or not self.repo_cache_file.exists():
            logger.info("Fetching repository info for %s from GitHub API...", repo_name)
            try:
                repo = self._gh.get_repo(repo_name)
                readme_content = ""
                try:
                    readme = repo.get_readme()
                    readme_content = readme.decoded_content.decode("utf-8")
                except GithubException:
                    logger.warning("No README found for repository: %s", repo_name)

                repo_model = RepositoryModel(
                    owner=repo.owner.login,
                    name=repo.name,
                    description=repo.description or "",
                    stars=repo.stargazers_count,
                    forks=repo.forks_count,
                    open_issues_count=repo.open_issues_count,
                    language=repo.language,
                    readme_content=readme_content
                )
                
                # Write cache
                with open(self.repo_cache_file, "w", encoding="utf-8") as f:
                    json.dump(repo_model.model_dump(), f, indent=2, ensure_ascii=False)
                
                with open(self.readme_cache_file, "w", encoding="utf-8") as f:
                    f.write(readme_content)
                
                return repo_model
            except Exception as e:
                if self.repo_cache_file.exists():
                    logger.warning("Failed to fetch live repository info. Falling back to cache: %s", e)
                else:
                    raise e

        # Read from cache
        logger.info("Loading repository info from cache: %s", self.repo_cache_file)
        with open(self.repo_cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return RepositoryModel(**data)

    def fetch_issues(self, repo_name: str, state: str = "all", limit: int = 100) -> list[IssueModel]:
        """Fetch issues from Live API or Cache."""
        if not self.use_cache or not self.issues_cache_file.exists():
            logger.info("Fetching issues for %s from GitHub API (state=%s)...", repo_name, state)
            try:
                repo = self._gh.get_repo(repo_name)
                # Pull both open and closed issues up to limit
                issues_page = repo.get_issues(state=state)
                
                issue_models: list[IssueModel] = []
                count = 0
                for issue in issues_page:
                    # Skip pull requests
                    if issue.pull_request:
                        continue
                    
                    issue_models.append(
                        IssueModel(
                            number=issue.number,
                            title=issue.title,
                            body=issue.body or "",
                            labels=[label.name for label in issue.labels],
                            state=issue.state,
                            created_at=issue.created_at.isoformat() if issue.created_at else None,
                            updated_at=issue.updated_at.isoformat() if issue.updated_at else None,
                            html_url=issue.html_url,
                            user_login=issue.user.login if issue.user else None
                        )
                    )
                    count += 1
                    if count >= limit:
                        break
                
                # Save cache
                with open(self.issues_cache_file, "w", encoding="utf-8") as f:
                    json.dump([issue.model_dump() for issue in issue_models], f, indent=2, ensure_ascii=False)
                
                return issue_models
            except Exception as e:
                if self.issues_cache_file.exists():
                    logger.warning("Failed to fetch live issues. Falling back to cache: %s", e)
                else:
                    raise e

        # Read from cache
        logger.info("Loading issues from cache: %s", self.issues_cache_file)
        with open(self.issues_cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return [IssueModel(**item) for item in data]

    def fetch_issue(self, repo_name: str, issue_number: int) -> IssueModel:
        """Fetch a single issue. Try cache first, then API."""
        if self.issues_cache_file.exists():
            with open(self.issues_cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    if item["number"] == issue_number:
                        return IssueModel(**item)
        
        # Live fetch
        logger.info("Fetching issue #%d from GitHub API...", issue_number)
        repo = self._gh.get_repo(repo_name)
        issue = repo.get_issue(issue_number)
        return IssueModel(
            number=issue.number,
            title=issue.title,
            body=issue.body or "",
            labels=[label.name for label in issue.labels],
            state=issue.state,
            created_at=issue.created_at.isoformat() if issue.created_at else None,
            updated_at=issue.updated_at.isoformat() if issue.updated_at else None,
            html_url=issue.html_url,
            user_login=issue.user.login if issue.user else None
        )
