"""
Git操作工具模块
"""

import os
from pathlib import Path
from typing import Optional
from datetime import datetime

try:
    from git import Repo, GitCommandError
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False


class GitHelper:
    """Git操作助手"""

    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.repo: Optional[Repo] = None

        if GIT_AVAILABLE:
            self._init_repo()

    def _init_repo(self):
        """初始化或连接到仓库"""
        if not GIT_AVAILABLE:
            return

        try:
            self.repo = Repo(self.project_path)
        except Exception:
            # 仓库不存在，初始化新仓库
            self.repo = Repo.init(self.project_path)

    def is_available(self) -> bool:
        """检查Git是否可用"""
        return GIT_AVAILABLE and self.repo is not None

    def add(self, files: list = None):
        """添加文件到暂存区"""
        if not self.is_available():
            return

        if files is None:
            self.repo.git.add(A=True)
        else:
            for f in files:
                self.repo.git.add(f)

    def commit(self, message: str) -> bool:
        """提交更改"""
        if not self.is_available():
            return False

        try:
            # 检查是否有更改
            if self.repo.is_dirty(untracked_files=True):
                self.repo.index.commit(message)
                return True
            return False
        except GitCommandError as e:
            print(f"Git commit error: {e}")
            return False

    def add_and_commit(self, message: str, files: list = None) -> bool:
        """添加并提交"""
        self.add(files)
        return self.commit(message)

    def get_last_commit(self) -> Optional[dict]:
        """获取最后一次提交"""
        if not self.is_available():
            return None

        try:
            commit = self.repo.head.commit
            return {
                'hash': commit.hexsha[:8],
                'message': commit.message,
                'author': str(commit.author),
                'date': datetime.fromtimestamp(commit.committed_date)
            }
        except Exception:
            return None

    def get_commit_history(self, max_count: int = 10) -> list:
        """获取提交历史"""
        if not self.is_available():
            return []

        try:
            commits = []
            for commit in self.repo.iter_commits(max_count=max_count):
                commits.append({
                    'hash': commit.hexsha[:8],
                    'message': commit.message,
                    'author': str(commit.author),
                    'date': datetime.fromtimestamp(commit.committed_date)
                })
            return commits
        except Exception:
            return []

    def get_status(self) -> dict:
        """获取仓库状态"""
        if not self.is_available():
            return {'available': False}

        return {
            'available': True,
            'is_dirty': self.repo.is_dirty(untracked_files=True),
            'untracked_files': list(self.repo.untracked_files),
            'modified_files': [item.a_path for item in self.repo.index.diff(None)]
        }

    def create_branch(self, branch_name: str) -> bool:
        """创建分支"""
        if not self.is_available():
            return False

        try:
            self.repo.create_head(branch_name)
            return True
        except GitCommandError:
            return False

    def switch_branch(self, branch_name: str) -> bool:
        """切换分支"""
        if not self.is_available():
            return False

        try:
            self.repo.heads[branch_name].checkout()
            return True
        except (KeyError, GitCommandError):
            return False

    def get_current_branch(self) -> Optional[str]:
        """获取当前分支名"""
        if not self.is_available():
            return None

        try:
            return self.repo.active_branch.name
        except Exception:
            return None
