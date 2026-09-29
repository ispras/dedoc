from dedoc_future.helpers.artifacts.huggingface import HuggingfaceArtifact

_artifacts = [
    HuggingfaceArtifact(
        name="txtlayer_classifier",
        repo_name="txtlayer_classifier",
        hub_names=["model.json"],
        hub_hash="9ca1de749d8d37147b00a3a228e03ee1776c695f"
    ),
    HuggingfaceArtifact(
        name="orientation_classifier",
        repo_name="scan_orientation_efficient_net_b0",
        hub_names=["model.pth"],
        hub_hash="c60812552a1be624476c1e5b58599867b36f8d4e"
    ),
    HuggingfaceArtifact(
        name="layout_docling",
        repo_name="docling-layout-heron",
        hub_names=["config.json", "model.safetensors", "preprocessor_config.json"],
        hub_hash="8f39ad3c0b4c58e9c2d2c84a38465abf757272d8",
        user_name="docling-project"
    ),
]

ARTIFACTS = {artifact.name: artifact for artifact in _artifacts}
