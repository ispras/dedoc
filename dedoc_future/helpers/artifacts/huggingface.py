import logging
import os
import shutil
from pathlib import Path

from huggingface_hub import hf_hub_download

from dedoc_future.env import get_artifacts_path
from dedoc_future.helpers.artifacts.abstract import AbstractArtifact

logger = logging.getLogger(__name__)


class HuggingfaceArtifact(AbstractArtifact):
    def __init__(self, name: str, repo_name: str, hub_names: list[str], hub_hash: str, user_name: str = "dedoc") -> None:
        self._name = name
        self._repo_name = repo_name
        self._hub_names = hub_names
        self._hub_hash = hub_hash
        self._user_name = user_name

    @property
    def name(self) -> str:
        return self._name

    def download(self, out_dir: str | None = None) -> str:
        out_dir = out_dir if out_dir is not None else get_artifacts_path()
        out_dir = Path(out_dir) / self.name / self._hub_hash
        out_dir.mkdir(parents=True, exist_ok=True)

        for hub_name in self._hub_names:
            out_hub_path = out_dir / hub_name
            if out_hub_path.exists():
                logger.info(f"Object {self._repo_name}/{hub_name} already exists, skipping downloading")
                continue

            logger.info(f"Downloading {self._repo_name}/{hub_name} into {out_hub_path}")
            path = os.path.realpath(hf_hub_download(repo_id=f"{self._user_name}/{self._repo_name}", filename=hub_name, revision=self._hub_hash))
            shutil.move(path, str(out_hub_path))

        if len(self._hub_names) == 1:
            return str(out_dir / self._hub_names[0])

        return str(out_dir)
