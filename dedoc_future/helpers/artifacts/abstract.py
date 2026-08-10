from abc import ABCMeta, abstractmethod


class AbstractArtifact(metaclass=ABCMeta):
    @property
    def name(self) -> str:
        """
        :return: unique name of the artifact
        """
        raise NotImplementedError

    @abstractmethod
    def download(self, out_dir: str | None = None) -> str:
        """
        Download artifact.

        :param out_dir: directory for saving artifact
        :return: path to the downloaded artifact
        """
        pass
